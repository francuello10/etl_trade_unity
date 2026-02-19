#!/usr/bin/env python3
"""
Script para generar análisis completo de inventario de Trade Unity (TU).

Alineado con documento base Trade Unity:
- Ecommerce B2B mayorista del grupo CEG
- Rubros: Máquinas y Herramientas, Hogar y Bazar, Electricidad e Iluminación, 
  Sanitarios y Griferías, Outdoor y Camping
- Marcas propias: Kuest, Barovo, Kushiro, Miyawa, Etheos, Gloa, Vonne

Análisis generado:
- Toma base del catálogo TU (nombres, marca, categoría)
- Toma stock del ERP (Pronosticado con pendiente en cajas)
- Calcula unidades (cajas × Box Qty) - según concepto "Caja madre / Box Qty"
- Clasifica stock usando fechas de recepción e importación
- Genera valuación según precios CEG (FOB, Plataforma, TU = Plataforma × 1.25)
- Calcula margen y ganancia potencial según principios de operación TU
"""

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from collections import defaultdict

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Archivos
CATALOGO_TU = "fuentes/catalogo_trade_unity.csv"
STOCK_ERP = "fuentes/stock_erp.csv"
CEG_PRODUCTOS_CSV = "fuentes/precios_plataforma_ceg.csv"
OUTPUT_DIR = "outputs"
OUTPUT_EXCEL = f"{OUTPUT_DIR}/TradeUnity Inventory Deep Dive.xlsx"


def parse_decimal(value: str) -> Decimal:
    """Convierte string a Decimal."""
    if not value or value == "":
        return Decimal("0")
    
    value_str = str(value).strip().replace("$", "").replace(" ", "").replace("%", "")
    value_str = value_str.replace(",", ".")
    
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_date(date_str: str) -> date:
    """Parsea fecha en varios formatos."""
    if not date_str or date_str == "":
        return None
    
    date_str = str(date_str).strip()
    
    # Formato YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        pass
    
    # Formato DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except:
        pass
    
    # Formato M/D/YY
    try:
        return datetime.strptime(date_str, "%m/%d/%y").date()
    except:
        pass
    
    return None


def days_since_today(target_date: date) -> int:
    """Calcula días desde hoy."""
    if not target_date:
        return None
    today = date.today()
    return (today - target_date).days


def auto_adjust_column_widths(writer, sheet_name, df):
    """Ajusta automáticamente el ancho de las columnas en Excel."""
    try:
        from openpyxl import load_workbook
        worksheet = writer.sheets[sheet_name]
        
        for idx, col in enumerate(df.columns, 1):
            column_letter = worksheet.cell(row=1, column=idx).column_letter
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            # Limitar ancho máximo a 50 caracteres
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    except Exception as e:
        print(f"   ⚠️  No se pudo ajustar columnas en {sheet_name}: {e}")


def classify_stock_by_dates(dias_recepcion, dias_importacion, clasif_recep, clasif_impo):
    """Clasifica stock según fechas y clasificaciones."""
    clasificacion = []
    riesgo = "Bajo"
    
    # Usar clasificación de recepción si existe
    if clasif_recep:
        if "2025" in clasif_recep or "2026" in clasif_recep:
            clasificacion.append("Reciente")
            riesgo = "Bajo"
        elif "2024" in clasif_recep:
            if "Septiembre a Diciembre" in clasif_recep or "Agosto o Después" in clasif_recep:
                clasificacion.append("Reciente 2024")
                riesgo = "Bajo"
            else:
                clasificacion.append("2024")
                riesgo = "Medio"
        elif "2023" in clasif_recep or "Previo" in clasif_recep:
            clasificacion.append("Antiguo")
            riesgo = "Alto"
    
    # Usar clasificación de importación si no hay recepción
    elif clasif_impo:
        if "2025" in clasif_impo or "2026" in clasif_impo:
            clasificacion.append("Reciente")
            riesgo = "Bajo"
        elif "2024" in clasif_impo:
            if "Septiembre a Diciembre" in clasif_impo or "Agosto o Después" in clasif_impo:
                clasificacion.append("Reciente 2024")
                riesgo = "Bajo"
            else:
                clasificacion.append("2024")
                riesgo = "Medio"
        elif "2023" in clasif_impo or "Previo" in clasif_impo:
            clasificacion.append("Antiguo")
            riesgo = "Alto"
    
    # Usar días si no hay clasificación
    elif dias_recepcion is not None:
        if dias_recepcion <= 90:
            clasificacion.append("Reciente")
            riesgo = "Bajo"
        elif dias_recepcion <= 365:
            clasificacion.append("Medio Plazo")
            riesgo = "Medio"
        else:
            clasificacion.append("Antiguo")
            riesgo = "Alto"
    elif dias_importacion is not None:
        if dias_importacion <= 90:
            clasificacion.append("Reciente")
            riesgo = "Bajo"
        elif dias_importacion <= 365:
            clasificacion.append("Medio Plazo")
            riesgo = "Medio"
        else:
            clasificacion.append("Antiguo")
            riesgo = "Alto"
    else:
        clasificacion.append("Sin Fecha")
        riesgo = "Alto"
    
    return " | ".join(clasificacion) if clasificacion else "Sin Clasificar", riesgo


