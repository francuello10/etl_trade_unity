#!/usr/bin/env python3
"""
MEGA EXCEL COMPLETO: Todas las hojas de Ventas + Inventario + Análisis Avanzado - Trade Unity

Alineado con documento base Trade Unity:
- Ecommerce B2B mayorista del grupo CEG
- Integración Magento + Odoo para operación end-to-end
- Analítica accionable: LTV, recencia/frecuencia, clusters, top productos
- Principios: Datos como sistema nervioso, automatización con control

Incluye:
- Resumen ejecutivo mejorado con métricas trimestrales desde 2024
- Análisis de ventas por cliente, producto, marca, categoría
- Análisis de inventario y stock
- Márgenes FOB y Plataforma
- Sugerencias DATA NINJA basadas en stock y ventas
"""

import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime, date
import statistics

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Archivos
VENTAS_CSV = "inputs/ventas_historicas_items_FINAL.csv"  # Fuente: Ventas.xlsx hoja 01_Ventas
STOCK_ERP = "fuentes/stock erp.csv"
CATALOGO_TU = "fuentes/Catalogo TU.csv"
OUTPUT_DIR = "outputs"
OUTPUT_EXCEL = f"{OUTPUT_DIR}/TradeUnity Sales Inventory Analysis.xlsx"


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


def parse_date(date_str: str):
    """Parsea fecha."""
    if not date_str or date_str == "":
        return None
    
    date_str = str(date_str).strip()
    
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%d-%m']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None


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


def get_quarter(date_obj: date) -> str:
    """Obtiene trimestre de una fecha."""
    if not date_obj:
        return ""
    quarter = (date_obj.month - 1) // 3 + 1
    return f"Q{quarter}"


def days_between(date1, date2):
    """Calcula días entre dos fechas."""
    if not date1 or not date2:
        return None
    
    if isinstance(date1, str):
        date1 = parse_date(date1)
    if isinstance(date2, str):
        date2 = parse_date(date2)
    
    if not date1 or not date2:
        return None
    
    return (date2 - date1).days


def calculate_purchase_probability(cliente_data, hoy):
    """Calcula probabilidad de compra."""
    if not cliente_data['compras']:
        return Decimal('0')
    
    compras = cliente_data['compras']
    num_compras = len(compras)
    
    if num_compras == 0:
        return Decimal('0')
    
    fechas_validas = [c['fecha'] for c in compras if c['fecha']]
    if fechas_validas:
        ultima_compra = max(fechas_validas)
        dias_desde_ultima = days_between(ultima_compra, hoy)
        if dias_desde_ultima is None:
            dias_desde_ultima = 999
    else:
        ultima_compra = None
        dias_desde_ultima = 999
    
    fechas_ordenadas = sorted(fechas_validas) if fechas_validas else []
    if len(fechas_ordenadas) > 1:
        intervalos = []
        for i in range(1, len(fechas_ordenadas)):
            intervalo = days_between(fechas_ordenadas[i-1], fechas_ordenadas[i])
            if intervalo and intervalo > 0:
                intervalos.append(intervalo)
        
        if intervalos:
            frecuencia_promedio = sum(intervalos) / len(intervalos)
        else:
            frecuencia_promedio = 180
    else:
        frecuencia_promedio = 180
    
    factor_frecuencia = min(num_compras / 10, 1.0)
    
    if frecuencia_promedio > 0:
        factor_tiempo = max(0, 1 - (abs(dias_desde_ultima - frecuencia_promedio) / frecuencia_promedio))
        factor_tiempo = min(factor_tiempo, 1.0)
    else:
        factor_tiempo = 0.5
    
    if dias_desde_ultima <= 30:
        factor_recencia = 1.0
    elif dias_desde_ultima <= 60:
        factor_recencia = 0.8
    elif dias_desde_ultima <= 90:
        factor_recencia = 0.6
    elif dias_desde_ultima <= 180:
        factor_recencia = 0.4
    else:
        factor_recencia = 0.2
    
    probabilidad = (
        factor_frecuencia * 0.3 +
        factor_tiempo * 0.3 +
        factor_recencia * 0.4
    )
    
    return Decimal(str(probabilidad))


