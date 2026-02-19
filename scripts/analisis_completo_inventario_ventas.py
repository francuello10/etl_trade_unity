#!/usr/bin/env python3
"""
Script para generar análisis completo combinando inventario y ventas:
- Valuación a precios TU (plataforma x 1.25) y FOB
- Análisis de ventas: si se vendió, clientes, cajas, unidades, precios max/min/avg, última venta
- Informes de valuación de stock
- Informes de inventario en volumen m³
- Genera mega Excel con todo
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
CATALOGO_TU = "fuentes/Catalogo TU.csv"
STOCK_ERP = "fuentes/stock erp.csv"
VENTAS_CSV = "ventas_historicas_items_FINAL.csv"
OUTPUT_EXCEL = "MEGA_ANALISIS_Completo_TradeUnity.xlsx"


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
    
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%Y %H:%M"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None


def days_since_today(target_date: date) -> int:
    """Calcula días desde hoy."""
    if not target_date:
        return None
    today = date.today()
    return (today - target_date).days


def classify_stock_by_dates(dias_recepcion, dias_importacion, clasif_recep, clasif_impo):
    """Clasifica stock según fechas."""
    clasificacion = []
    riesgo = "Bajo"
    
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
    print(f"📖 Cargando catálogo TU...")
    
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
            
            if d365_ref:
                catalog[d365_ref] = catalog[sku]
    
    print(f"   ✅ {len(catalog)} productos cargados")
    return catalog


def load_stock():
    """Carga stock del ERP."""
    print(f"📖 Cargando stock del ERP...")
    
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
            })
    
    print(f"   ✅ {len(stock_data)} productos con stock")
    return stock_data


def load_ventas():
    """Carga datos de ventas."""
    print(f"📖 Cargando datos de ventas...")
    
    ventas_por_sku = defaultdict(lambda: {
        'vendido': False,
        'clientes_unicos': set(),
        'ordenes_unicas': set(),
        'cantidad_cajas': Decimal('0'),
        'cantidad_unidades': Decimal('0'),
        'precios_unitarios': [],
        'precios_caja': [],
        'fechas_venta': [],
        'total_facturado': Decimal('0'),
    })
    
    with open(VENTAS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = str(row.get('SKU', '')).strip().upper()
            if not sku:
                continue
            
            ventas_por_sku[sku]['vendido'] = True
            ventas_por_sku[sku]['clientes_unicos'].add(row.get('Email Cliente', ''))
            ventas_por_sku[sku]['ordenes_unicas'].add(row.get('Número de Orden', ''))
            
            cantidad_cajas = parse_decimal(row.get('Cantidad', ''))
            cantidad_unidades = parse_decimal(row.get('Cantidad Unitarias', ''))
            precio_unitario = parse_decimal(row.get('Precio Venta Unitario', ''))
            precio_caja = parse_decimal(row.get('Precio Venta', ''))
            fecha_venta = parse_date(row.get('Fecha Creación', ''))
            total_item = parse_decimal(row.get('Total Item con IVA', ''))
            
            ventas_por_sku[sku]['cantidad_cajas'] += cantidad_cajas
            ventas_por_sku[sku]['cantidad_unidades'] += cantidad_unidades
            ventas_por_sku[sku]['total_facturado'] += total_item
            
            if precio_unitario > 0:
                ventas_por_sku[sku]['precios_unitarios'].append(precio_unitario)
            if precio_caja > 0:
                ventas_por_sku[sku]['precios_caja'].append(precio_caja)
            if fecha_venta:
                ventas_por_sku[sku]['fechas_venta'].append(fecha_venta)
    
    print(f"   ✅ {len(ventas_por_sku)} SKUs con datos de ventas")
    return ventas_por_sku


def generate_complete_analysis():
    """Genera análisis completo combinando inventario y ventas."""
    print("🔄 Generando análisis completo...")
    
    # Cargar datos
    catalog = load_catalog()
    stock_data = load_stock()
    ventas_data = load_ventas()
    
    # Combinar datos
    inventory = []
    
    print("\n🔄 Combinando datos y calculando...")
    
    for stock in stock_data:
        d365_ref = stock['d365_reference']
        
        # Buscar en catálogo
        product = catalog.get(d365_ref) or catalog.get(d365_ref.upper())
        
        if not product:
            product = {
                'sku': d365_ref,
                'd365_reference': d365_ref,
                'nombre': '',
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
        
        sku = product['sku']
        
        # Calcular unidades
        stock_cajas = stock['stock_cajas']
        box_qty = product['cantidad_paquete'] if product['cantidad_paquete'] > 0 else stock['box_qty']
        stock_unidades = stock_cajas * box_qty
        
        # Parsear fechas
        fecha_impo = parse_date(product['fecha_importacion'])
        fecha_recep = parse_date(product['fecha_recepcion'])
        
        dias_impo = days_since_today(fecha_impo) if fecha_impo else None
        dias_recep = days_since_today(fecha_recep) if fecha_recep else None
        
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
        
        # Datos de ventas
        ventas = ventas_data.get(sku, {
            'vendido': False,
            'clientes_unicos': set(),
            'ordenes_unicas': set(),
            'cantidad_cajas': Decimal('0'),
            'cantidad_unidades': Decimal('0'),
            'precios_unitarios': [],
            'precios_caja': [],
            'fechas_venta': [],
            'total_facturado': Decimal('0'),
        })
        
        # Calcular métricas de ventas
        num_clientes = len(ventas['clientes_unicos'])
        num_ordenes = len(ventas['ordenes_unicas'])
        precio_unit_max = max(ventas['precios_unitarios']) if ventas['precios_unitarios'] else 0
        precio_unit_min = min(ventas['precios_unitarios']) if ventas['precios_unitarios'] else 0
        precio_unit_avg = sum(ventas['precios_unitarios']) / len(ventas['precios_unitarios']) if ventas['precios_unitarios'] else 0
        precio_caja_max = max(ventas['precios_caja']) if ventas['precios_caja'] else 0
        precio_caja_min = min(ventas['precios_caja']) if ventas['precios_caja'] else 0
        precio_caja_avg = sum(ventas['precios_caja']) / len(ventas['precios_caja']) if ventas['precios_caja'] else 0
        ultima_venta = max(ventas['fechas_venta']) if ventas['fechas_venta'] else None
        dias_desde_ultima_venta = days_since_today(ultima_venta) if ultima_venta else None
        
        # Calcular valuaciones
        precio_plataforma = product['precio_plataforma_unitario']
        precio_tu = precio_plataforma * Decimal('1.25')  # Plataforma x 1.25
        fob_unitario = product['fob_unitario']
        
        valor_fob = stock_unidades * fob_unitario if fob_unitario > 0 else Decimal('0')
        valor_plataforma = stock_unidades * precio_plataforma if precio_plataforma > 0 else Decimal('0')
        valor_tu = stock_unidades * precio_tu if precio_tu > 0 else Decimal('0')
        
        volumen_total = stock_cajas * product['volumen_box'] if product['volumen_box'] > 0 else stock['volumen'] * stock_cajas
        
        inventory.append({
            'SKU': sku,
            'Código D365': product['d365_reference'],
            'Nombre Producto': product['nombre'],
            'Marca': product['marca'],
            'Categoría (2° Nivel)': product['categoria_2'],
            'Categoría Última': product['categoria_ultima'],
            'Stock Cajas': float(stock_cajas),
            'Cantidad por Paquete': float(box_qty),
            'Stock Unidades': float(stock_unidades),
            'FOB Unitario': float(fob_unitario),
            'Precio Plataforma Unitario': float(precio_plataforma),
            'Precio TU Unitario (Plataforma x1.25)': float(precio_tu),
            'Valor Stock FOB (USD)': float(valor_fob),
            'Valor Stock Plataforma (USD)': float(valor_plataforma),
            'Valor Stock TU (USD)': float(valor_tu),
            'Volumen Box': float(product['volumen_box']),
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
            # Datos de ventas
            'Se Vendió': 'Sí' if ventas['vendido'] else 'No',
            'Número de Clientes': num_clientes,
            'Número de Órdenes': num_ordenes,
            'Cajas Vendidas': float(ventas['cantidad_cajas']),
            'Unidades Vendidas': float(ventas['cantidad_unidades']),
            'Precio Unitario Max': float(precio_unit_max),
            'Precio Unitario Min': float(precio_unit_min),
            'Precio Unitario Promedio': float(precio_unit_avg),
            'Precio Caja Max': float(precio_caja_max),
            'Precio Caja Min': float(precio_caja_min),
            'Precio Caja Promedio': float(precio_caja_avg),
            'Última Venta': ultima_venta.strftime('%Y-%m-%d') if ultima_venta else '',
            'Días desde Última Venta': dias_desde_ultima_venta if dias_desde_ultima_venta is not None else '',
            'Total Facturado (USD)': float(ventas['total_facturado']),
        })
    
    # Crear DataFrame
    df = pd.DataFrame(inventory)
    df = df.sort_values('Valor Stock TU (USD)', ascending=False)
    
    # Crear archivo Excel con múltiples hojas
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Hoja principal: Inventario Completo
        df.to_excel(writer, sheet_name='00_Inventario Completo', index=False)
        
        # Hoja: Resumen por Categoría
        resumen_categoria = df.groupby('Categoría (2° Nivel)').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_categoria.columns = [
            'Categoría', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Volumen Total (m³)'
        ]
        resumen_categoria = resumen_categoria.sort_values('Valor TU (USD)', ascending=False)
        resumen_categoria.to_excel(writer, sheet_name='01_Resumen por Categoría', index=False)
        
        # Hoja: Resumen por Marca
        resumen_marca = df.groupby('Marca').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_marca.columns = [
            'Marca', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Volumen Total (m³)'
        ]
        resumen_marca = resumen_marca.sort_values('Valor TU (USD)', ascending=False)
        resumen_marca.to_excel(writer, sheet_name='02_Resumen por Marca', index=False)
        
        # Hoja: Clasificación por Riesgo
        resumen_riesgo = df.groupby('Riesgo').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        resumen_riesgo.columns = [
            'Riesgo', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Volumen Total (m³)'
        ]
        resumen_riesgo.to_excel(writer, sheet_name='03_Clasificación por Riesgo', index=False)
        
        # Hoja: Análisis de Ventas
        analisis_ventas = df.groupby('Se Vendió').agg({
            'SKU': 'nunique',
            'Stock Cajas': 'sum',
            'Stock Unidades': 'sum',
            'Valor Stock FOB (USD)': 'sum',
            'Valor Stock Plataforma (USD)': 'sum',
            'Valor Stock TU (USD)': 'sum',
            'Volumen Total (m³)': 'sum',
        }).reset_index()
        analisis_ventas.columns = [
            'Se Vendió', 'Productos Únicos', 'Stock Cajas', 'Stock Unidades',
            'Valor FOB (USD)', 'Valor Plataforma (USD)', 'Valor TU (USD)', 'Volumen Total (m³)'
        ]
        analisis_ventas.to_excel(writer, sheet_name='04_Análisis Ventas', index=False)
        
        # Hoja: Productos Sin Venta
        sin_venta = df[df['Se Vendió'] == 'No'].sort_values('Valor Stock TU (USD)', ascending=False)
        sin_venta.to_excel(writer, sheet_name='05_Productos Sin Venta', index=False)
        
        # Hoja: Top 50 por Valor TU
        top_valor = df.nlargest(50, 'Valor Stock TU (USD)')
        top_valor.to_excel(writer, sheet_name='06_Top 50 por Valor TU', index=False)
        
        # Hoja: Resumen Valuación
        resumen_valuacion = pd.DataFrame({
            'Valuación': ['FOB', 'Plataforma CEG', 'TU (Plataforma x1.25)'],
            'Valor Total (USD)': [
                df['Valor Stock FOB (USD)'].sum(),
                df['Valor Stock Plataforma (USD)'].sum(),
                df['Valor Stock TU (USD)'].sum(),
            ],
            'Stock Total Cajas': [df['Stock Cajas'].sum()] * 3,
            'Stock Total Unidades': [df['Stock Unidades'].sum()] * 3,
            'Volumen Total (m³)': [df['Volumen Total (m³)'].sum()] * 3,
        })
        resumen_valuacion.to_excel(writer, sheet_name='07_Resumen Valuación', index=False)
        
        # Hoja: Resumen Volumen
        resumen_volumen = df.groupby('Categoría (2° Nivel)').agg({
            'Volumen Total (m³)': 'sum',
            'Stock Cajas': 'sum',
            'SKU': 'nunique',
        }).reset_index()
        resumen_volumen.columns = ['Categoría', 'Volumen Total (m³)', 'Stock Cajas', 'Productos Únicos']
        resumen_volumen = resumen_volumen.sort_values('Volumen Total (m³)', ascending=False)
        resumen_volumen.to_excel(writer, sheet_name='08_Resumen Volumen', index=False)
        
        # Hoja: Stock Antiguo (Alto Riesgo)
        stock_antiguo = df[df['Riesgo'] == 'Alto'].sort_values('Valor Stock TU (USD)', ascending=False)
        stock_antiguo.to_excel(writer, sheet_name='09_Stock Antiguo (Alto Riesgo)', index=False)
        
        # Hoja: Productos con Mayor Rotación
        con_venta = df[df['Se Vendió'] == 'Sí'].copy()
        con_venta['Rotación'] = con_venta['Unidades Vendidas'] / con_venta['Stock Unidades']
        con_venta = con_venta.sort_values('Rotación', ascending=False)
        con_venta.to_excel(writer, sheet_name='10_Productos con Mayor Rotación', index=False)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    # Estadísticas
    print(f"\n📊 Estadísticas del Inventario:")
    print(f"   Total productos con stock: {len(df)}")
    print(f"   Total stock en cajas: {df['Stock Cajas'].sum():,.0f}")
    print(f"   Total stock en unidades: {df['Stock Unidades'].sum():,.0f}")
    print(f"   Valor total FOB: ${df['Valor Stock FOB (USD)'].sum():,.2f}")
    print(f"   Valor total Plataforma: ${df['Valor Stock Plataforma (USD)'].sum():,.2f}")
    print(f"   Valor total TU: ${df['Valor Stock TU (USD)'].sum():,.2f}")
    print(f"   Volumen total: {df['Volumen Total (m³)'].sum():,.2f} m³")
    print(f"\n   Productos vendidos: {len(df[df['Se Vendió'] == 'Sí'])}")
    print(f"   Productos sin venta: {len(df[df['Se Vendió'] == 'No'])}")
    print(f"\n   Clasificación por Riesgo:")
    for riesgo, count in df['Riesgo'].value_counts().items():
        print(f"      {riesgo}: {count} productos")


if __name__ == "__main__":
    if not HAS_PANDAS:
        print("Instalando pandas...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    print("🔄 Iniciando análisis completo de inventario y ventas...")
    generate_complete_analysis()
    print("\n✨ Proceso completado!")
