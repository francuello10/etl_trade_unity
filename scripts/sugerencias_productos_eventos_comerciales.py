#!/usr/bin/env python3
"""
Sistema de Sugerencias Inteligentes de Productos para Eventos Comerciales - Trade Unity

Alineado con documento base Trade Unity:
- Ecommerce B2B mayorista del grupo CEG
- Rubros principales: Máquinas y Herramientas, Hogar y Bazar, Electricidad e Iluminación, 
  Sanitarios y Griferías, Outdoor y Camping
- Principios de operación: No romper operación por promos, reglas trazables, 
  datos como sistema nervioso

Analiza:
- Calendario comercial 2026 con eventos específicos
- Patrones de compra históricos por categoría y marca
- Stock disponible del ERP
- Precios CEG (FOB y Plataforma)
- Genera sugerencias teledirigidas por tipo de evento (Bundles, Liquidaciones, Flash Sales)
"""

import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from collections import defaultdict
import pandas as pd

# Archivos
CALENDARIO_CSV = "fuentes/Calendario comercial - Hoja de trabajo.csv"
VENTAS_CSV = "inputs/ventas_historicas_items_FINAL.csv"  # Fuente: Ventas.xlsx hoja 01_Ventas
STOCK_ERP = "fuentes/stock erp.csv"
CATALOGO_TU = "fuentes/Catalogo TU.csv"
CEG_PRODUCTOS_CSV = "fuentes/Productos plataforma CEG_base price unit & fob_Tabla (2).csv"
OUTPUT_DIR = "outputs"
OUTPUT_EXCEL = f"{OUTPUT_DIR}/TradeUnity Commercial Calendar 2026.xlsx"


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


def load_calendario():
    """Carga calendario comercial y filtra eventos TU."""
    print("📖 Cargando calendario comercial...")
    
    df = pd.read_csv(CALENDARIO_CSV, encoding='utf-8-sig')
    eventos_tu = df[df['UNIDAD DE NEGOCIO'] == 'TU'].copy()
    
    eventos = []
    for _, row in eventos_tu.iterrows():
        mes = str(row.get('MES', '')).strip()
        nombre = str(row.get('NOMBRE COMERCIAL- FECHA', '')).strip()
        tipo_accion = str(row.get('TIPO DE ACCION', '')).strip()
        objetivo = str(row.get('OBJETIVO', '')).strip()
        
        if nombre and nombre != 'nan':
            eventos.append({
                'mes': mes,
                'nombre': nombre,
                'tipo_accion': tipo_accion,
                'objetivo': objetivo,
            })
    
    print(f"   ✅ {len(eventos)} eventos TU encontrados")
    return eventos


def load_ventas():
    """Carga datos de ventas y analiza patrones."""
    print("📖 Cargando y analizando ventas...")
    
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
    numeric_cols = ['Cantidad Unitarias', 'Total Item con IVA', 'Precio Venta Unitario']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convertir fechas
    if 'Fecha Creación' in df.columns:
        df['Fecha Creación'] = pd.to_datetime(df['Fecha Creación'], errors='coerce')
        df['Mes'] = df['Fecha Creación'].dt.month
        df['Año'] = df['Fecha Creación'].dt.year
    
    print(f"   ✅ {len(df)} registros de ventas cargados")
    return df


