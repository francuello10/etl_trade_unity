#!/usr/bin/env python3
"""
Análisis de Inteligencia Comercial: Publicaciones y Pricing - Trade Unity

Alineado con documento base Trade Unity:
- Ecommerce B2B mayorista del grupo CEG
- Stack: Magento 2, Odoo, Connectif
- Principios: No romper operación por promos (respetar precios recientes), 
  reglas trazables (descuentos documentados)

Analiza:
- Compara precios publicados vs precio normal TU (Plataforma * 1.25)
- Impacto en ventas por período de publicación
- Efectividad de ofertas y eventos comerciales
- Comparación 2024 vs 2025
- Stock actual de productos publicados
"""

import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from collections import defaultdict
import pandas as pd

# Archivos
PUBLICACIONES_CSV = "fuentes/publicaciones_productos.csv"
CEG_PRODUCTOS_CSV = "fuentes/precios_plataforma_ceg.csv"
VENTAS_CSV = "inputs/ventas_historicas_items.csv"  # Fuente: ventas.xlsx hoja 01_Ventas
STOCK_ERP = "fuentes/stock_erp.csv"
CATALOGO_TU = "fuentes/catalogo_trade_unity.csv"
CALENDARIO_CSV = "fuentes/calendario_comercial_2026.csv"
OUTPUT_DIR = "outputs"
OUTPUT_EXCEL = f"{OUTPUT_DIR}/TradeUnity Pricing Intelligence.xlsx"


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