def load_catalog():
    """Carga catálogo TU."""
    print("📖 Cargando catálogo TU...")
    
    catalog = {}
    
    with open(CATALOGO_TU, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = str(row.get('sku', '')).strip().upper()
            d365_ref = str(row.get('Código de Producto (D365)', '')).strip()
            
            if not sku:
                continue
            
            catalog[sku] = {
                'd365_reference': d365_ref,
                'nombre': str(row.get('Nombre del Producto', '')).strip(),
                'marca': str(row.get('Marca', '')).strip(),
                'categoria_2': str(row.get('Categoría (2° Nivel)', '')).strip(),
                'cantidad_paquete': parse_decimal(row.get('Cantidad por Paquete Comercial', '')),
                'fob_unitario': parse_decimal(row.get('Costo FOB (Unitario)', '')),
                'precio_plataforma_unitario': parse_decimal(row.get('Precio Plataforma (Unitario) – CEG', '')),
                'volumen_box': parse_decimal(row.get('Volumen (box)', '')),
            }
    
    print(f"   ✅ {len(catalog)} productos en catálogo")
    return catalog


def load_stock():
    """Carga stock del ERP."""
    print("📖 Cargando stock del ERP...")
    
    stock_data = {}
    
    with open(STOCK_ERP, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d365_ref = str(row.get('D365 Reference', '')).strip()
            stock_cajas = parse_decimal(row.get('Pronosticado con pendiente', ''))
            box_qty = parse_decimal(row.get('Box Qty', ''))
            volumen = parse_decimal(row.get('Volumen', ''))
            
            if not d365_ref or stock_cajas == 0:
                continue
            
            stock_data[d365_ref] = {
                'stock_cajas': stock_cajas,
                'box_qty': box_qty,
                'volumen': volumen,
                'nombre_erp': str(row.get('Nombre', '')).strip(),
            }
    
    print(f"   ✅ {len(stock_data)} productos con stock")
    return stock_data


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
    
    # Convertir columnas numéricas
    numeric_cols = [
        'Cantidad', 'Cantidad Unitarias', 'Cantidad por Paquete Comercial',
        'Precio Original', 'Precio Venta', 'Precio Original Unitario', 
        'Precio Venta Unitario', 'FOB CEG', 'Base Price CEG',
        'Margen sobre FOB', '% Margen sobre FOB', 
        'Margen sobre Plataforma', '% Margen sobre Plataforma',
        'Total Item', 'Total Item con IVA', 'Total Orden', 'Subtotal Orden', 'Volumen del Item',
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    print(f"   ✅ {len(df)} filas cargadas")
    return df


def create_enhanced_summary_sheet(df, writer):
    """Crea resumen ejecutivo mejorado con métricas trimestrales desde 2024."""
    print("📊 Creando Resumen Ejecutivo Mejorado...")
    
    # Si no hay datos, crear resumen básico
    if len(df) == 0:
        summary_data = {
            'Métrica': ['Estado', 'Mensaje', 'Acción Requerida', '', 'NOTA IMPORTANTE - Precios', '', ''],
            'Valor': [
                'Sin datos de ventas',
                'No se encontraron datos de ventas históricas',
                'Ejecutar: python3 scripts/export_ventas_tradeunity.py',
                '',
                'Los precios Plataforma CEG (mejor escala) y FOB utilizados corresponden a precios actualizados al 18.02.2026.',
                'Estos precios tienden a la baja en muchos casos, lo cual puede explicar parcialmente los márgenes negativos observados.',
                'Queda pendiente el cruce con los costos históricos reales al momento de cada venta para un análisis más preciso.'
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='00_Resumen Ejecutivo', index=False)
        auto_adjust_column_widths(writer, '00_Resumen Ejecutivo', summary_df)
        return
    
    # Filtrar desde 2024
    if 'Fecha Creación' in df.columns:
        df['Fecha Creación'] = pd.to_datetime(df['Fecha Creación'], errors='coerce')
        df['Año'] = df['Fecha Creación'].dt.year
        df['Mes'] = df['Fecha Creación'].dt.month
        df['Trimestre'] = df['Mes'].apply(lambda x: f"Q{(x-1)//3 + 1}")
        df['Año-Trimestre'] = df['Año'].astype(str) + '-' + df['Trimestre']
    
    df_2024 = df[df['Año'] >= 2024].copy()
    
    # Calcular métricas totales desde 2024
    total_ordenes = df_2024['Número de Orden'].nunique()
    total_items = len(df_2024)
    total_unidades = df_2024['Cantidad Unitarias'].sum()
    total_facturado = df_2024['Total Item'].sum()
    total_facturado_iva = df_2024['Total Item con IVA'].sum()
    clientes_unicos = df_2024['Email Cliente'].nunique()
    productos_unicos = df_2024['SKU'].nunique()
    marcas_unicas = df_2024['Brand Name CEG'].nunique()
    categorias_unicas = df_2024['Categoría (2° Nivel)'].nunique()
    margen_prom_fob = df_2024['% Margen sobre FOB'].mean()
    margen_prom_plataforma = df_2024['% Margen sobre Plataforma'].mean()
    volumen_total = df_2024['Volumen del Item'].sum()
    
    # Convertir Total Orden para cálculos
    if 'Total Orden' in df_2024.columns:
        df_2024['Total Orden'] = df_2024['Total Orden'].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
        df_2024['Total Orden'] = pd.to_numeric(df_2024['Total Orden'], errors='coerce').fillna(0)
    
    # Calcular promedio de orden usando Total Orden (valor completo de la orden)
    # NOTA: Si Looker/Odoo muestra valores diferentes, puede ser porque:
    # 1. Usa GMV (Gross Merchandise Value) en lugar de Total Orden
    # 2. Filtra por estados diferentes (sale, draft, sent vs Entregado)
    # 3. Tiene datos más actualizados que el CSV
    # Usamos .first() porque Total Orden es el mismo para todos los items de una orden
    if 'Total Orden' in df_2024.columns:
        # Convertir Total Orden si no está convertido
        if df_2024['Total Orden'].dtype == 'object':
            df_2024['Total Orden'] = df_2024['Total Orden'].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
            df_2024['Total Orden'] = pd.to_numeric(df_2024['Total Orden'], errors='coerce').fillna(0)
        
        if df_2024['Total Orden'].sum() > 0:
            ordenes_totales = df_2024.groupby('Número de Orden')['Total Orden'].first()
        else:
            # Fallback: sumar Total Item con IVA si Total Orden está vacío
            ordenes_totales = df_2024.groupby('Número de Orden')['Total Item con IVA'].sum()
    else:
        # Fallback: sumar Total Item con IVA si Total Orden no está disponible
        ordenes_totales = df_2024.groupby('Número de Orden')['Total Item con IVA'].sum()
    
    promedio_orden = ordenes_totales.mean()
    
    # Calcular mediana de ventas (por orden)
    mediana_ventas = ordenes_totales.median()
    
    # SKUs promedio por orden
    skus_por_orden = df_2024.groupby('Número de Orden')['SKU'].nunique()
    skus_promedio_por_orden = skus_por_orden.mean()
    
    # Precio promedio SKU vendido
    precio_promedio_sku = df_2024['Precio Venta Unitario'].mean()
    
    # Clientes únicos que compraron (ya calculado arriba)
    
    # Nuevos clientes por trimestre (clientes que compraron por primera vez en ese trimestre)
    clientes_por_trimestre = {}
    clientes_anteriores = set()
    
    for trimestre in sorted(df_2024['Año-Trimestre'].unique()):
        df_trim = df_2024[df_2024['Año-Trimestre'] == trimestre]
        clientes_trim = set(df_trim['Email Cliente'].unique())
        nuevos_clientes = clientes_trim - clientes_anteriores
        clientes_por_trimestre[trimestre] = len(nuevos_clientes)
        clientes_anteriores.update(clientes_trim)
    
    # Calcular métricas por trimestre
    trimestres = sorted(df_2024['Año-Trimestre'].unique())
    
    summary_rows = []
    
    # Métricas totales
    metricas = [
        ('Total Órdenes', total_ordenes, 'int'),
        ('Total Items Vendidos', total_items, 'int'),
        ('Total Unidades Vendidas', total_unidades, 'int'),
        ('Total Facturado (USD)', total_facturado, 'float'),
        ('Total Facturado con IVA (USD)', total_facturado_iva, 'float'),
        ('Clientes Únicos', clientes_unicos, 'int'),
        ('Productos Únicos Vendidos', productos_unicos, 'int'),
        ('Marcas Únicas', marcas_unicas, 'int'),
        ('Categorías Únicas', categorias_unicas, 'int'),
        ('Margen Promedio sobre FOB (%)', margen_prom_fob, 'float'),
        ('Margen Promedio sobre Plataforma (%)', margen_prom_plataforma, 'float'),
        ('Volumen Total (m³)', volumen_total, 'float'),
        ('Promedio de Orden (USD)', promedio_orden, 'float'),
        ('Mediana de Ventas (USD)', mediana_ventas, 'float'),
        ('SKUs Promedio por Orden', skus_promedio_por_orden, 'float'),
        ('Precio Promedio SKU Vendido (USD)', precio_promedio_sku, 'float'),
        ('Clientes Únicos que Compraron', clientes_unicos, 'int'),
    ]
    
    for metrica, valor_total, tipo in metricas:
        row = {'Métrica': metrica, 'Total': valor_total}
        
        # Agregar valores por trimestre
        for trim in trimestres:
            df_trim = df_2024[df_2024['Año-Trimestre'] == trim]
            
            if metrica == 'Total Órdenes':
                valor = df_trim['Número de Orden'].nunique()
            elif metrica == 'Total Items Vendidos':
                valor = len(df_trim)
            elif metrica == 'Total Unidades Vendidas':
                valor = df_trim['Cantidad Unitarias'].sum()
            elif metrica == 'Total Facturado (USD)':
                valor = df_trim['Total Item'].sum()
            elif metrica == 'Total Facturado con IVA (USD)':
                valor = df_trim['Total Item con IVA'].sum()
            elif metrica == 'Clientes Únicos':
                valor = df_trim['Email Cliente'].nunique()
            elif metrica == 'Productos Únicos Vendidos':
                valor = df_trim['SKU'].nunique()
            elif metrica == 'Marcas Únicas':
                valor = df_trim['Brand Name CEG'].nunique()
            elif metrica == 'Categorías Únicas':
                valor = df_trim['Categoría (2° Nivel)'].nunique()
            elif metrica == 'Margen Promedio sobre FOB (%)':
                valor = df_trim['% Margen sobre FOB'].mean()
            elif metrica == 'Margen Promedio sobre Plataforma (%)':
                valor = df_trim['% Margen sobre Plataforma'].mean()
            elif metrica == 'Volumen Total (m³)':
                valor = df_trim['Volumen del Item'].sum()
            elif metrica == 'Promedio de Orden (USD)':
                # Usar Total Orden si está disponible, sino sumar Total Item con IVA
                if 'Total Orden' in df_trim.columns:
                    df_trim['Total Orden'] = df_trim['Total Orden'].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
                    df_trim['Total Orden'] = pd.to_numeric(df_trim['Total Orden'], errors='coerce').fillna(0)
                    if df_trim['Total Orden'].sum() > 0:
                        ordenes_trim = df_trim.groupby('Número de Orden')['Total Orden'].first()
                    else:
                        ordenes_trim = df_trim.groupby('Número de Orden')['Total Item con IVA'].sum()
                else:
                    ordenes_trim = df_trim.groupby('Número de Orden')['Total Item con IVA'].sum()
                valor = ordenes_trim.mean() if len(ordenes_trim) > 0 else 0
            elif metrica == 'Mediana de Ventas (USD)':
                # Usar Total Orden si está disponible, sino sumar Total Item con IVA
                if 'Total Orden' in df_trim.columns:
                    df_trim['Total Orden'] = df_trim['Total Orden'].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
                    df_trim['Total Orden'] = pd.to_numeric(df_trim['Total Orden'], errors='coerce').fillna(0)
                    if df_trim['Total Orden'].sum() > 0:
                        ordenes_trim = df_trim.groupby('Número de Orden')['Total Orden'].first()
                    else:
                        ordenes_trim = df_trim.groupby('Número de Orden')['Total Item con IVA'].sum()
                else:
                    ordenes_trim = df_trim.groupby('Número de Orden')['Total Item con IVA'].sum()
                valor = ordenes_trim.median() if len(ordenes_trim) > 0 else 0
            elif metrica == 'SKUs Promedio por Orden':
                skus_trim = df_trim.groupby('Número de Orden')['SKU'].nunique()
                valor = skus_trim.mean() if len(skus_trim) > 0 else 0
            elif metrica == 'Precio Promedio SKU Vendido (USD)':
                valor = df_trim['Precio Venta Unitario'].mean()
            elif metrica == 'Clientes Únicos que Compraron':
                valor = df_trim['Email Cliente'].nunique()
            else:
                valor = 0
            
            if tipo == 'int':
                row[trim] = int(valor) if not pd.isna(valor) else 0
            else:
                row[trim] = round(float(valor), 2) if not pd.isna(valor) else 0
        
        summary_rows.append(row)
    
    # Agregar métrica de nuevos clientes
    nuevos_clientes_row = {'Métrica': 'Nuevos Clientes que Compraron', 'Total': sum(clientes_por_trimestre.values())}
    for trim in trimestres:
        nuevos_clientes_row[trim] = clientes_por_trimestre.get(trim, 0)
    summary_rows.append(nuevos_clientes_row)
    
    # Crear DataFrame
    columns = ['Métrica', 'Total'] + trimestres
    
    df_summary = pd.DataFrame(summary_rows)
    df_summary = df_summary[columns]
    
    # Agregar nota importante sobre precios
    nota_precios = pd.DataFrame({
        'Métrica': ['', '', '⚠️ NOTA IMPORTANTE - Precios', '', ''],
        'Total': ['', '', 'Los precios Plataforma CEG (mejor escala) y FOB corresponden a precios actualizados al 18.02.2026.', 'Estos precios tienden a la baja en muchos casos, lo cual puede explicar parcialmente los márgenes negativos observados.', 'Queda pendiente el cruce con los costos históricos reales al momento de cada venta para un análisis más preciso.']
    })
    for col in trimestres:
        nota_precios[col] = ''
    
    df_summary = pd.concat([df_summary, nota_precios], ignore_index=True)
    
    df_summary.to_excel(writer, sheet_name='00_Resumen Ejecutivo', index=False)
    auto_adjust_column_widths(writer, '00_Resumen Ejecutivo', df_summary)
    
    worksheet = writer.sheets['00_Resumen Ejecutivo']
    worksheet.column_dimensions['A'].width = 40
    for col in range(2, len(columns) + 1):
        worksheet.column_dimensions[chr(64 + col)].width = 15


# Importar funciones de los otros scripts (simplificadas)
def create_ventas_sheet(df, writer):
    """Crea hoja con todas las ventas originales."""
    print("📊 Creando hoja de Ventas...")
    df_ventas = df.sort_values(['Número de Orden', 'Fecha Creación'])
    df_ventas.to_excel(writer, sheet_name='01_Ventas', index=False)
    auto_adjust_column_widths(writer, '01_Ventas', df_ventas)


def create_cliente_producto_sheet(df, writer):
    """Crea hoja de análisis desglosado por Cliente y Producto."""
    print("📊 Creando análisis Cliente-Producto...")
    
    cliente_producto = df.groupby(['Email Cliente', 'SKU']).agg({
        'Nombre Cliente': 'first',
        'Apellido Cliente': 'first',
        'CUIT Cliente': 'first',
        'Nombre Producto': 'first',
        'Brand Name CEG': 'first',
        'Categoría (2° Nivel)': 'first',
        'Categoría CEG': 'first',
        'Número de Orden': 'nunique',
        'Cantidad': 'sum',
        'Cantidad Unitarias': 'sum',
        'Precio Venta Unitario': ['mean', 'max', 'min'],
        'Precio Venta': 'mean',
        'FOB CEG': 'first',
        'Base Price CEG': 'first',
        'Total Item': 'sum',
        'Total Item con IVA': 'sum',
        'Volumen del Item': 'sum',
        'Fecha Creación': ['min', 'max'],
    }).reset_index()
    
    cliente_producto.columns = [
        'Email Cliente', 'SKU', 'Nombre Cliente', 'Apellido Cliente', 'CUIT Cliente',
        'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
        'Número de Órdenes', 'Cantidad Cajas Total', 'Cantidad Unidades Total',
        'Precio Unitario Promedio', 'Precio Unitario Máximo', 'Precio Unitario Mínimo',
        'Precio Caja Promedio', 'FOB Unitario', 'Precio Plataforma Unitario',
        'Total Facturado (USD)', 'Total Facturado con IVA (USD)', 'Volumen Total (m³)',
        'Primera Compra', 'Última Compra'
    ]
    
    cliente_producto['Diferencia vs FOB'] = (
        cliente_producto['Precio Unitario Promedio'] - cliente_producto['FOB Unitario']
    )
    cliente_producto['% Diferencia vs FOB'] = (
        (cliente_producto['Diferencia vs FOB'] / cliente_producto['FOB Unitario'] * 100)
        .replace([float('inf'), -float('inf')], 0)
        .fillna(0)
    )
    
    cliente_producto['Diferencia vs Plataforma'] = (
        cliente_producto['Precio Unitario Promedio'] - cliente_producto['Precio Plataforma Unitario']
    )
    cliente_producto['% Diferencia vs Plataforma'] = (
        (cliente_producto['Diferencia vs Plataforma'] / cliente_producto['Precio Plataforma Unitario'] * 100)
        .replace([float('inf'), -float('inf')], 0)
        .fillna(0)
    )
    
    cliente_producto = cliente_producto.sort_values(
        ['Email Cliente', 'Total Facturado con IVA (USD)'], 
        ascending=[True, False]
    )
    
    cliente_producto.to_excel(writer, sheet_name='02_Cliente Producto', index=False)
    auto_adjust_column_widths(writer, '02_Cliente Producto', cliente_producto)


def create_sku_clientes_potenciales(df, stock_data, catalog, writer):
    """Crea hoja de análisis por SKU con clientes potenciales."""
    print("📊 Creando análisis SKU - Clientes Potenciales...")
    
    hoy = datetime.now().date()
    
    # Convertir DataFrame a lista de diccionarios para procesamiento
    ventas_data = df.to_dict('records')
    
    # Agrupar ventas por SKU y cliente
    sku_clientes = defaultdict(lambda: defaultdict(lambda: {
        'compras': [],
        'total_unidades': Decimal('0'),
        'total_facturado': Decimal('0'),
        'precio_promedio': Decimal('0'),
        'nombre': '',
        'apellido': '',
        'cuit': '',
    }))
    
    for row in ventas_data:
        sku = str(row.get('SKU', '')).strip().upper()
        email = str(row.get('Email Cliente', '')).strip()
        
        if not sku or not email:
            continue
        
        fecha_str = str(row.get('Fecha Creación', ''))
        fecha = parse_date(fecha_str)
        cantidad_unidades = Decimal(str(row.get('Cantidad Unitarias', 0)))
        precio_unitario = Decimal(str(row.get('Precio Venta Unitario', 0)))
        total_item = Decimal(str(row.get('Total Item con IVA', 0)))
        
        if not sku_clientes[sku][email]['nombre']:
            sku_clientes[sku][email]['nombre'] = str(row.get('Nombre Cliente', '')).strip()
            sku_clientes[sku][email]['apellido'] = str(row.get('Apellido Cliente', '')).strip()
            sku_clientes[sku][email]['cuit'] = str(row.get('CUIT Cliente', '')).strip()
        
        sku_clientes[sku][email]['compras'].append({
            'fecha': fecha,
            'cantidad_unidades': cantidad_unidades,
            'precio_unitario': precio_unitario,
            'total_item': total_item,
        })
        
        sku_clientes[sku][email]['total_unidades'] += cantidad_unidades
        sku_clientes[sku][email]['total_facturado'] += total_item
    
    # Calcular promedios
    for sku in sku_clientes:
        for email in sku_clientes[sku]:
            cliente_data = sku_clientes[sku][email]
            if cliente_data['compras']:
                precios = [c['precio_unitario'] for c in cliente_data['compras'] if c['precio_unitario'] > 0]
                if precios:
                    cliente_data['precio_promedio'] = sum(precios) / len(precios)
    
    # Crear datos para la hoja
    resultados = []
    skus_con_stock = set()
    
    for d365_ref, stock_info in stock_data.items():
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                skus_con_stock.add(sku)
                break
    
    for sku in sorted(skus_con_stock):
        if sku not in sku_clientes:
            continue
        
        cat_info = catalog.get(sku, {})
        d365_ref = cat_info.get('d365_reference', '')
        stock_info = stock_data.get(d365_ref, {})
        
        stock_cajas = Decimal(str(stock_info.get('stock_cajas', 0)))
        box_qty = Decimal(str(stock_info.get('box_qty', 1)))
        stock_unidades = stock_cajas * box_qty
        
        for email, cliente_data in sku_clientes[sku].items():
            probabilidad = calculate_purchase_probability(cliente_data, hoy)
            cantidad_esperada = cliente_data['total_unidades'] / len(cliente_data['compras']) if cliente_data['compras'] else Decimal('0')
            stock_restante = stock_unidades - (cantidad_esperada * probabilidad)
            
            ultima_compra_info = max(
                cliente_data['compras'],
                key=lambda x: x['fecha'] if x['fecha'] else datetime(1900, 1, 1).date()
            )
            ultima_fecha = ultima_compra_info['fecha']
            dias_desde_ultima = days_between(ultima_fecha, hoy) if ultima_fecha else None
            
            fob_unitario = cat_info.get('fob_unitario', Decimal('0'))
            precio_plataforma = cat_info.get('precio_plataforma_unitario', Decimal('0'))
            precio_promedio = cliente_data['precio_promedio']
            
            resultados.append({
                'SKU': sku,
                'Nombre Producto': cat_info.get('nombre', ''),
                'Marca': cat_info.get('marca', ''),
                'Categoría': cat_info.get('categoria_2', ''),
                'Stock Cajas': float(stock_cajas),
                'Stock Unidades': float(stock_unidades),
                'Email Cliente': email,
                'Nombre Cliente': cliente_data.get('nombre', ''),
                'Apellido Cliente': cliente_data.get('apellido', ''),
                'CUIT Cliente': cliente_data.get('cuit', ''),
                'Número de Compras': len(cliente_data['compras']),
                'Total Unidades Compradas Históricas': float(cliente_data['total_unidades']),
                'Cantidad Promedio por Compra': float(cantidad_esperada),
                'Última Compra': ultima_fecha.strftime('%Y-%m-%d') if ultima_fecha else '',
                'Días desde Última Compra': dias_desde_ultima if dias_desde_ultima is not None else '',
                'Precio Promedio Pagado': float(precio_promedio),
                'FOB Unitario': float(fob_unitario),
                'Precio Plataforma Unitario': float(precio_plataforma),
                'Total Facturado Histórico': float(cliente_data['total_facturado']),
                'Probabilidad de Compra (%)': float(probabilidad * 100),
                'Cantidad Esperada (Probabilística)': float(cantidad_esperada * probabilidad),
                'Stock Restante Esperado': float(stock_restante),
            })
    
    df_resultados = pd.DataFrame(resultados)
    if len(df_resultados) > 0:
        df_resultados = df_resultados.sort_values(
            ['SKU', 'Probabilidad de Compra (%)'],
            ascending=[True, False]
        )
        df_resultados.to_excel(writer, sheet_name='03_SKU Clientes Potenciales', index=False)
        auto_adjust_column_widths(writer, '03_SKU Clientes Potenciales', df_resultados)
        print(f"   ✅ {len(df_resultados)} registros creados")


# Continuar con más funciones de análisis...
def create_analisis_por_cliente_detallado(df, writer):
    """Crea hoja detallada de análisis por cliente."""
    print("📊 Creando análisis detallado por Cliente...")
    
    clientes_data = []
    
    for _, row in df.iterrows():
        clientes_data.append({
            'Email Cliente': row.get('Email Cliente', ''),
            'Nombre Cliente': row.get('Nombre Cliente', ''),
            'Apellido Cliente': row.get('Apellido Cliente', ''),
            'CUIT Cliente': row.get('CUIT Cliente', ''),
            'Número de Orden': row.get('Número de Orden', ''),
            'Fecha Creación': row.get('Fecha Creación', ''),
            'Estado': row.get('Estado', ''),
            'SKU': row.get('SKU', ''),
            'Nombre Producto': row.get('Nombre Producto', ''),
            'Marca': row.get('Brand Name CEG', ''),
            'Categoría (2° Nivel)': row.get('Categoría (2° Nivel)', ''),
            'Cantidad Cajas': row.get('Cantidad', 0),
            'Cantidad Unidades': row.get('Cantidad Unitarias', 0),
            'Precio Unitario Vendido': row.get('Precio Venta Unitario', 0),
            'FOB Unitario': row.get('FOB CEG', 0),
            'Precio Plataforma Unitario': row.get('Base Price CEG', 0),
            'Diferencia vs FOB': row.get('Precio Venta Unitario', 0) - row.get('FOB CEG', 0),
            '% Diferencia vs FOB': ((row.get('Precio Venta Unitario', 0) - row.get('FOB CEG', 0)) / row.get('FOB CEG', 1) * 100) if row.get('FOB CEG', 0) > 0 else 0,
            'Diferencia vs Plataforma': row.get('Precio Venta Unitario', 0) - row.get('Base Price CEG', 0),
            '% Diferencia vs Plataforma': ((row.get('Precio Venta Unitario', 0) - row.get('Base Price CEG', 0)) / row.get('Base Price CEG', 1) * 100) if row.get('Base Price CEG', 0) > 0 else 0,
            'Total Item (USD)': row.get('Total Item', 0),
            'Total Item con IVA (USD)': row.get('Total Item con IVA', 0),
        })
    
    df_clientes = pd.DataFrame(clientes_data)
    df_clientes = df_clientes.sort_values(['Email Cliente', 'Fecha Creación', 'Número de Orden'])
    df_clientes.to_excel(writer, sheet_name='04_Análisis por Cliente', index=False)
    auto_adjust_column_widths(writer, '04_Análisis por Cliente', df_clientes)
    
    # Resumen por cliente
    resumen_clientes = df.groupby('Email Cliente').agg({
        'Nombre Cliente': 'first',
        'Apellido Cliente': 'first',
        'CUIT Cliente': 'first',
        'Número de Orden': 'nunique',
        'SKU': 'nunique',
        'Cantidad': 'sum',
        'Cantidad Unitarias': 'sum',
        'Total Item': 'sum',
        'Total Item con IVA': 'sum',
        'Precio Venta Unitario': 'mean',
    }).reset_index()
    
    resumen_clientes.columns = [
        'Email Cliente', 'Nombre', 'Apellido', 'CUIT',
        'Órdenes', 'Productos Únicos', 'Cajas Totales', 'Unidades Totales',
        'Facturación Neta (USD)', 'Facturación con IVA (USD)', 'Precio Promedio Unitario'
    ]
    
    resumen_clientes = resumen_clientes.sort_values('Facturación con IVA (USD)', ascending=False)
    resumen_clientes.to_excel(writer, sheet_name='05_Resumen por Cliente', index=False)
    auto_adjust_column_widths(writer, '05_Resumen por Cliente', resumen_clientes)


def create_by_product_sheet(df, writer):
    """Crea hoja de análisis por producto."""
    print("📊 Creando análisis por Producto...")
    
    product_analysis = df.groupby('SKU').agg({
        'Nombre Producto': 'first',
        'Brand Name CEG': 'first',
        'Categoría (2° Nivel)': 'first',
        'Categoría CEG': 'first',
        'Cantidad': 'sum',
        'Cantidad Unitarias': 'sum',
        'Total Item': 'sum',
        'Total Item con IVA': 'sum',
        'Precio Venta Unitario': 'mean',
        'FOB CEG': 'first',
        'Base Price CEG': 'first',
        '% Margen sobre FOB': 'mean',
        '% Margen sobre Plataforma': 'mean',
        'Volumen del Item': 'sum',
    }).reset_index()
    
    product_analysis['Margen Absoluto FOB'] = (
        product_analysis['Precio Venta Unitario'] - product_analysis['FOB CEG']
    ) * product_analysis['Cantidad Unitarias']
    
    product_analysis['Margen Absoluto Plataforma'] = (
        product_analysis['Precio Venta Unitario'] - product_analysis['Base Price CEG']
    ) * product_analysis['Cantidad Unitarias']
    
    product_analysis = product_analysis.sort_values('Total Item con IVA', ascending=False)
    
    product_analysis.columns = [
        'SKU', 'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
        'Cantidad Cajas', 'Cantidad Unidades', 'Facturación Neta (USD)', 
        'Facturación con IVA (USD)', 'Precio Promedio Unitario', 'FOB Unitario',
        'Precio Plataforma Unitario', 'Margen % FOB', 'Margen % Plataforma',
        'Volumen Total (m³)', 'Margen Absoluto FOB', 'Margen Absoluto Plataforma'
    ]
    
    product_analysis.to_excel(writer, sheet_name='06_Por Producto', index=False)
    auto_adjust_column_widths(writer, '06_Por Producto', product_analysis)


def create_by_brand_sheet(df, writer):
    """Crea hoja de análisis por marca."""
    print("📊 Creando análisis por Marca...")
    
    brand_analysis = df.groupby('Brand Name CEG').agg({
        'SKU': 'nunique',
        'Cantidad': 'sum',
        'Cantidad Unitarias': 'sum',
        'Total Item': 'sum',
        'Total Item con IVA': 'sum',
        'Precio Venta Unitario': 'mean',
        '% Margen sobre FOB': 'mean',
        '% Margen sobre Plataforma': 'mean',
        'Volumen del Item': 'sum',
    }).reset_index()
    
    total_facturado = brand_analysis['Total Item con IVA'].sum()
    brand_analysis['Participación %'] = (
        brand_analysis['Total Item con IVA'] / total_facturado * 100
    )
    
    brand_analysis = brand_analysis.sort_values('Total Item con IVA', ascending=False)
    
    brand_analysis.columns = [
        'Marca', 'Productos Únicos', 'Cantidad Cajas', 'Cantidad Unidades',
        'Facturación Neta (USD)', 'Facturación con IVA (USD)', 
        'Precio Promedio Unitario', 'Margen % FOB', 'Margen % Plataforma',
        'Volumen Total (m³)', 'Participación %'
    ]
    
    brand_analysis.to_excel(writer, sheet_name='07_Por Marca', index=False)
    auto_adjust_column_widths(writer, '07_Por Marca', brand_analysis)


def create_by_category_sheet(df, writer):
    """Crea hoja de análisis por categoría."""
    print("📊 Creando análisis por Categoría...")
    
    category_analysis = df.groupby('Categoría (2° Nivel)').agg({
        'SKU': 'nunique',
        'Brand Name CEG': 'nunique',
        'Cantidad': 'sum',
        'Cantidad Unitarias': 'sum',
        'Total Item': 'sum',
        'Total Item con IVA': 'sum',
        'Precio Venta Unitario': 'mean',
        '% Margen sobre FOB': 'mean',
        '% Margen sobre Plataforma': 'mean',
        'Volumen del Item': 'sum',
    }).reset_index()
    
    total_facturado = category_analysis['Total Item con IVA'].sum()
    category_analysis['Participación %'] = (
        category_analysis['Total Item con IVA'] / total_facturado * 100
    )
    
    category_analysis = category_analysis.sort_values('Total Item con IVA', ascending=False)
    
    category_analysis.columns = [
        'Categoría (2° Nivel)', 'Productos Únicos', 'Marcas Únicas',
        'Cantidad Cajas', 'Cantidad Unidades', 'Facturación Neta (USD)',
        'Facturación con IVA (USD)', 'Precio Promedio Unitario',
        'Margen % FOB', 'Margen % Plataforma', 'Volumen Total (m³)', 'Participación %'
    ]
    
    category_analysis.to_excel(writer, sheet_name='08_Por Categoría', index=False)
    auto_adjust_column_widths(writer, '08_Por Categoría', category_analysis)


def create_margin_analysis_sheet(df, writer):
    """Crea hojas de análisis de márgenes."""
    print("📊 Creando análisis de Márgenes...")
    
    margin_df = df[
        (df['% Margen sobre FOB'] > 0) & 
        (df['% Margen sobre Plataforma'] > 0)
    ].copy()
    
    # Análisis por rango de margen FOB
    margin_df['Rango Margen FOB'] = pd.cut(
        margin_df['% Margen sobre FOB'],
        bins=[0, 50, 100, 150, 200, float('inf')],
        labels=['0-50%', '50-100%', '100-150%', '150-200%', '200%+']
    )
    
    margin_fob_analysis = margin_df.groupby('Rango Margen FOB').agg({
        'SKU': 'nunique',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
    }).reset_index()
    
    margin_fob_analysis.columns = [
        'Rango Margen FOB', 'Productos Únicos', 'Facturación Total (USD)', 'Unidades Vendidas'
    ]
    
    # Análisis por rango de margen Plataforma
    margin_df['Rango Margen Plataforma'] = pd.cut(
        margin_df['% Margen sobre Plataforma'],
        bins=[0, 10, 20, 30, 50, float('inf')],
        labels=['0-10%', '10-20%', '20-30%', '30-50%', '50%+']
    )
    
    margin_plat_analysis = margin_df.groupby('Rango Margen Plataforma').agg({
        'SKU': 'nunique',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
    }).reset_index()
    
    margin_plat_analysis.columns = [
        'Rango Margen Plataforma', 'Productos Únicos', 'Facturación Total (USD)', 'Unidades Vendidas'
    ]
    
    # Top productos por margen FOB
    top_margin_fob = margin_df.nlargest(20, '% Margen sobre FOB')[
        ['SKU', 'Nombre Producto', 'Brand Name CEG', '% Margen sobre FOB', 
         'Total Item con IVA', 'Cantidad Unitarias']
    ]
    top_margin_fob.columns = [
        'SKU', 'Producto', 'Marca', 'Margen % FOB', 'Facturación (USD)', 'Unidades'
    ]
    
    # Top productos por margen Plataforma
    top_margin_plat = margin_df.nlargest(20, '% Margen sobre Plataforma')[
        ['SKU', 'Nombre Producto', 'Brand Name CEG', '% Margen sobre Plataforma',
         'Total Item con IVA', 'Cantidad Unitarias']
    ]
    top_margin_plat.columns = [
        'SKU', 'Producto', 'Marca', 'Margen % Plataforma', 'Facturación (USD)', 'Unidades'
    ]
    
    # Agregar nota sobre precios en hojas de márgenes
    nota_fob = pd.DataFrame([{
        'Rango Margen FOB': '⚠️ NOTA: Precios FOB actualizados al 18.02.2026. Pueden explicar márgenes negativos vs ventas históricas.',
        'Productos Únicos': 'Queda pendiente cruce con costos históricos reales.',
        'Facturación Total (USD)': '',
        'Unidades Vendidas': ''
    }])
    margin_fob_analysis = pd.concat([nota_fob, margin_fob_analysis], ignore_index=True)
    
    nota_plat = pd.DataFrame([{
        'Rango Margen Plataforma': '⚠️ NOTA: Precios Plataforma CEG (mejor escala) actualizados al 18.02.2026. Tienden a la baja.',
        'Productos Únicos': 'Esto puede explicar parcialmente los márgenes negativos observados.',
        'Facturación Total (USD)': 'Queda pendiente cruce con costos históricos reales.',
        'Unidades Vendidas': ''
    }])
    margin_plat_analysis = pd.concat([nota_plat, margin_plat_analysis], ignore_index=True)
    
    margin_fob_analysis.to_excel(writer, sheet_name='09_Márgenes FOB', index=False)
    auto_adjust_column_widths(writer, '09_Márgenes FOB', margin_fob_analysis)
    margin_plat_analysis.to_excel(writer, sheet_name='10_Márgenes Plataforma', index=False)
    auto_adjust_column_widths(writer, '10_Márgenes Plataforma', margin_plat_analysis)
    top_margin_fob.to_excel(writer, sheet_name='11_Top 20 Margen FOB', index=False)
    auto_adjust_column_widths(writer, '11_Top 20 Margen FOB', top_margin_fob)
    top_margin_plat.to_excel(writer, sheet_name='12_Top 20 Margen Plataforma', index=False)
    auto_adjust_column_widths(writer, '12_Top 20 Margen Plataforma', top_margin_plat)


def create_top_products_sheet(df, writer):
    """Crea hojas con top productos."""
    print("📊 Creando Top Productos...")
    
    # Top por facturación
    top_facturacion = df.groupby('SKU').agg({
        'Nombre Producto': 'first',
        'Brand Name CEG': 'first',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
        'Cantidad': 'sum',
    }).reset_index().nlargest(50, 'Total Item con IVA')
    
    top_facturacion.columns = [
        'SKU', 'Producto', 'Marca', 'Facturación Total (USD)', 'Unidades', 'Cajas'
    ]
    
    # Top por unidades vendidas
    top_unidades = df.groupby('SKU').agg({
        'Nombre Producto': 'first',
        'Brand Name CEG': 'first',
        'Cantidad Unitarias': 'sum',
        'Total Item con IVA': 'sum',
    }).reset_index().nlargest(50, 'Cantidad Unitarias')
    
    top_unidades.columns = [
        'SKU', 'Producto', 'Marca', 'Unidades', 'Facturación Total (USD)'
    ]
    
    top_facturacion.to_excel(writer, sheet_name='13_Top 50 Facturación', index=False)
    auto_adjust_column_widths(writer, '13_Top 50 Facturación', top_facturacion)
    top_unidades.to_excel(writer, sheet_name='14_Top 50 Unidades', index=False)
    auto_adjust_column_widths(writer, '14_Top 50 Unidades', top_unidades)


def create_data_ninja_suggestions(df, stock_data, catalog, writer):
    """Crea hoja con sugerencias DATA NINJA."""
    print("📊 Creando sugerencias DATA NINJA...")
    
    sugerencias = []
    
    # Agrupar ventas por SKU
    ventas_por_sku = df.groupby('SKU').agg({
        'Cantidad Unitarias': 'sum',
        'Email Cliente': lambda x: x.nunique(),
    }).reset_index()
    ventas_por_sku.columns = ['SKU', 'unidades_vendidas', 'clientes']
    
    # Productos con stock alto y ventas bajas
    for d365_ref, stock_info in stock_data.items():
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                stock_unidades = float(stock_info['stock_cajas'] * stock_info['box_qty'])
                ventas_info = ventas_por_sku[ventas_por_sku['SKU'] == sku]
                
                if len(ventas_info) > 0:
                    unidades_vendidas = float(ventas_info.iloc[0]['unidades_vendidas'])
                    if stock_unidades > 100 and unidades_vendidas < 10:
                        sugerencias.append({
                            'Tipo Análisis': 'Stock Alto / Ventas Bajas',
                            'SKU': sku,
                            'Producto': cat_info.get('nombre', ''),
                            'Marca': cat_info.get('marca', ''),
                            'Stock Unidades': stock_unidades,
                            'Unidades Vendidas': unidades_vendidas,
                            'Sugerencia': f'Considerar promoción o descuento. Stock {stock_unidades:.0f} unidades vs {unidades_vendidas:.0f} vendidas.',
                            'Prioridad': 'ALTA',
                        })
                break
    
    if sugerencias:
        df_sugerencias = pd.DataFrame(sugerencias)
        df_sugerencias.to_excel(writer, sheet_name='15_DATA NINJA Sugerencias', index=False)
        auto_adjust_column_widths(writer, '15_DATA NINJA Sugerencias', df_sugerencias)
        print(f"   ✅ {len(sugerencias)} sugerencias generadas")


def generate_mega_excel():
    """Genera el mega Excel completo."""
    print("🔄 Generando MEGA EXCEL COMPLETO...")
    
    # Cargar datos
    df = load_ventas()
    catalog = load_catalog()
    stock_data = load_stock()
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Crear Excel
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Siempre crear al menos el resumen ejecutivo
        try:
            create_enhanced_summary_sheet(df, writer)
        except Exception as e:
            print(f"   ⚠️  Error creando resumen ejecutivo: {e}")
            # Crear resumen básico
            summary_df = pd.DataFrame({
                'Métrica': ['Estado', 'Mensaje'],
                'Valor': ['Sin datos', 'Ejecutar export_ventas_tradeunity.py para generar datos de ventas']
            })
            summary_df.to_excel(writer, sheet_name='00_Resumen Ejecutivo', index=False)
            auto_adjust_column_widths(writer, '00_Resumen Ejecutivo', summary_df)
        
        # Crear otras hojas solo si hay datos
        if len(df) > 0:
            try:
                create_ventas_sheet(df, writer)
                create_cliente_producto_sheet(df, writer)
                create_sku_clientes_potenciales(df, stock_data, catalog, writer)
                create_analisis_por_cliente_detallado(df, writer)
                create_by_product_sheet(df, writer)
                create_by_brand_sheet(df, writer)
                create_by_category_sheet(df, writer)
                create_margin_analysis_sheet(df, writer)
                create_top_products_sheet(df, writer)
                create_data_ninja_suggestions(df, stock_data, catalog, writer)
            except Exception as e:
                print(f"   ⚠️  Error creando algunas hojas: {e}")
        else:
            # Crear hojas vacías con estructura para cuando haya datos
            print("   ⚠️  Sin datos de ventas, creando hojas con estructura básica...")
            empty_df = pd.DataFrame(columns=['SKU', 'Mensaje'])
            empty_df.loc[0] = ['N/A', 'Sin datos de ventas históricas. Ejecutar export_ventas_tradeunity.py para generar datos.']
            empty_df.to_excel(writer, sheet_name='01_Ventas', index=False)
            auto_adjust_column_widths(writer, '01_Ventas', empty_df)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    print(f"\n📋 Hojas creadas:")
    print(f"   00. Resumen Ejecutivo (con métricas trimestrales desde 2024)")
    print(f"   01. Ventas (datos originales)")
    print(f"   02. Cliente-Producto (desglosado)")
    print(f"   03. SKU Clientes Potenciales (con probabilidades)")
    print(f"   04. Análisis por Cliente (detallado)")
    print(f"   05. Resumen por Cliente")
    print(f"   06. Por Producto")
    print(f"   07. Por Marca")
    print(f"   08. Por Categoría")
    print(f"   09. Márgenes FOB")
    print(f"   10. Márgenes Plataforma")
    print(f"   11. Top 20 Margen FOB")
    print(f"   12. Top 20 Margen Plataforma")
    print(f"   13. Top 50 Facturación")
    print(f"   14. Top 50 Unidades")
    print(f"   15. DATA NINJA Sugerencias")


if __name__ == "__main__":
    if not HAS_PANDAS:
        print("Instalando pandas...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    print("🔄 Iniciando generación de MEGA EXCEL COMPLETO...")
    generate_mega_excel()
    print("\n✨ Proceso completado!")