def load_stock():
    """Carga stock del ERP."""
    print("📖 Cargando stock...")
    
    stock_data = {}
    
    with open(STOCK_ERP, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d365_ref = str(row.get('D365 Reference', '')).strip()
            stock_cajas = parse_decimal(row.get('Pronosticado con pendiente', ''))
            box_qty = parse_decimal(row.get('Box Qty', ''))
            
            if d365_ref and stock_cajas > 0:
                stock_data[d365_ref] = {
                    'stock_cajas': stock_cajas,
                    'box_qty': box_qty,
                    'stock_unidades': stock_cajas * box_qty,
                }
    
    print(f"   ✅ {len(stock_data)} productos con stock")
    return stock_data


def load_catalog():
    """Carga catálogo TU."""
    print("📖 Cargando catálogo TU...")
    
    catalog = {}
    
    with open(CATALOGO_TU, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = str(row.get('sku', '')).strip().upper()
            d365_ref = str(row.get('Código de Producto (D365)', '')).strip()
            
            if sku and d365_ref:
                catalog[sku] = {
                    'd365_reference': d365_ref,
                    'nombre': str(row.get('Nombre del Producto', '')).strip(),
                    'marca': str(row.get('Marca', '')).strip(),
                    'categoria_2': str(row.get('Categoría (2° Nivel)', '')).strip(),
                    'categoria_ceg': str(row.get('Categoría CEG', '')).strip(),
                }
    
    print(f"   ✅ {len(catalog)} productos en catálogo")
    return catalog


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


def load_ceg_prices():
    """Carga precios CEG."""
    print("📖 Cargando precios CEG...")
    
    ceg_prices = {}
    
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
    
    print(f"   ✅ {len(ceg_prices)} productos con precios")
    return ceg_prices


def analyze_purchase_patterns(ventas_df):
    """Analiza patrones de compra por categoría, marca, etc."""
    print("📊 Analizando patrones de compra...")
    
    # Si no hay datos de ventas, crear DataFrames vacíos con estructura correcta
    if len(ventas_df) == 0:
        print("   ⚠️  Sin datos de ventas históricas, creando estructuras vacías...")
        categoria_analysis = pd.DataFrame(columns=['Categoría', 'SKUs Únicos', 'Facturación Total', 'Unidades Vendidas', 'Clientes Únicos', 'Precio Promedio'])
        marca_analysis = pd.DataFrame(columns=['Marca', 'SKUs Únicos', 'Facturación Total', 'Unidades Vendidas', 'Clientes Únicos'])
        top_productos = pd.DataFrame(columns=['SKU', 'Nombre', 'Marca', 'Categoría', 'Facturación', 'Unidades', 'Clientes'])
        return {
            'categoria': categoria_analysis,
            'marca': marca_analysis,
            'productos': top_productos,
        }
    
    # Análisis por categoría
    categoria_analysis = ventas_df.groupby('Categoría (2° Nivel)').agg({
        'SKU': 'nunique',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
        'Email Cliente': 'nunique',
        'Precio Venta Unitario': 'mean',
    }).reset_index()
    
    categoria_analysis.columns = [
        'Categoría', 'SKUs Únicos', 'Facturación Total', 'Unidades Vendidas',
        'Clientes Únicos', 'Precio Promedio'
    ]
    
    # Análisis por marca
    marca_analysis = ventas_df.groupby('Brand Name CEG').agg({
        'SKU': 'nunique',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
        'Email Cliente': 'nunique',
    }).reset_index()
    
    marca_analysis.columns = [
        'Marca', 'SKUs Únicos', 'Facturación Total', 'Unidades Vendidas', 'Clientes Únicos'
    ]
    
    # Top productos por facturación
    top_productos = ventas_df.groupby('SKU').agg({
        'Nombre Producto': 'first',
        'Brand Name CEG': 'first',
        'Categoría (2° Nivel)': 'first',
        'Total Item con IVA': 'sum',
        'Cantidad Unitarias': 'sum',
        'Email Cliente': 'nunique',
    }).reset_index()
    
    top_productos.columns = [
        'SKU', 'Nombre', 'Marca', 'Categoría', 'Facturación', 'Unidades', 'Clientes'
    ]
    
    # Asegurar que Facturación sea numérico
    if 'Facturación' in top_productos.columns:
        top_productos['Facturación'] = pd.to_numeric(top_productos['Facturación'], errors='coerce').fillna(0)
    
    return {
        'categoria': categoria_analysis,
        'marca': marca_analysis,
        'productos': top_productos,
    }


def match_event_to_categories(evento_nombre, tipo_accion, categoria_analysis, ventas_df):
    """Mapea eventos a categorías relevantes basado en el tipo de evento y patrones históricos."""
    
    # Mapeo de eventos a categorías según documento base Trade Unity
    # Rubros principales: Máquinas y Herramientas, Hogar y Bazar, Electricidad e Iluminación, 
    # Sanitarios y Griferías, Outdoor y Camping
    evento_categorias = {
        'Rebajas de Verano': ['Outdoor y Camping', 'Hogar y Bazar'],
        'Vuelta al Cole': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],
        'San Valentín': ['Hogar y Bazar'],  # Productos para el hogar
        'Día Internacional de la Mujer': ['Hogar y Bazar'],  # Productos para el hogar
        'Día del Consumidor': ['Máquinas y Herramientas', 'Electricidad e Iluminación', 'Hogar y Bazar'],
        'Semana Santa': ['Outdoor y Camping'],  # Productos para salidas
        'Hot Sale': ['Máquinas y Herramientas', 'Electricidad e Iluminación', 'Hogar y Bazar', 'Outdoor y Camping', 'Sanitarios y Griferías'],
        'Día de la Tierra': ['Hogar y Bazar'],  # Productos sustentables
        'Día del Trabajador': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],
        'Día de la Madre': ['Hogar y Bazar', 'Sanitarios y Griferías'],  # Productos para el hogar
        'Día del Padre': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],
        'Inicio de Invierno': ['Hogar y Bazar'],  # Productos para el hogar
        'Mid Season Sale': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],  # Liquidación herramientas
        'Día del Amigo': ['Outdoor y Camping'],  # Productos para compartir
        'Día de la Niñez': ['Hogar y Bazar'],  # Productos familiares
        'Primavera': ['Hogar y Bazar', 'Outdoor y Camping'],
        'Halloween': ['Hogar y Bazar'],  # Decoración
        'Singles Day': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],
        'Black Friday': ['Máquinas y Herramientas', 'Electricidad e Iluminación', 'Hogar y Bazar', 'Outdoor y Camping', 'Sanitarios y Griferías'],
        'Cyber Monday': ['Máquinas y Herramientas', 'Electricidad e Iluminación'],
        'Navidad': ['Hogar y Bazar', 'Sanitarios y Griferías'],  # Gift packs hogar
        'Fin de Año': ['Máquinas y Herramientas', 'Electricidad e Iluminación', 'Hogar y Bazar'],
    }
    
    # Buscar categorías relevantes
    categorias_relevantes = []
    for evento_key, cats in evento_categorias.items():
        if evento_key.lower() in evento_nombre.lower():
            categorias_relevantes = cats
            break
    
    # Si no hay match exacto, analizar ventas históricas del mes del evento
    if not categorias_relevantes:
        # Mapear mes del evento a número
        meses_map = {
            'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
            'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
        }
        # Usar todas las categorías ordenadas por facturación
        categorias_relevantes = categoria_analysis.sort_values('Facturación Total', ascending=False)['Categoría'].head(5).tolist()
    
    return categorias_relevantes