def clean_period_name(column_name: str) -> str:
    """Limpia y unifica nombres de períodos para mayor legibilidad."""
    name = column_name
    
    # Remover prefijos comunes
    name = re.sub(r'^Precio\s+Unitario\s*', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Limpiar eventos especiales primero
    # Remover paréntesis alrededor de eventos
    name = re.sub(r'^\(([^)]+)\)\s*', r'\1 ', name)
    
    eventos_clean = {
        r'Summer Sale\s+Enero\s*/\s*FE?brero': 'Summer Sale Enero/Febrero',
        r'Summer Sale\s+2026\s+enero': 'Summer Sale Enero 2026',
        r'Summer Sale': 'Summer Sale',
        r'Hot Week': 'Hot Week',
        r'Pre Hot Sale\s+2': 'Pre Hot Sale 2',
        r'Pre Hot Sale': 'Pre Hot Sale',
        r'Post\s+HOTSALE': 'Post Hot Sale',
        r'Dia del Niño': 'Día del Niño',
        r'Liq\s+Julio': 'Liquidación Julio',
        r'Pre\s+CyberSale': 'Pre Cyber Sale',
        r'Blackfriday': 'Black Friday',
        r'Especial\s+Fiestas': 'Especial Fiestas',
        r'LIQUIDACION\s+ENERO/FEBRERO\s+2026': 'Liquidación Enero/Febrero 2026',
        r'Precio\s+LIQUIDACION\s+ENERO/FEBRERO\s+2026\s+unitario\s+neto': 'Liquidación Enero/Febrero 2026',
        r'Precio\s+LIQUIDACION\s+ENERO/FEBRERO\s+2026': 'Liquidación Enero/Febrero 2026',
    }
    
    for evento_orig, evento_clean in eventos_clean.items():
        if re.search(evento_orig, name, re.IGNORECASE):
            name = re.sub(evento_orig, evento_clean, name, flags=re.IGNORECASE)
            # Limpiar espacios y retornar
            name = ' '.join(name.split())
            # Si es un evento especial sin fechas, retornar directamente
            if not re.search(r'\d{1,2}\s+(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)', name):
                return name.strip()
    
    # Si tiene fechas, formatear
    meses = {
        '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'
    }
    
    # Patrón: (DD-MM-YYYY al DD-MM-YYYY) o sin paréntesis
    pattern1 = r'\(?(\d{1,2})-(\d{1,2})-(\d{4})\s+al\s+(\d{1,2})-(\d{1,2})-(\d{4})\)?'
    match1 = re.search(pattern1, name)
    if match1:
        dia_i, mes_i, año_i, dia_f, mes_f, año_f = match1.groups()
        return f"{dia_i} {meses.get(mes_i, mes_i)} {año_i} - {dia_f} {meses.get(mes_f, mes_f)} {año_f}"
    
    # Patrón: (DD-MM al DD-MM) YYYY o sin paréntesis
    pattern2 = r'\(?(\d{1,2})-(\d{1,2})\s+al\s+(\d{1,2})-(\d{1,2})\)?\s+(\d{4})'
    match2 = re.search(pattern2, name)
    if match2:
        dia_i, mes_i, dia_f, mes_f, año = match2.groups()
        return f"{dia_i} {meses.get(mes_i, mes_i)} - {dia_f} {meses.get(mes_f, mes_f)} {año}"
    
    # Patrón: Evento (DD-MM al DD-MM) YYYY
    pattern3 = r'Evento\s+\(?(\d{1,2})-(\d{1,2})\s+al\s+(\d{1,2})-(\d{1,2})\)?\s+(\d{4})'
    match3 = re.search(pattern3, name)
    if match3:
        dia_i, mes_i, dia_f, mes_f, año = match3.groups()
        return f"Evento {dia_i} {meses.get(mes_i, mes_i)} - {dia_f} {meses.get(mes_f, mes_f)} {año}"
    
    # Limpiar paréntesis y espacios
    name = name.replace('(', '').replace(')', '').strip()
    name = ' '.join(name.split())
    
    return name if name else column_name


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


def parse_date_from_column(column_name: str):
    """
    Extrae fechas desde-hasta de nombres de columnas de publicaciones.
    Ejemplos:
    - "Precio Unitario (25-10 al 01-11) 2024" -> (2024-10-25, 2024-11-01)
    - "Precio Unitario (26-12-2024 al 08-01-2025)" -> (2024-12-26, 2025-01-08)
    """
    # Buscar patrón de fechas
    patterns = [
        r'\((\d{1,2})-(\d{1,2})\s+al\s+(\d{1,2})-(\d{1,2})\)\s+(\d{4})',  # (25-10 al 01-11) 2024
        r'\((\d{1,2})-(\d{1,2})-(\d{4})\s+al\s+(\d{1,2})-(\d{1,2})-(\d{4})\)',  # (26-12-2024 al 08-01-2025)
        r'\((\d{1,2})-(\d{1,2})\s+al\s+(\d{1,2})-(\d{1,2})\)',  # Sin año (asumir año anterior o inferir)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, column_name)
        if match:
            groups = match.groups()
            
            if len(groups) == 5:  # (25-10 al 01-11) 2024
                dia_inicio, mes_inicio, dia_fin, mes_fin, año = groups
                try:
                    fecha_inicio = date(int(año), int(mes_inicio), int(dia_inicio))
                    # Si mes_fin < mes_inicio, es del año siguiente
                    año_fin = int(año) if int(mes_fin) >= int(mes_inicio) else int(año) + 1
                    fecha_fin = date(año_fin, int(mes_fin), int(dia_fin))
                    return fecha_inicio, fecha_fin
                except:
                    pass
            
            elif len(groups) == 6:  # (26-12-2024 al 08-01-2025)
                dia_inicio, mes_inicio, año_inicio, dia_fin, mes_fin, año_fin = groups
                try:
                    fecha_inicio = date(int(año_inicio), int(mes_inicio), int(dia_inicio))
                    fecha_fin = date(int(año_fin), int(mes_fin), int(dia_fin))
                    return fecha_inicio, fecha_fin
                except:
                    pass
    
    # Buscar eventos especiales y mapear a fechas aproximadas
    eventos_fechas = {
        'Summer Sale': (date(2025, 1, 1), date(2025, 2, 28)),
        'Hot Week': (date(2025, 5, 1), date(2025, 5, 7)),
        'Pre Hot Sale': (date(2025, 4, 20), date(2025, 4, 30)),
        'Pre Hot Sale 2': (date(2025, 4, 25), date(2025, 5, 5)),
        'Post HOTSALE': (date(2025, 5, 8), date(2025, 5, 15)),
        'Dia del Niño': (date(2025, 7, 20), date(2025, 8, 3)),
        'Liq Julio': (date(2025, 7, 1), date(2025, 7, 31)),
        'Pre CyberSale': (date(2025, 10, 1), date(2025, 10, 31)),
        'Blackfriday': (date(2025, 11, 24), date(2025, 11, 30)),
        'Especial Fiestas': (date(2025, 12, 15), date(2025, 12, 31)),
        'LIQUIDACION ENERO/FEBRERO 2026': (date(2026, 1, 1), date(2026, 2, 28)),
    }
    
    for evento, fechas in eventos_fechas.items():
        if evento.lower() in column_name.lower():
            return fechas
    
    return None, None


def load_ceg_prices():
    """Carga precios FOB y Plataforma desde archivo CEG."""
    print("📖 Cargando precios CEG (FOB y Plataforma)...")
    
    ceg_prices = {}
    
    with open(CEG_PRODUCTOS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = str(row.get('sku', '')).strip().upper()
            base_price = parse_decimal(row.get('base_price', ''))
            fob = parse_decimal(row.get('fob', ''))
            
            if sku:
                ceg_prices[sku] = {
                    'base_price': base_price,  # Precio Plataforma
                    'fob': fob,
                    'precio_normal_tu': base_price * Decimal('1.25'),  # Precio normal Trade Unity
                }
    
    print(f"   ✅ {len(ceg_prices)} productos con precios CEG cargados")
    return ceg_prices


def load_publicaciones():
    """Carga publicaciones y estructura por períodos."""
    print("📖 Cargando publicaciones de productos...")
    
    df = pd.read_csv(PUBLICACIONES_CSV, encoding='utf-8-sig')
    
    publicaciones_data = []
    periodos_info = []
    
    # Procesar cada columna de precio (excepto SKU y D365)
    precio_columns = [col for col in df.columns if 'Precio' in col or 'Evento' in col or 'Sale' in col or 'LIQUIDACION' in col]
    
    print(f"   📅 {len(precio_columns)} períodos de publicación encontrados")
    
    for col in precio_columns:
        fecha_inicio, fecha_fin = parse_date_from_column(col)
        
        nombre_limpio = clean_period_name(col)
        
        if fecha_inicio and fecha_fin:
            periodos_info.append({
                'columna': col,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'nombre_periodo': nombre_limpio,
            })
        else:
            # Si no se puede parsear, intentar inferir del nombre
            periodos_info.append({
                'columna': col,
                'fecha_inicio': None,
                'fecha_fin': None,
                'nombre_periodo': nombre_limpio,
            })
    
    # Ordenar períodos por fecha
    periodos_info.sort(key=lambda x: x['fecha_inicio'] if x['fecha_inicio'] else date(2099, 12, 31))
    
    # Procesar cada producto
    for idx, row in df.iterrows():
        sku = str(row.get('sku', '')).strip().upper()
        if not sku:
            continue
        
        # Para cada período, extraer precio publicado
        for periodo in periodos_info:
            precio_str = str(row.get(periodo['columna'], '')).strip()
            
            if precio_str and precio_str not in ['', 'nan', 'None']:
                precio_publicado = parse_decimal(precio_str)
                
                if precio_publicado > 0:
                    publicaciones_data.append({
                        'sku': sku,
                        'periodo': periodo['nombre_periodo'],
                        'fecha_inicio': periodo['fecha_inicio'],
                        'fecha_fin': periodo['fecha_fin'],
                        'precio_publicado': precio_publicado,
                    })
    
    print(f"   ✅ {len(publicaciones_data)} publicaciones cargadas")
    return publicaciones_data, periodos_info


def load_ventas():
    """Carga datos de ventas."""
    print("📖 Cargando datos de ventas...")
    
    import os
    if not os.path.exists(VENTAS_CSV):
        print(f"   ⚠️  Archivo de ventas no encontrado: {VENTAS_CSV}")
        print("   📝 Creando DataFrame vacío con estructura necesaria...")
        # Crear DataFrame vacío con columnas necesarias según documento base Trade Unity
        df = pd.DataFrame(columns=[
            'SKU', 'Nombre Producto', 'Brand Name CEG', 'Categoría (2° Nivel)',
            'Cantidad Unitarias', 'Total Item con IVA', 'Precio Venta Unitario',
            'Fecha Creación', 'Email Cliente', 'Número de Orden'
        ])
        print("   ✅ DataFrame vacío creado (sin datos de ventas históricas)")
        return df
    
    df = pd.read_csv(VENTAS_CSV, encoding='utf-8-sig')
    
    # Convertir fecha si existe
    if 'Fecha Creación' in df.columns:
        df['Fecha Creación'] = pd.to_datetime(df['Fecha Creación'], errors='coerce')
    
    # Convertir columnas numéricas
    numeric_cols = ['Precio Original', 'Precio Venta', 'Precio Venta Unitario', 
                    'Total Item', 'Total Item con IVA', 'Cantidad Unitarias']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convertir fechas
    df['Fecha Creación'] = pd.to_datetime(df['Fecha Creación'], errors='coerce')
    
    print(f"   ✅ {len(df)} registros de ventas cargados")
    return df


def analyze_pricing_impact(publicaciones_data, ceg_prices, ventas_df, periodos_info, writer):
    """Analiza impacto de pricing en ventas."""
    print("📊 Analizando impacto de pricing...")
    
    # 1. Análisis de precios publicados vs precio normal
    analisis_precios = []
    
    for pub in publicaciones_data:
        sku = pub['sku']
        precio_publicado = pub['precio_publicado']
        ceg_info = ceg_prices.get(sku, {})
        
        precio_normal = ceg_info.get('precio_normal_tu', Decimal('0'))
        precio_plataforma = ceg_info.get('base_price', Decimal('0'))
        fob = ceg_info.get('fob', Decimal('0'))
        
        if precio_normal > 0:
            descuento_pct = ((precio_normal - precio_publicado) / precio_normal * 100) if precio_normal > 0 else Decimal('0')
            es_descuento = precio_publicado < precio_normal
            
            margen_vs_fob = precio_publicado - fob if fob > 0 else Decimal('0')
            margen_vs_plataforma = precio_publicado - precio_plataforma if precio_plataforma > 0 else Decimal('0')
            
            analisis_precios.append({
                'SKU': sku,
                'Período': pub['periodo'],
                'Fecha Inicio': pub['fecha_inicio'].strftime('%Y-%m-%d') if pub['fecha_inicio'] else '',
                'Fecha Fin': pub['fecha_fin'].strftime('%Y-%m-%d') if pub['fecha_fin'] else '',
                'Precio Publicado': float(precio_publicado),
                'Precio Normal TU': float(precio_normal),
                'Precio Plataforma': float(precio_plataforma),
                'FOB': float(fob),
                'Descuento (%)': float(descuento_pct),
                'Es Descuento': 'Sí' if es_descuento else 'No',
                'Margen vs FOB': float(margen_vs_fob),
                'Margen vs Plataforma': float(margen_vs_plataforma),
                '% Margen vs FOB': float((margen_vs_fob / fob * 100) if fob > 0 else 0),
                '% Margen vs Plataforma': float((margen_vs_plataforma / precio_plataforma * 100) if precio_plataforma > 0 else 0),
            })
    
    df_precios = pd.DataFrame(analisis_precios)
    df_precios.to_excel(writer, sheet_name='01_Pricing Publicaciones', index=False)
    auto_adjust_column_widths(writer, '01_Pricing Publicaciones', df_precios)
    print(f"   ✅ {len(analisis_precios)} registros de pricing analizados")
    
    # 2. Análisis de ventas durante períodos de publicación
    analisis_ventas_periodo = []
    
    for periodo in periodos_info:
        if not periodo['fecha_inicio'] or not periodo['fecha_fin']:
            continue
        
        # Filtrar ventas en el período
        ventas_periodo = ventas_df[
            (ventas_df['Fecha Creación'] >= pd.Timestamp(periodo['fecha_inicio'])) &
            (ventas_df['Fecha Creación'] <= pd.Timestamp(periodo['fecha_fin']))
        ].copy()
        
        if len(ventas_periodo) == 0:
            continue
        
        # Productos publicados en este período
        productos_publicados = [p['sku'] for p in publicaciones_data 
                               if p.get('periodo') == periodo['nombre_periodo']]
        
        # Ventas de productos publicados vs no publicados
        ventas_publicados = ventas_periodo[ventas_periodo['SKU'].isin(productos_publicados)]
        ventas_no_publicados = ventas_periodo[~ventas_periodo['SKU'].isin(productos_publicados)]
        
        analisis_ventas_periodo.append({
            'Período': periodo['nombre_periodo'],
            'Fecha Inicio': periodo['fecha_inicio'].strftime('%Y-%m-%d'),
            'Fecha Fin': periodo['fecha_fin'].strftime('%Y-%m-%d'),
            'Productos Publicados': len(productos_publicados),
            'Total Ventas (USD)': float(ventas_periodo['Total Item con IVA'].sum()),
            'Ventas Productos Publicados (USD)': float(ventas_publicados['Total Item con IVA'].sum()),
            'Ventas Productos NO Publicados (USD)': float(ventas_no_publicados['Total Item con IVA'].sum()),
            '% Ventas de Publicados': float((ventas_publicados['Total Item con IVA'].sum() / ventas_periodo['Total Item con IVA'].sum() * 100) if ventas_periodo['Total Item con IVA'].sum() > 0 else 0),
            'Unidades Vendidas Publicados': int(ventas_publicados['Cantidad Unitarias'].sum()),
            'Unidades Vendidas NO Publicados': int(ventas_no_publicados['Cantidad Unitarias'].sum()),
            'Órdenes Totales': int(ventas_periodo['Número de Orden'].nunique()),
        })
    
    df_ventas_periodo = pd.DataFrame(analisis_ventas_periodo)
    df_ventas_periodo.to_excel(writer, sheet_name='02_Impacto Ventas por Período', index=False)
    auto_adjust_column_widths(writer, '02_Impacto Ventas por Período', df_ventas_periodo)
    print(f"   ✅ {len(analisis_ventas_periodo)} períodos analizados")
    
    # 3. Análisis de productos: precio original vs descuento en ventas
    print("📊 Analizando ventas a precio original vs descuento...")
    
    # Verificar si hay datos de ventas y columnas necesarias
    # Verificar si hay datos de ventas y columnas necesarias
    if len(ventas_df) == 0 or 'Precio Original' not in ventas_df.columns:
        print("   ⚠️  Sin datos de ventas o columnas necesarias, saltando análisis de descuentos...")
        resumen_precio = {
            'Total Items Vendidos': 0,
            'Items a Precio Original': 0,
            'Items con Descuento': 0,
            '% Vendidos a Precio Original': 0,
            '% Vendidos con Descuento': 0,
            'Facturación Precio Original (USD)': 0,
            'Facturación con Descuento (USD)': 0,
            'Descuento Promedio (%)': 0,
        }
        df_resumen_precio = pd.DataFrame([resumen_precio])
    else:
        ventas_con_precio = ventas_df[ventas_df['Precio Original'] > 0].copy()
        if len(ventas_con_precio) > 0:
            ventas_con_precio['Es Descuento'] = ventas_con_precio['Precio Venta'] < ventas_con_precio['Precio Original']
            ventas_con_precio['Descuento %'] = ((ventas_con_precio['Precio Original'] - ventas_con_precio['Precio Venta']) / 
                                                ventas_con_precio['Precio Original'] * 100)
            
            resumen_precio = {
                'Total Items Vendidos': len(ventas_con_precio),
                'Items a Precio Original': len(ventas_con_precio[~ventas_con_precio['Es Descuento']]),
                'Items con Descuento': len(ventas_con_precio[ventas_con_precio['Es Descuento']]),
                '% Vendidos a Precio Original': float(len(ventas_con_precio[~ventas_con_precio['Es Descuento']]) / len(ventas_con_precio) * 100) if len(ventas_con_precio) > 0 else 0,
                '% Vendidos con Descuento': float(len(ventas_con_precio[ventas_con_precio['Es Descuento']]) / len(ventas_con_precio) * 100) if len(ventas_con_precio) > 0 else 0,
                'Facturación Precio Original (USD)': float(ventas_con_precio[~ventas_con_precio['Es Descuento']]['Total Item con IVA'].sum()) if 'Total Item con IVA' in ventas_con_precio.columns else 0,
                'Facturación con Descuento (USD)': float(ventas_con_precio[ventas_con_precio['Es Descuento']]['Total Item con IVA'].sum()) if 'Total Item con IVA' in ventas_con_precio.columns else 0,
                'Descuento Promedio (%)': float(ventas_con_precio[ventas_con_precio['Es Descuento']]['Descuento %'].mean()) if len(ventas_con_precio[ventas_con_precio['Es Descuento']]) > 0 else 0,
            }
            df_resumen_precio = pd.DataFrame([resumen_precio])
        else:
            resumen_precio = {
                'Total Items Vendidos': 0,
                'Items a Precio Original': 0,
                'Items con Descuento': 0,
                '% Vendidos a Precio Original': 0,
                '% Vendidos con Descuento': 0,
                'Facturación Precio Original (USD)': 0,
                'Facturación con Descuento (USD)': 0,
                'Descuento Promedio (%)': 0,
            }
            df_resumen_precio = pd.DataFrame([resumen_precio])
    df_resumen_precio.to_excel(writer, sheet_name='03_Resumen Precio vs Descuento', index=False)
    print(f"   ✅ Resumen de precios generado")
    
    # 4. Análisis por producto: comparación precio publicado vs precio vendido
    print("📊 Analizando productos individuales...")
    analisis_producto = []
    
    # Verificar si hay datos de ventas
    if len(ventas_df) > 0 and 'SKU' in ventas_df.columns:
        productos_publicados_set = set([p['sku'] for p in publicaciones_data])
        
        for sku in productos_publicados_set:
            # Publicaciones de este producto
            pubs_producto = [p for p in publicaciones_data if p['sku'] == sku]
            
            # Ventas de este producto
            ventas_producto = ventas_df[ventas_df['SKU'] == sku].copy()
            
            if len(ventas_producto) == 0:
                continue
        
        ceg_info = ceg_prices.get(sku, {})
        precio_normal = ceg_info.get('precio_normal_tu', Decimal('0'))
        
        # Precio promedio publicado
        precios_publicados = [p['precio_publicado'] for p in pubs_producto]
        precio_promedio_publicado = sum(precios_publicados) / len(precios_publicados) if precios_publicados else Decimal('0')
        
        # Precio promedio vendido
        precio_promedio_vendido = ventas_producto['Precio Venta Unitario'].mean()
        
        analisis_producto.append({
            'SKU': sku,
            'Precio Normal TU': float(precio_normal),
            'Precio Promedio Publicado': float(precio_promedio_publicado),
            'Precio Promedio Vendido': float(precio_promedio_vendido),
            'Diferencia Publicado vs Vendido': float(precio_promedio_publicado) - float(precio_promedio_vendido),
            'Veces Publicado': len(pubs_producto),
            'Unidades Vendidas': int(ventas_producto['Cantidad Unitarias'].sum()),
            'Facturación Total (USD)': float(ventas_producto['Total Item con IVA'].sum()),
        })
    
    df_producto = pd.DataFrame(analisis_producto)
    if len(df_producto) > 0 and 'Facturación Total (USD)' in df_producto.columns:
        df_producto = df_producto.sort_values('Facturación Total (USD)', ascending=False)
    df_producto.to_excel(writer, sheet_name='04_Análisis por Producto', index=False)
    auto_adjust_column_widths(writer, '04_Análisis por Producto', df_producto)
    print(f"   ✅ {len(analisis_producto)} productos analizados")
    
    # 5. Análisis de mix de productos por período
    print("📊 Analizando mix de productos por período...")
    
    mix_periodos = []
    productos_totales_vistos = set()
    
    for periodo in periodos_info:
        productos_periodo = [p['sku'] for p in publicaciones_data 
                            if p.get('periodo') == periodo['nombre_periodo']]
        
        productos_nuevos = set(productos_periodo) - productos_totales_vistos
        productos_repetidos = set(productos_periodo) & productos_totales_vistos
        
        mix_periodos.append({
            'Período': periodo['nombre_periodo'],
            'Fecha Inicio': periodo['fecha_inicio'].strftime('%Y-%m-%d') if periodo['fecha_inicio'] else '',
            'Fecha Fin': periodo['fecha_fin'].strftime('%Y-%m-%d') if periodo['fecha_fin'] else '',
            'Total Productos Publicados': len(productos_periodo),
            'Productos Nuevos': len(productos_nuevos),
            'Productos Repetidos': len(productos_repetidos),
            '% Productos Nuevos': float(len(productos_nuevos) / len(productos_periodo) * 100) if productos_periodo else 0,
        })
        
        productos_totales_vistos.update(productos_periodo)
    
    df_mix = pd.DataFrame(mix_periodos)
    df_mix.to_excel(writer, sheet_name='05_Mix Productos por Período', index=False)
    auto_adjust_column_widths(writer, '05_Mix Productos por Período', df_mix)
    print(f"   ✅ {len(mix_periodos)} períodos analizados")
    
    # 6. Comparación 2024 vs 2025 (publicaciones semanales se dejaron a fines de 2025)
    print("📊 Comparando 2024 vs 2025...")
    
    # 2024: todo el año
    publicaciones_2024 = [p for p in publicaciones_data if p.get('fecha_inicio') and p['fecha_inicio'].year == 2024]
    
    # 2025: hasta fines de 2025 (cuando se dejaron las publicaciones semanales)
    # Asumimos que se dejaron en diciembre 2025
    publicaciones_2025 = [p for p in publicaciones_data 
                         if p.get('fecha_inicio') and 
                         p['fecha_inicio'].year == 2025 and 
                         p['fecha_inicio'] <= date(2025, 12, 31)]
    
    # Verificar si hay datos y fecha es datetime
    if len(ventas_df) == 0 or 'Fecha Creación' not in ventas_df.columns:
        ventas_2024 = pd.DataFrame()
        ventas_2025 = pd.DataFrame()
    else:
        # Asegurar que Fecha Creación sea datetime
        if not pd.api.types.is_datetime64_any_dtype(ventas_df['Fecha Creación']):
            ventas_df['Fecha Creación'] = pd.to_datetime(ventas_df['Fecha Creación'], errors='coerce')
        
        ventas_2024 = ventas_df[ventas_df['Fecha Creación'].dt.year == 2024]
        ventas_2025 = ventas_df[
            (ventas_df['Fecha Creación'].dt.year == 2025) &
            (ventas_df['Fecha Creación'] <= pd.Timestamp('2025-12-31'))
        ]
    
    periodos_2024 = [p for p in periodos_info if p.get('fecha_inicio') and p['fecha_inicio'].year == 2024]
    periodos_2025 = [p for p in periodos_info 
                    if p.get('fecha_inicio') and 
                    p['fecha_inicio'].year == 2025 and 
                    p['fecha_inicio'] <= date(2025, 12, 31)]
    
    # Calcular métricas de ventas (manejar DataFrames vacíos)
    ventas_2024_total = float(ventas_2024['Total Item con IVA'].sum()) if len(ventas_2024) > 0 and 'Total Item con IVA' in ventas_2024.columns else 0
    ventas_2025_total = float(ventas_2025['Total Item con IVA'].sum()) if len(ventas_2025) > 0 and 'Total Item con IVA' in ventas_2025.columns else 0
    unidades_2024 = int(ventas_2024['Cantidad Unitarias'].sum()) if len(ventas_2024) > 0 and 'Cantidad Unitarias' in ventas_2024.columns else 0
    unidades_2025 = int(ventas_2025['Cantidad Unitarias'].sum()) if len(ventas_2025) > 0 and 'Cantidad Unitarias' in ventas_2025.columns else 0
    ordenes_2024 = int(ventas_2024['Número de Orden'].nunique()) if len(ventas_2024) > 0 and 'Número de Orden' in ventas_2024.columns else 0
    ordenes_2025 = int(ventas_2025['Número de Orden'].nunique()) if len(ventas_2025) > 0 and 'Número de Orden' in ventas_2025.columns else 0
    
    comparacion = {
        'Período': ['2024', '2025'],
        'Productos Únicos Publicados': [
            len(set([p['sku'] for p in publicaciones_2024])),
            len(set([p['sku'] for p in publicaciones_2025])),
        ],
        'Total Publicaciones': [len(publicaciones_2024), len(publicaciones_2025)],
        'Promedio Productos por Período': [
            len(publicaciones_2024) / max(1, len(periodos_2024)),
            len(publicaciones_2025) / max(1, len(periodos_2025)),
        ],
        'Total Ventas (USD)': [ventas_2024_total, ventas_2025_total],
        'Unidades Vendidas': [unidades_2024, unidades_2025],
        'Órdenes Totales': [ordenes_2024, ordenes_2025],
    }
    
    df_comparacion = pd.DataFrame(comparacion)
    df_comparacion.to_excel(writer, sheet_name='06_Comparación 2024 vs 2025', index=False)
    auto_adjust_column_widths(writer, '06_Comparación 2024 vs 2025', df_comparacion)
    print(f"   ✅ Comparación 2024 vs 2025 generada")
    
    # 7. Análisis de stock actual de productos publicados
    print("📊 Analizando stock actual de productos publicados...")
    
    # Cargar stock
    try:
        stock_df = pd.read_csv(STOCK_ERP, encoding='utf-8-sig')
        stock_df['Pronosticado con pendiente'] = pd.to_numeric(
            stock_df['Pronosticado con pendiente'].astype(str).str.replace(',', '.'), errors='coerce'
        )
        stock_df['Box Qty'] = pd.to_numeric(
            stock_df['Box Qty'].astype(str).str.replace(',', '.'), errors='coerce'
        )
        
        # Cargar catálogo para mapear D365 a SKU
        catalogo_df = pd.read_csv(CATALOGO_TU, encoding='utf-8-sig')
        d365_to_sku = dict(zip(catalogo_df['Código de Producto (D365)'], catalogo_df['sku']))
        
        stock_por_sku = {}
        for _, row in stock_df.iterrows():
            d365_ref = str(row.get('D365 Reference', '')).strip()
            sku = d365_to_sku.get(d365_ref, '').upper() if d365_ref in d365_to_sku else ''
            if sku:
                stock_cajas = row.get('Pronosticado con pendiente', 0)
                box_qty = row.get('Box Qty', 1)
                stock_unidades = stock_cajas * box_qty
                stock_por_sku[sku] = {
                    'stock_cajas': stock_cajas,
                    'stock_unidades': stock_unidades,
                }
        
        # Analizar productos publicados con stock
        productos_publicados_sku = set([p['sku'] for p in publicaciones_data])
        analisis_stock = []
        
        for sku in productos_publicados_sku:
            stock_info = stock_por_sku.get(sku, {})
            if stock_info and stock_info.get('stock_unidades', 0) > 0:
                # Última publicación
                pubs_sku = [p for p in publicaciones_data if p['sku'] == sku]
                ultima_pub = max(pubs_sku, key=lambda x: x.get('fecha_inicio') or date(1900, 1, 1)) if pubs_sku else None
                
                ceg_info = ceg_prices.get(sku, {})
                
                analisis_stock.append({
                    'SKU': sku,
                    'Stock Cajas': float(stock_info.get('stock_cajas', 0)),
                    'Stock Unidades': float(stock_info.get('stock_unidades', 0)),
                    'Última Publicación': ultima_pub['periodo'] if ultima_pub else '',
                    'Fecha Última Pub': ultima_pub['fecha_inicio'].strftime('%Y-%m-%d') if ultima_pub and ultima_pub.get('fecha_inicio') else '',
                    'Precio Normal TU': float(ceg_info.get('precio_normal_tu', 0)),
                    'FOB': float(ceg_info.get('fob', 0)),
                    'Veces Publicado': len(pubs_sku),
                })
        
        df_stock = pd.DataFrame(analisis_stock)
        df_stock = df_stock.sort_values('Stock Unidades', ascending=False)
        df_stock.to_excel(writer, sheet_name='07_Stock Actual Publicados', index=False)
        auto_adjust_column_widths(writer, '07_Stock Actual Publicados', df_stock)
        print(f"   ✅ {len(analisis_stock)} productos con stock analizados")
    except Exception as e:
        print(f"   ⚠️  No se pudo cargar stock: {e}")


def generate_commercial_intelligence():
    """Genera análisis completo de inteligencia comercial."""
    print("🔄 Generando Análisis de Inteligencia Comercial...")
    
    # Cargar datos
    ceg_prices = load_ceg_prices()
    publicaciones_data, periodos_info = load_publicaciones()
    ventas_df = load_ventas()
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Crear Excel
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        analyze_pricing_impact(publicaciones_data, ceg_prices, ventas_df, periodos_info, writer)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    print(f"\n📋 Hojas creadas:")
    print(f"   01. Pricing Publicaciones (precios publicados vs normal)")
    print(f"   02. Impacto Ventas por Período")
    print(f"   03. Resumen Precio vs Descuento")
    print(f"   04. Análisis por Producto")
    print(f"   05. Mix Productos por Período")
    print(f"   06. Comparación 2024 vs 2025")
    print(f"   07. Stock Actual Publicados")


if __name__ == "__main__":
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("Instalando dependencias...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    generate_commercial_intelligence()
    print("\n✨ Proceso completado!")