def load_catalog():
    """Carga catálogo TU."""
    print(f"📖 Cargando catálogo TU desde: {CATALOGO_TU}")
    
    catalog = {}
    
    with open(CATALOGO_TU, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = str(row.get('sku', '')).strip().upper()
            d365_ref = str(row.get('Código de Producto (D365)', '')).strip()
            
            if not sku:
                continue
            
            catalog[sku] = {
                'sku': sku,
                'd365_reference': d365_ref,
                'nombre': str(row.get('Nombre del Producto', '')).strip(),
                'marca': str(row.get('Marca', '')).strip(),
                'categoria_2': str(row.get('Categoría (2° Nivel)', '')).strip(),
                'categoria_ultima': str(row.get('Categoría (Ultimo Nivel)', '')).strip(),
                'cantidad_paquete': parse_decimal(row.get('Cantidad por Paquete Comercial', '')),
                'fob_unitario': parse_decimal(row.get('Costo FOB (Unitario)', '')),
                'precio_plataforma_unitario': parse_decimal(row.get('Precio Plataforma (Unitario) – CEG', '')),
                'precio_plataforma_caja': parse_decimal(row.get('Precio Plataforma (Caja) – CEG', '')),
                'volumen_box': parse_decimal(row.get('Volumen (box)', '')),
                'fecha_importacion': row.get('Fecha de última importación CEG', '').strip(),
                'clasificacion_impo': str(row.get('Clasificacion IMPO', '')).strip(),
                'fecha_recepcion': row.get('Fecha de última recepción CEG', '').strip(),
                'clasificacion_recep': str(row.get('Clasificacion RECEP', '')).strip(),
                'dias_impo': row.get('Días desde última impo CEG', '').strip(),
                'dias_recep': row.get('Días desde última recep CEG', '').strip(),
                'tipo_marca': str(row.get('Tipo de Marca', '')).strip(),
                'ean': str(row.get('EAN', '')).strip(),
            }
            
            # También indexar por D365 Reference
            if d365_ref:
                catalog[d365_ref] = catalog[sku]
    
    print(f"   ✅ {len(catalog)} productos cargados del catálogo")
    return catalog


def load_stock():
    """Carga stock del ERP."""
    print(f"📖 Cargando stock desde: {STOCK_ERP}")
    
    stock_data = []
    
    with open(STOCK_ERP, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d365_ref = str(row.get('D365 Reference', '')).strip()
            stock_cajas = parse_decimal(row.get('Pronosticado con pendiente', ''))
            box_qty = parse_decimal(row.get('Box Qty', ''))
            volumen = parse_decimal(row.get('Volumen', ''))
            
            if not d365_ref or stock_cajas == 0:
                continue
            
            stock_data.append({
                'd365_reference': d365_ref,
                'stock_cajas': stock_cajas,
                'box_qty': box_qty,
                'volumen': volumen,
                'nombre_erp': str(row.get('Nombre', '')).strip(),
            })
    
    print(f"   ✅ {len(stock_data)} productos con stock cargado")
    return stock_data


def load_ceg_prices():
    """Carga precios CEG (base_price y fob)."""
    print(f"📖 Cargando precios CEG desde: {CEG_PRODUCTOS_CSV}")
    
    ceg_prices = {}
    
    try:
        with open(CEG_PRODUCTOS_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = str(row.get('sku', '')).strip().upper()
                base_price = parse_decimal(row.get('base_price', ''))
                fob = parse_decimal(row.get('fob', ''))
                
                if sku:
                    ceg_prices[sku] = {
                        'base_price': base_price,
                        'fob': fob,
                        'precio_normal_tu': base_price * Decimal('1.25'),
                    }
        
        print(f"   ✅ {len(ceg_prices)} productos con precios CEG cargados")
    except FileNotFoundError:
        print(f"   ⚠️  Archivo CEG no encontrado, continuando sin precios CEG")
    
    return ceg_prices


def generate_inventory_analysis():
    """Genera análisis completo de inventario."""
    print("🔄 Generando análisis de inventario...")
    
    # Cargar datos
    catalog = load_catalog()
    stock_data = load_stock()
    ceg_prices = load_ceg_prices()
    
    # Combinar datos
    inventory = []
    
    print("\n🔄 Combinando datos y calculando...")
    
    for stock in stock_data:
        d365_ref = stock['d365_reference']
        
        # Buscar en catálogo por D365 Reference o SKU
        product = catalog.get(d365_ref) or catalog.get(d365_ref.upper())
        
        # Buscar SKU para precios CEG
        sku = product['sku'] if product else d365_ref
        ceg_info = ceg_prices.get(sku, {})
        
        if not product:
            # Si no se encuentra, usar datos del ERP
            product = {
                'sku': d365_ref,
                'd365_reference': d365_ref,
                'nombre': stock['nombre_erp'],
                'marca': '',
                'categoria_2': '',
                'categoria_ultima': '',
                'cantidad_paquete': stock['box_qty'],
                'fob_unitario': Decimal('0'),
                'precio_plataforma_unitario': Decimal('0'),
                'precio_plataforma_caja': Decimal('0'),
                'volumen_box': stock['volumen'],
                'fecha_importacion': '',
                'clasificacion_impo': '',
                'fecha_recepcion': '',
                'clasificacion_recep': '',
                'dias_impo': '',
                'dias_recep': '',
                'tipo_marca': '',
                'ean': '',
            }
        
        # Calcular unidades
        stock_cajas = stock['stock_cajas']
        box_qty = product['cantidad_paquete'] if product['cantidad_paquete'] > 0 else stock['box_qty']
        stock_unidades = stock_cajas * box_qty
        
        # Parsear fechas
        fecha_impo = parse_date(product['fecha_importacion'])
        fecha_recep = parse_date(product['fecha_recepcion'])
        
        dias_impo = days_since_today(fecha_impo) if fecha_impo else None
        dias_recep = days_since_today(fecha_recep) if fecha_recep else None
        
        # Si no hay fecha parseada, usar días del catálogo
        if dias_impo is None and product['dias_impo']:
            try:
                dias_impo = int(parse_decimal(product['dias_impo']))
            except:
                pass
        
        if dias_recep is None and product['dias_recep']:
            try:
                dias_recep = int(parse_decimal(product['dias_recep']))
            except:
                pass
        
        # Clasificar stock
        clasificacion, riesgo = classify_stock_by_dates(
            dias_recep, dias_impo,
            product['clasificacion_recep'],
            product['clasificacion_impo']
        )
        
        # Obtener precios (priorizar CEG si está disponible, sino usar catálogo)
        fob_unitario = ceg_info.get('fob', product['fob_unitario']) if ceg_info.get('fob', 0) > 0 else product['fob_unitario']
        precio_plataforma = ceg_info.get('base_price', product['precio_plataforma_unitario']) if ceg_info.get('base_price', 0) > 0 else product['precio_plataforma_unitario']
        precio_tu = ceg_info.get('precio_normal_tu', precio_plataforma * Decimal('1.25')) if ceg_info.get('precio_normal_tu', 0) > 0 else (precio_plataforma * Decimal('1.25') if precio_plataforma > 0 else Decimal('0'))
        
        # Calcular valuaciones
        valor_fob = stock_unidades * fob_unitario if fob_unitario > 0 else Decimal('0')
        valor_plataforma = stock_unidades * precio_plataforma if precio_plataforma > 0 else Decimal('0')
        valor_tu = stock_unidades * precio_tu if precio_tu > 0 else Decimal('0')
        margen_unitario = precio_tu - fob_unitario if precio_tu > 0 and fob_unitario > 0 else Decimal('0')
        margen_porcentaje = (margen_unitario / precio_tu * 100) if precio_tu > 0 else Decimal('0')
        ganancia_potencial = valor_tu - valor_fob
        volumen_total = stock_cajas * product['volumen_box'] if product['volumen_box'] > 0 else stock['volumen'] * stock_cajas
        
        inventory.append({
            'SKU': product['sku'],
            'Código D365': product['d365_reference'],
            'Nombre Producto': product['nombre'],
            'Marca': product['marca'],
            'Categoría (2° Nivel)': product['categoria_2'],
            'Categoría Última': product['categoria_ultima'],
            'Stock Cajas': float(stock_cajas),
            'Cantidad por Paquete': float(box_qty),
            'Stock Unidades': float(stock_unidades),
            'FOB Unitario (USD)': float(fob_unitario),
            'Precio Plataforma Unitario (USD)': float(precio_plataforma),
            'Precio TU Unitario (USD)': float(precio_tu),
            'Margen Unitario (USD)': float(margen_unitario),
            'Margen %': float(margen_porcentaje),
            'Valor Stock FOB (USD)': float(valor_fob),
            'Valor Stock Plataforma (USD)': float(valor_plataforma),
            'Valor Stock TU (USD)': float(valor_tu),
            'Ganancia Potencial (USD)': float(ganancia_potencial),
            'Volumen Box (m³)': float(product['volumen_box']),
            'Volumen Total (m³)': float(volumen_total),
            'Fecha Última Importación': product['fecha_importacion'],
            'Días desde Importación': dias_impo if dias_impo is not None else '',
            'Clasificación Importación': product['clasificacion_impo'],
            'Fecha Última Recepción': product['fecha_recepcion'],
            'Días desde Recepción': dias_recep if dias_recep is not None else '',
            'Clasificación Recepción': product['clasificacion_recep'],
            'Clasificación Stock': clasificacion,
            'Riesgo': riesgo,
            'Tipo Marca': product['tipo_marca'],
            'EAN': product['ean'],
        })
    
    # Crear DataFrame
    df = pd.DataFrame(inventory)
    
    # Ordenar por valor de stock TU
    df = df.sort_values('Valor Stock TU (USD)', ascending=False)
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Crear archivo Excel con múltiples hojas
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Hoja principal: Inventario Completo
        df.to_excel(writer, sheet_name='00_Inventario Completo', index=False)
        auto_adjust_column_widths(writer, '00_Inventario Completo', df)
        
        # Hoja: Resumen por Categoría
        resumen_categoria = df.groupby('Categoría (2° Nivel)').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Ganancia Potencial (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_categoria.columns = [
            'Categoría', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Ganancia Potencial (USD)', 'Volumen Total (m³)'
        ]
        resumen_categoria = resumen_categoria.sort_values('Valor TU (USD)', ascending=False)
        resumen_categoria.to_excel(writer, sheet_name='01_Resumen por Categoría', index=False)
        auto_adjust_column_widths(writer, '01_Resumen por Categoría', resumen_categoria)
        
        # Hoja: Resumen por Marca
        resumen_marca = df.groupby('Marca').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Ganancia Potencial (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_marca.columns = [
            'Marca', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Ganancia Potencial (USD)', 'Volumen Total (m³)'
        ]
        resumen_marca = resumen_marca.sort_values('Valor TU (USD)', ascending=False)
        resumen_marca.to_excel(writer, sheet_name='02_Resumen por Marca', index=False)
        auto_adjust_column_widths(writer, '02_Resumen por Marca', resumen_marca)
        
        # Hoja: Clasificación por Riesgo
        resumen_riesgo = df.groupby('Riesgo').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Ganancia Potencial (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_riesgo.columns = [
            'Riesgo', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Ganancia Potencial (USD)', 'Volumen Total (m³)'
        ]
        resumen_riesgo.to_excel(writer, sheet_name='03_Clasificación por Riesgo', index=False)
        auto_adjust_column_widths(writer, '03_Clasificación por Riesgo', resumen_riesgo)
        
        # Hoja: Stock Antiguo (Riesgo Alto)
        stock_antiguo = df[df['Riesgo'] == 'Alto'].sort_values('Valor Stock TU (USD)', ascending=False)
        stock_antiguo.to_excel(writer, sheet_name='04_Stock Antiguo (Alto Riesgo)', index=False)
        auto_adjust_column_widths(writer, '04_Stock Antiguo (Alto Riesgo)', stock_antiguo)
        
        # Hoja: Top 50 por Valor TU
        top_valor = df.nlargest(50, 'Valor Stock TU (USD)')
        top_valor.to_excel(writer, sheet_name='05_Top 50 por Valor TU', index=False)
        auto_adjust_column_widths(writer, '05_Top 50 por Valor TU', top_valor)
        
        # Hoja: Top 50 por Ganancia Potencial
        top_ganancia = df.nlargest(50, 'Ganancia Potencial (USD)')
        top_ganancia.to_excel(writer, sheet_name='06_Top 50 Ganancia Potencial', index=False)
        auto_adjust_column_widths(writer, '06_Top 50 Ganancia Potencial', top_ganancia)
        
        # Hoja: Stock sin Movimiento (sin fechas)
        stock_sin_fecha = df[df['Clasificación Stock'] == 'Sin Fecha'].sort_values('Valor Stock TU (USD)', ascending=False)
        stock_sin_fecha.to_excel(writer, sheet_name='07_Stock Sin Fecha', index=False)
        auto_adjust_column_widths(writer, '07_Stock Sin Fecha', stock_sin_fecha)
        
        # Hoja: Productos con Mejor Margen
        productos_margen = df[df['Margen %'] > 0].nlargest(100, 'Margen %')
        productos_margen.to_excel(writer, sheet_name='08_Mejor Margen %', index=False)
        auto_adjust_column_widths(writer, '08_Mejor Margen %', productos_margen)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    # Estadísticas
    print(f"\n📊 Estadísticas del Inventario:")
    print(f"   Total productos con stock: {len(df)}")
    print(f"   Total stock en cajas: {df['Stock Cajas'].sum():,.0f}")
    print(f"   Total stock en unidades: {df['Stock Unidades'].sum():,.0f}")
    print(f"   Valor total FOB: ${df['Valor Stock FOB (USD)'].sum():,.2f}")
    print(f"   Valor total Plataforma: ${df['Valor Stock Plataforma (USD)'].sum():,.2f}")
    print(f"   Valor total TU: ${df['Valor Stock TU (USD)'].sum():,.2f}")
    print(f"   Ganancia potencial total: ${df['Ganancia Potencial (USD)'].sum():,.2f}")
    print(f"   Volumen total: {df['Volumen Total (m³)'].sum():,.2f} m³")
    print(f"\n   Clasificación por Riesgo:")
    for riesgo, count in df['Riesgo'].value_counts().items():
        print(f"      {riesgo}: {count} productos")
    print(f"\n   Margen promedio: {df['Margen %'].mean():.2f}%")
    print(f"   Productos con margen > 30%: {len(df[df['Margen %'] > 30])}")


if __name__ == "__main__":
    if not HAS_PANDAS:
        print("Instalando pandas...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    print("🔄 Iniciando análisis de inventario...")
    generate_inventory_analysis()
    print("\n✨ Proceso completado!")