def _generate_recommendation_reason(producto, evento):
    """Genera razón de recomendación personalizada."""
    razones = []
    
    if producto['facturacion_historica'] > 20000:
        razones.append(f"Alta facturación histórica (${producto['facturacion_historica']:,.0f})")
    
    if producto['stock_unidades'] > 500:
        razones.append(f"Stock abundante ({producto['stock_unidades']:.0f} unidades)")
    elif producto['stock_unidades'] > 100:
        razones.append(f"Stock moderado ({producto['stock_unidades']:.0f} unidades)")
    
    if producto['clientes_unicos'] > 20:
        razones.append(f"Demanda probada ({producto['clientes_unicos']} clientes únicos)")
    
    if 'Bundle' in evento['tipo_accion']:
        razones.append("Ideal para combinar en bundle")
    elif 'Liquidación' in evento['tipo_accion']:
        razones.append("Adecuado para liquidación (stock disponible)")
    
    return " | ".join(razones) if razones else "Producto con buen historial de ventas"


def generate_suggestions(eventos, ventas_df, stock_data, catalog, ceg_prices, patterns, writer):
    """Genera sugerencias de productos para cada evento."""
    print("📊 Generando sugerencias por evento...")
    
    # Mapear D365 a SKU
    d365_to_sku = {}
    for sku, info in catalog.items():
        d365_to_sku[info['d365_reference']] = sku
    
    # Obtener productos con stock y sus datos
    productos_con_stock = {}
    for d365_ref, stock_info in stock_data.items():
        sku = d365_to_sku.get(d365_ref, '')
        if sku and sku in catalog:
            cat_info = catalog[sku]
            ceg_info = ceg_prices.get(sku, {})
            
            # Ventas de este producto
            ventas_producto = ventas_df[ventas_df['SKU'] == sku]
            
            # Calcular métricas adicionales
            precio_normal = float(ceg_info.get('precio_normal_tu', 0))
            fob = float(ceg_info.get('fob', 0))
            facturacion_historica = float(ventas_producto['Total Item con IVA'].sum()) if len(ventas_producto) > 0 else 0
            unidades_vendidas = int(ventas_producto['Cantidad Unitarias'].sum()) if len(ventas_producto) > 0 else 0
            stock_unidades = float(stock_info['stock_unidades'])
            
            # Calcular margen potencial
            margen_unitario = precio_normal - fob if precio_normal > 0 and fob > 0 else 0
            margen_porcentaje = (margen_unitario / precio_normal * 100) if precio_normal > 0 else 0
            
            # Calcular rotación histórica (unidades vendidas / tiempo)
            precio_promedio_vendido = float(ventas_producto['Precio Venta Unitario'].mean()) if len(ventas_producto) > 0 else 0
            ultima_venta = ventas_producto['Fecha Creación'].max() if len(ventas_producto) > 0 else None
            dias_desde_ultima_venta = (datetime.now() - ultima_venta).days if ultima_venta is not None and pd.notna(ultima_venta) else None
            
            # Calcular días de stock (basado en rotación histórica)
            rotacion_mensual = unidades_vendidas / 12 if unidades_vendidas > 0 else 0
            dias_stock = (stock_unidades / rotacion_mensual * 30) if rotacion_mensual > 0 else 999
            
            # Calcular ROI potencial del stock
            valor_stock_fob = stock_unidades * fob
            valor_stock_venta = stock_unidades * precio_normal
            ganancia_potencial = valor_stock_venta - valor_stock_fob
            
            productos_con_stock[sku] = {
                'sku': sku,
                'nombre': cat_info.get('nombre', ''),
                'marca': cat_info.get('marca', ''),
                'categoria': cat_info.get('categoria_2', ''),
                'stock_unidades': stock_unidades,
                'stock_cajas': float(stock_info['stock_cajas']),
                'precio_normal': precio_normal,
                'fob': fob,
                'facturacion_historica': facturacion_historica,
                'unidades_vendidas': unidades_vendidas,
                'clientes_unicos': int(ventas_producto['Email Cliente'].nunique()) if len(ventas_producto) > 0 else 0,
                'precio_promedio_vendido': precio_promedio_vendido,
                'margen_unitario': margen_unitario,
                'margen_porcentaje': margen_porcentaje,
                'dias_desde_ultima_venta': dias_desde_ultima_venta,
                'dias_stock': dias_stock,
                'rotacion_mensual': rotacion_mensual,
                'valor_stock_fob': valor_stock_fob,
                'valor_stock_venta': valor_stock_venta,
                'ganancia_potencial': ganancia_potencial,
            }
    
    # Generar sugerencias por evento
    todas_sugerencias = []
    
    meses_orden = {
        'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
        'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
    }
    
    hoy = datetime.now()
    mes_actual = hoy.month
    
    for evento in eventos:
        mes_num = meses_orden.get(evento['mes'], 99)
        
        # Solo eventos futuros o del mes actual
        if mes_num < mes_actual:
            continue
        
        categorias_relevantes = match_event_to_categories(
            evento['nombre'], 
            evento['tipo_accion'],
            patterns['categoria'],
            ventas_df
        )
        
        # Filtrar productos por categorías relevantes y con stock
        productos_candidatos = [
            p for p in productos_con_stock.values()
            if p['categoria'] in categorias_relevantes and p['stock_unidades'] > 0
        ]
        
        # Ordenar por criterios de relevancia específicos por tipo de evento
        if 'Bundle' in evento['tipo_accion']:
            # Para bundles, priorizar productos con buen precio y stock
            productos_candidatos.sort(
                key=lambda x: (
                    x['facturacion_historica'] * 0.3 +
                    min(x['stock_unidades'] / 50, 2) * 5000 * 0.4 +  # Más peso a stock para bundles
                    x['clientes_unicos'] * 100 * 0.3
                ),
                reverse=True
            )
        elif 'Liquidación' in evento['tipo_accion']:
            # Para liquidaciones, priorizar productos con mucho stock
            productos_candidatos.sort(
                key=lambda x: (
                    x['stock_unidades'] * 0.5 +  # 50% peso a stock
                    x['facturacion_historica'] * 0.3 +
                    x['clientes_unicos'] * 100 * 0.2
                ),
                reverse=True
            )
        elif 'Flash' in evento['tipo_accion']:
            # Para flash sales, priorizar productos de alta rotación
            productos_candidatos.sort(
                key=lambda x: (
                    x['facturacion_historica'] * 0.5 +  # 50% peso a facturación
                    x['unidades_vendidas'] * 10 * 0.3 +
                    min(x['stock_unidades'] / 100, 1) * 5000 * 0.2
                ),
                reverse=True
            )
        else:
            # Default: balance entre facturación, stock y clientes
            productos_candidatos.sort(
                key=lambda x: (
                    x['facturacion_historica'] * 0.4 +
                    min(x['stock_unidades'] / 100, 1) * 10000 * 0.3 +
                    x['clientes_unicos'] * 100 * 0.3
                ),
                reverse=True
            )
        
        # Asegurar diversidad: máximo 3 productos por marca, máximo 5 por categoría
        productos_seleccionados = []
        marcas_usadas = defaultdict(int)
        categorias_usadas = defaultdict(int)
        
        for producto in productos_candidatos:
            marca = producto['marca']
            categoria = producto['categoria']
            
            # Limitar productos por marca y categoría para diversidad
            if marcas_usadas[marca] < 3 and categorias_usadas[categoria] < 5:
                productos_seleccionados.append(producto)
                marcas_usadas[marca] += 1
                categorias_usadas[categoria] += 1
                
                if len(productos_seleccionados) >= 20:
                    break
        
        # Si no llegamos a 20, completar con los mejores restantes
        if len(productos_seleccionados) < 20:
            productos_restantes = [p for p in productos_candidatos if p not in productos_seleccionados]
            productos_seleccionados.extend(productos_restantes[:20 - len(productos_seleccionados)])
        
        top_productos = productos_seleccionados
        
        for producto in top_productos:
            # Calcular score de recomendación (ajustado por tipo de evento)
            if 'Bundle' in evento['tipo_accion']:
                score = (
                    (producto['facturacion_historica'] / 1000) * 0.3 +
                    (min(producto['stock_unidades'] / 50, 2)) * 0.4 +
                    (producto['clientes_unicos'] / 10) * 0.3
                )
            elif 'Liquidación' in evento['tipo_accion']:
                score = (
                    (producto['stock_unidades'] / 100) * 0.5 +
                    (producto['facturacion_historica'] / 1000) * 0.3 +
                    (producto['clientes_unicos'] / 10) * 0.2
                )
            else:
                score = (
                    (producto['facturacion_historica'] / 1000) * 0.4 +
                    (min(producto['stock_unidades'] / 100, 1)) * 0.3 +
                    (producto['clientes_unicos'] / 10) * 0.3
                )
            
            # Sugerir tipo de acción
            if 'Bundle' in evento['tipo_accion']:
                accion_sugerida = 'Bundle (combo con productos relacionados)'
            elif 'Descuento' in evento['tipo_accion']:
                descuento_sugerido = 15 if 'Flash' in evento['tipo_accion'] else 25
                accion_sugerida = f'Descuento {descuento_sugerido}%'
            elif 'Liquidación' in evento['tipo_accion']:
                accion_sugerida = 'Liquidación (30-40% descuento)'
            else:
                accion_sugerida = evento['tipo_accion']
            
            todas_sugerencias.append({
                'Evento': evento['nombre'],
                'Mes': evento['mes'],
                'Tipo Acción': evento['tipo_accion'],
                'SKU': producto['sku'],
                'Nombre Producto': producto['nombre'],
                'Marca': producto['marca'],
                'Categoría': producto['categoria'],
                'Stock Unidades': producto['stock_unidades'],
                'Stock Cajas': producto['stock_cajas'],
                'Precio Normal TU': producto['precio_normal'],
                'FOB': producto['fob'],
                'Margen Unitario': producto['margen_unitario'],
                'Margen %': round(producto['margen_porcentaje'], 2),
                'Facturación Histórica (USD)': producto['facturacion_historica'],
                'Unidades Vendidas Históricas': producto['unidades_vendidas'],
                'Rotación Mensual': round(producto['rotacion_mensual'], 2),
                'Días de Stock': round(producto['dias_stock'], 0) if producto['dias_stock'] < 999 else 'N/A',
                'Días desde Última Venta': producto['dias_desde_ultima_venta'] if producto['dias_desde_ultima_venta'] is not None else 'N/A',
                'Clientes Únicos': producto['clientes_unicos'],
                'Precio Promedio Vendido': producto['precio_promedio_vendido'],
                'Valor Stock FOB': producto['valor_stock_fob'],
                'Valor Stock Venta': producto['valor_stock_venta'],
                'Ganancia Potencial': producto['ganancia_potencial'],
                'Score Recomendación': round(score, 2),
                'Acción Sugerida': accion_sugerida,
                'Razón Recomendación': _generate_recommendation_reason(producto, evento),
            })
    
    df_sugerencias = pd.DataFrame(todas_sugerencias)
    df_sugerencias = df_sugerencias.sort_values(['Mes', 'Evento', 'Score Recomendación'], ascending=[True, True, False])
    
    df_sugerencias.to_excel(writer, sheet_name='01_Sugerencias por Evento', index=False)
    auto_adjust_column_widths(writer, '01_Sugerencias por Evento', df_sugerencias)
    print(f"   ✅ {len(todas_sugerencias)} sugerencias generadas")
    
    # Resumen por evento
    resumen_eventos = []
    for evento in eventos:
        sugerencias_evento = df_sugerencias[df_sugerencias['Evento'] == evento['nombre']]
        if len(sugerencias_evento) > 0:
            resumen_eventos.append({
                'Evento': evento['nombre'],
                'Mes': evento['mes'],
                'Tipo Acción': evento['tipo_accion'],
                'Productos Sugeridos': len(sugerencias_evento),
                'Total Stock Disponible': int(sugerencias_evento['Stock Unidades'].sum()),
                'Facturación Histórica Total': float(sugerencias_evento['Facturación Histórica (USD)'].sum()),
                'Marcas Únicas': int(sugerencias_evento['Marca'].nunique()),
                'Categorías Únicas': int(sugerencias_evento['Categoría'].nunique()),
            })
    
    df_resumen = pd.DataFrame(resumen_eventos)
    df_resumen.to_excel(writer, sheet_name='02_Resumen por Evento', index=False)
    auto_adjust_column_widths(writer, '02_Resumen por Evento', df_resumen)
    print(f"   ✅ {len(resumen_eventos)} eventos resumidos")


def generate_commercial_suggestions():
    """Genera sistema completo de sugerencias."""
    print("🔄 Generando Sistema de Sugerencias Comerciales...")
    
    # Cargar datos
    eventos = load_calendario()
    ventas_df = load_ventas()
    stock_data = load_stock()
    catalog = load_catalog()
    ceg_prices = load_ceg_prices()
    
    # Analizar patrones
    patterns = analyze_purchase_patterns(ventas_df)
    
    # Crear directorio de salida si no existe
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generar sugerencias
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        generate_suggestions(eventos, ventas_df, stock_data, catalog, ceg_prices, patterns, writer)
        
        # Agregar análisis de patrones
        patterns['categoria'].to_excel(writer, sheet_name='03_Patrones por Categoría', index=False)
        auto_adjust_column_widths(writer, '03_Patrones por Categoría', patterns['categoria'])
        patterns['marca'].to_excel(writer, sheet_name='04_Patrones por Marca', index=False)
        auto_adjust_column_widths(writer, '04_Patrones por Marca', patterns['marca'])
        
        # Top productos (solo si hay datos)
        if len(patterns['productos']) > 0 and 'Facturación' in patterns['productos'].columns:
            top_productos = patterns['productos'].nlargest(100, 'Facturación')
        else:
            top_productos = patterns['productos'].head(100) if len(patterns['productos']) > 0 else patterns['productos']
        top_productos.to_excel(writer, sheet_name='05_Top 100 Productos', index=False)
        auto_adjust_column_widths(writer, '05_Top 100 Productos', top_productos)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    print(f"\n📋 Hojas creadas:")
    print(f"   01. Sugerencias por Evento (productos recomendados)")
    print(f"   02. Resumen por Evento")
    print(f"   03. Patrones por Categoría")
    print(f"   04. Patrones por Marca")
    print(f"   05. Top 100 Productos")


if __name__ == "__main__":
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("Instalando dependencias...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    generate_commercial_suggestions()
    print("\n✨ Proceso completado!")
