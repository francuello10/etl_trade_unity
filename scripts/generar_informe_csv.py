#!/usr/bin/env python3
"""
Script para generar informe completo de análisis de ventas en archivos CSV separados.
Cada análisis se guarda en un CSV individual para importar en spreadsheet.
"""

import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict

# Archivos
INPUT_CSV = "ventas_historicas_items_FINAL.csv"


def parse_decimal(value: str) -> Decimal:
    """Convierte string con formato europeo a Decimal."""
    if not value or value == "":
        return Decimal("0")
    
    value_str = str(value).strip().replace("$", "").replace(" ", "").replace("%", "")
    value_str = value_str.replace(",", ".")
    
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def format_number(value, decimals=2):
    """Formatea número para mostrar."""
    if value == 0 or value == "":
        return ""
    return f"{round(float(value), decimals):,.{decimals}f}".replace(".", ",").replace(",", ".", 1) if decimals > 0 else str(int(value))


def load_data():
    """Carga datos del CSV."""
    print(f"📖 Cargando datos desde: {INPUT_CSV}")
    
    rows = []
    headers = []
    
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        for row in reader:
            rows.append(row)
    
    print(f"   ✅ {len(rows)} filas cargadas")
    return rows, headers


def write_csv(filename, headers, rows):
    """Escribe un archivo CSV."""
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(f"   ✅ {filename} generado")


def create_summary_sheet(rows):
    """Crea CSV de resumen ejecutivo."""
    print("📊 Creando Resumen Ejecutivo...")
    
    # Calcular métricas
    ordenes_unicas = len(set(r.get('Número de Orden', '') for r in rows))
    total_items = len(rows)
    total_unidades = sum(parse_decimal(r.get('Cantidad Unitarias', '')) for r in rows)
    total_facturado = sum(parse_decimal(r.get('Total Item', '')) for r in rows)
    total_facturado_iva = sum(parse_decimal(r.get('Total Item con IVA', '')) for r in rows)
    productos_unicos = len(set(r.get('SKU', '') for r in rows if r.get('SKU')))
    marcas_unicas = len(set(r.get('Brand Name CEG', '') for r in rows if r.get('Brand Name CEG')))
    categorias_unicas = len(set(r.get('Categoría (2° Nivel)', '') for r in rows if r.get('Categoría (2° Nivel)')))
    
    # Márgenes promedio
    margenes_fob = [parse_decimal(r.get('% Margen sobre FOB', '')) for r in rows if r.get('% Margen sobre FOB')]
    margen_prom_fob = sum(margenes_fob) / len(margenes_fob) if margenes_fob else 0
    
    margenes_plat = [parse_decimal(r.get('% Margen sobre Plataforma', '')) for r in rows if r.get('% Margen sobre Plataforma')]
    margen_prom_plat = sum(margenes_plat) / len(margenes_plat) if margenes_plat else 0
    
    volumen_total = sum(parse_decimal(r.get('Volumen del Item', '')) for r in rows)
    
    summary_data = [
        {'Métrica': 'Total Órdenes', 'Valor': str(ordenes_unicas)},
        {'Métrica': 'Total Items Vendidos', 'Valor': str(total_items)},
        {'Métrica': 'Total Unidades Vendidas', 'Valor': format_number(total_unidades, 0)},
        {'Métrica': 'Total Facturado (USD)', 'Valor': format_number(total_facturado, 2)},
        {'Métrica': 'Total Facturado con IVA (USD)', 'Valor': format_number(total_facturado_iva, 2)},
        {'Métrica': 'Productos Únicos Vendidos', 'Valor': str(productos_unicos)},
        {'Métrica': 'Marcas Únicas', 'Valor': str(marcas_unicas)},
        {'Métrica': 'Categorías Únicas', 'Valor': str(categorias_unicas)},
        {'Métrica': 'Margen Promedio sobre FOB (%)', 'Valor': format_number(margen_prom_fob, 2)},
        {'Métrica': 'Margen Promedio sobre Plataforma (%)', 'Valor': format_number(margen_prom_plat, 2)},
        {'Métrica': 'Volumen Total (m³)', 'Valor': format_number(volumen_total, 6)},
    ]
    
    write_csv('01_Resumen_Ejecutivo.csv', ['Métrica', 'Valor'], summary_data)


def create_by_product_sheet(rows):
    """Crea CSV de análisis por producto."""
    print("📊 Creando análisis por Producto...")
    
    products = defaultdict(lambda: {
        'Nombre Producto': '',
        'Brand Name CEG': '',
        'Categoría (2° Nivel)': '',
        'Categoría CEG': '',
        'Cantidad': Decimal('0'),
        'Cantidad Unitarias': Decimal('0'),
        'Total Item': Decimal('0'),
        'Total Item con IVA': Decimal('0'),
        'Precio Venta Unitario': [],
        'FOB CEG': Decimal('0'),
        'Base Price CEG': Decimal('0'),
        '% Margen sobre FOB': [],
        '% Margen sobre Plataforma': [],
        'Volumen del Item': Decimal('0'),
    })
    
    for row in rows:
        sku = row.get('SKU', '').strip()
        if not sku:
            continue
        
        if not products[sku]['Nombre Producto']:
            products[sku]['Nombre Producto'] = row.get('Nombre Producto', '')
            products[sku]['Brand Name CEG'] = row.get('Brand Name CEG', '')
            products[sku]['Categoría (2° Nivel)'] = row.get('Categoría (2° Nivel)', '')
            products[sku]['Categoría CEG'] = row.get('Categoría CEG', '')
            products[sku]['FOB CEG'] = parse_decimal(row.get('FOB CEG', ''))
            products[sku]['Base Price CEG'] = parse_decimal(row.get('Base Price CEG', ''))
        
        products[sku]['Cantidad'] += parse_decimal(row.get('Cantidad', ''))
        products[sku]['Cantidad Unitarias'] += parse_decimal(row.get('Cantidad Unitarias', ''))
        products[sku]['Total Item'] += parse_decimal(row.get('Total Item', ''))
        products[sku]['Total Item con IVA'] += parse_decimal(row.get('Total Item con IVA', ''))
        products[sku]['Volumen del Item'] += parse_decimal(row.get('Volumen del Item', ''))
        
        pvu = parse_decimal(row.get('Precio Venta Unitario', ''))
        if pvu > 0:
            products[sku]['Precio Venta Unitario'].append(pvu)
        
        mfob = parse_decimal(row.get('% Margen sobre FOB', ''))
        if mfob > 0:
            products[sku]['% Margen sobre FOB'].append(mfob)
        
        mplat = parse_decimal(row.get('% Margen sobre Plataforma', ''))
        if mplat > 0:
            products[sku]['% Margen sobre Plataforma'].append(mplat)
    
    # Convertir a formato final
    product_data = []
    for sku, data in products.items():
        precio_prom = sum(data['Precio Venta Unitario']) / len(data['Precio Venta Unitario']) if data['Precio Venta Unitario'] else 0
        margen_fob_prom = sum(data['% Margen sobre FOB']) / len(data['% Margen sobre FOB']) if data['% Margen sobre FOB'] else 0
        margen_plat_prom = sum(data['% Margen sobre Plataforma']) / len(data['% Margen sobre Plataforma']) if data['% Margen sobre Plataforma'] else 0
        
        margen_abs_fob = (precio_prom - data['FOB CEG']) * data['Cantidad Unitarias'] if precio_prom > 0 and data['FOB CEG'] > 0 else 0
        margen_abs_plat = (precio_prom - data['Base Price CEG']) * data['Cantidad Unitarias'] if precio_prom > 0 and data['Base Price CEG'] > 0 else 0
        
        product_data.append({
            'SKU': sku,
            'Nombre Producto': data['Nombre Producto'],
            'Marca': data['Brand Name CEG'],
            'Categoría (2° Nivel)': data['Categoría (2° Nivel)'],
            'Categoría CEG': data['Categoría CEG'],
            'Cantidad Cajas': format_number(data['Cantidad'], 0),
            'Cantidad Unidades': format_number(data['Cantidad Unitarias'], 0),
            'Facturación Neta (USD)': format_number(data['Total Item'], 2),
            'Facturación con IVA (USD)': format_number(data['Total Item con IVA'], 2),
            'Precio Promedio Unitario': format_number(precio_prom, 4),
            'FOB Unitario': format_number(data['FOB CEG'], 4),
            'Precio Plataforma Unitario': format_number(data['Base Price CEG'], 4),
            'Margen % FOB': format_number(margen_fob_prom, 2),
            'Margen % Plataforma': format_number(margen_plat_prom, 2),
            'Volumen Total (m³)': format_number(data['Volumen del Item'], 6),
            'Margen Absoluto FOB': format_number(margen_abs_fob, 2),
            'Margen Absoluto Plataforma': format_number(margen_abs_plat, 2),
        })
    
    # Ordenar por facturación
    product_data.sort(key=lambda x: parse_decimal(x.get('Facturación con IVA (USD)', '0')), reverse=True)
    
    headers = ['SKU', 'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
               'Cantidad Cajas', 'Cantidad Unidades', 'Facturación Neta (USD)', 
               'Facturación con IVA (USD)', 'Precio Promedio Unitario', 'FOB Unitario',
               'Precio Plataforma Unitario', 'Margen % FOB', 'Margen % Plataforma',
               'Volumen Total (m³)', 'Margen Absoluto FOB', 'Margen Absoluto Plataforma']
    
    write_csv('02_Por_Producto.csv', headers, product_data)


def create_by_brand_sheet(rows):
    """Crea CSV de análisis por marca."""
    print("📊 Creando análisis por Marca...")
    
    brands = defaultdict(lambda: {
        'SKUs': set(),
        'Cantidad': Decimal('0'),
        'Cantidad Unitarias': Decimal('0'),
        'Total Item': Decimal('0'),
        'Total Item con IVA': Decimal('0'),
        'Precio Venta Unitario': [],
        '% Margen sobre FOB': [],
        '% Margen sobre Plataforma': [],
        'Volumen del Item': Decimal('0'),
    })
    
    for row in rows:
        brand = row.get('Brand Name CEG', '').strip()
        if not brand:
            continue
        
        brands[brand]['SKUs'].add(row.get('SKU', ''))
        brands[brand]['Cantidad'] += parse_decimal(row.get('Cantidad', ''))
        brands[brand]['Cantidad Unitarias'] += parse_decimal(row.get('Cantidad Unitarias', ''))
        brands[brand]['Total Item'] += parse_decimal(row.get('Total Item', ''))
        brands[brand]['Total Item con IVA'] += parse_decimal(row.get('Total Item con IVA', ''))
        brands[brand]['Volumen del Item'] += parse_decimal(row.get('Volumen del Item', ''))
        
        pvu = parse_decimal(row.get('Precio Venta Unitario', ''))
        if pvu > 0:
            brands[brand]['Precio Venta Unitario'].append(pvu)
        
        mfob = parse_decimal(row.get('% Margen sobre FOB', ''))
        if mfob > 0:
            brands[brand]['% Margen sobre FOB'].append(mfob)
        
        mplat = parse_decimal(row.get('% Margen sobre Plataforma', ''))
        if mplat > 0:
            brands[brand]['% Margen sobre Plataforma'].append(mplat)
    
    total_facturado = sum(b['Total Item con IVA'] for b in brands.values())
    
    brand_data = []
    for brand, data in brands.items():
        precio_prom = sum(data['Precio Venta Unitario']) / len(data['Precio Venta Unitario']) if data['Precio Venta Unitario'] else 0
        margen_fob_prom = sum(data['% Margen sobre FOB']) / len(data['% Margen sobre FOB']) if data['% Margen sobre FOB'] else 0
        margen_plat_prom = sum(data['% Margen sobre Plataforma']) / len(data['% Margen sobre Plataforma']) if data['% Margen sobre Plataforma'] else 0
        participacion = (data['Total Item con IVA'] / total_facturado * 100) if total_facturado > 0 else 0
        
        brand_data.append({
            'Marca': brand,
            'Productos Únicos': str(len(data['SKUs'])),
            'Cantidad Cajas': format_number(data['Cantidad'], 0),
            'Cantidad Unidades': format_number(data['Cantidad Unitarias'], 0),
            'Facturación Neta (USD)': format_number(data['Total Item'], 2),
            'Facturación con IVA (USD)': format_number(data['Total Item con IVA'], 2),
            'Precio Promedio Unitario': format_number(precio_prom, 4),
            'Margen % FOB': format_number(margen_fob_prom, 2),
            'Margen % Plataforma': format_number(margen_plat_prom, 2),
            'Volumen Total (m³)': format_number(data['Volumen del Item'], 6),
            'Participación %': format_number(participacion, 2),
        })
    
    brand_data.sort(key=lambda x: parse_decimal(x.get('Facturación con IVA (USD)', '0')), reverse=True)
    
    headers = ['Marca', 'Productos Únicos', 'Cantidad Cajas', 'Cantidad Unidades',
               'Facturación Neta (USD)', 'Facturación con IVA (USD)', 
               'Precio Promedio Unitario', 'Margen % FOB', 'Margen % Plataforma',
               'Volumen Total (m³)', 'Participación %']
    
    write_csv('03_Por_Marca.csv', headers, brand_data)


def create_by_category_sheet(rows):
    """Crea CSV de análisis por categoría."""
    print("📊 Creando análisis por Categoría...")
    
    categories = defaultdict(lambda: {
        'SKUs': set(),
        'Brands': set(),
        'Cantidad': Decimal('0'),
        'Cantidad Unitarias': Decimal('0'),
        'Total Item': Decimal('0'),
        'Total Item con IVA': Decimal('0'),
        'Precio Venta Unitario': [],
        '% Margen sobre FOB': [],
        '% Margen sobre Plataforma': [],
        'Volumen del Item': Decimal('0'),
    })
    
    for row in rows:
        category = row.get('Categoría (2° Nivel)', '').strip()
        if not category:
            continue
        
        categories[category]['SKUs'].add(row.get('SKU', ''))
        categories[category]['Brands'].add(row.get('Brand Name CEG', ''))
        categories[category]['Cantidad'] += parse_decimal(row.get('Cantidad', ''))
        categories[category]['Cantidad Unitarias'] += parse_decimal(row.get('Cantidad Unitarias', ''))
        categories[category]['Total Item'] += parse_decimal(row.get('Total Item', ''))
        categories[category]['Total Item con IVA'] += parse_decimal(row.get('Total Item con IVA', ''))
        categories[category]['Volumen del Item'] += parse_decimal(row.get('Volumen del Item', ''))
        
        pvu = parse_decimal(row.get('Precio Venta Unitario', ''))
        if pvu > 0:
            categories[category]['Precio Venta Unitario'].append(pvu)
        
        mfob = parse_decimal(row.get('% Margen sobre FOB', ''))
        if mfob > 0:
            categories[category]['% Margen sobre FOB'].append(mfob)
        
        mplat = parse_decimal(row.get('% Margen sobre Plataforma', ''))
        if mplat > 0:
            categories[category]['% Margen sobre Plataforma'].append(mplat)
    
    total_facturado = sum(c['Total Item con IVA'] for c in categories.values())
    
    category_data = []
    for category, data in categories.items():
        precio_prom = sum(data['Precio Venta Unitario']) / len(data['Precio Venta Unitario']) if data['Precio Venta Unitario'] else 0
        margen_fob_prom = sum(data['% Margen sobre FOB']) / len(data['% Margen sobre FOB']) if data['% Margen sobre FOB'] else 0
        margen_plat_prom = sum(data['% Margen sobre Plataforma']) / len(data['% Margen sobre Plataforma']) if data['% Margen sobre Plataforma'] else 0
        participacion = (data['Total Item con IVA'] / total_facturado * 100) if total_facturado > 0 else 0
        
        category_data.append({
            'Categoría (2° Nivel)': category,
            'Productos Únicos': str(len(data['SKUs'])),
            'Marcas Únicas': str(len(data['Brands'])),
            'Cantidad Cajas': format_number(data['Cantidad'], 0),
            'Cantidad Unidades': format_number(data['Cantidad Unitarias'], 0),
            'Facturación Neta (USD)': format_number(data['Total Item'], 2),
            'Facturación con IVA (USD)': format_number(data['Total Item con IVA'], 2),
            'Precio Promedio Unitario': format_number(precio_prom, 4),
            'Margen % FOB': format_number(margen_fob_prom, 2),
            'Margen % Plataforma': format_number(margen_plat_prom, 2),
            'Volumen Total (m³)': format_number(data['Volumen del Item'], 6),
            'Participación %': format_number(participacion, 2),
        })
    
    category_data.sort(key=lambda x: parse_decimal(x.get('Facturación con IVA (USD)', '0')), reverse=True)
    
    headers = ['Categoría (2° Nivel)', 'Productos Únicos', 'Marcas Únicas',
               'Cantidad Cajas', 'Cantidad Unidades', 'Facturación Neta (USD)',
               'Facturación con IVA (USD)', 'Precio Promedio Unitario',
               'Margen % FOB', 'Margen % Plataforma', 'Volumen Total (m³)', 'Participación %']
    
    write_csv('04_Por_Categoria.csv', headers, category_data)


def create_margin_analysis_sheets(rows):
    """Crea CSVs de análisis de márgenes."""
    print("📊 Creando análisis de Márgenes...")
    
    # Filtrar productos con datos de margen
    margin_rows = [r for r in rows if parse_decimal(r.get('% Margen sobre FOB', '')) > 0 and parse_decimal(r.get('% Margen sobre Plataforma', '')) > 0]
    
    # Análisis por rango de margen FOB
    ranges_fob = {
        '0-50%': [],
        '50-100%': [],
        '100-150%': [],
        '150-200%': [],
        '200%+': [],
    }
    
    for row in margin_rows:
        margen = parse_decimal(row.get('% Margen sobre FOB', ''))
        if margen <= 50:
            ranges_fob['0-50%'].append(row)
        elif margen <= 100:
            ranges_fob['50-100%'].append(row)
        elif margen <= 150:
            ranges_fob['100-150%'].append(row)
        elif margen <= 200:
            ranges_fob['150-200%'].append(row)
        else:
            ranges_fob['200%+'].append(row)
    
    margin_fob_data = []
    for rango, items in ranges_fob.items():
        skus_unicos = len(set(r.get('SKU', '') for r in items))
        facturacion = sum(parse_decimal(r.get('Total Item con IVA', '')) for r in items)
        unidades = sum(parse_decimal(r.get('Cantidad Unitarias', '')) for r in items)
        
        margin_fob_data.append({
            'Rango Margen FOB': rango,
            'Productos Únicos': str(skus_unicos),
            'Facturación Total (USD)': format_number(facturacion, 2),
            'Unidades Vendidas': format_number(unidades, 0),
        })
    
    write_csv('05_Margenes_FOB.csv', ['Rango Margen FOB', 'Productos Únicos', 'Facturación Total (USD)', 'Unidades Vendidas'], margin_fob_data)
    
    # Análisis por rango de margen Plataforma
    ranges_plat = {
        '0-10%': [],
        '10-20%': [],
        '20-30%': [],
        '30-50%': [],
        '50%+': [],
    }
    
    for row in margin_rows:
        margen = parse_decimal(row.get('% Margen sobre Plataforma', ''))
        if margen <= 10:
            ranges_plat['0-10%'].append(row)
        elif margen <= 20:
            ranges_plat['10-20%'].append(row)
        elif margen <= 30:
            ranges_plat['20-30%'].append(row)
        elif margen <= 50:
            ranges_plat['30-50%'].append(row)
        else:
            ranges_plat['50%+'].append(row)
    
    margin_plat_data = []
    for rango, items in ranges_plat.items():
        skus_unicos = len(set(r.get('SKU', '') for r in items))
        facturacion = sum(parse_decimal(r.get('Total Item con IVA', '')) for r in items)
        unidades = sum(parse_decimal(r.get('Cantidad Unitarias', '')) for r in items)
        
        margin_plat_data.append({
            'Rango Margen Plataforma': rango,
            'Productos Únicos': str(skus_unicos),
            'Facturación Total (USD)': format_number(facturacion, 2),
            'Unidades Vendidas': format_number(unidades, 0),
        })
    
    write_csv('06_Margenes_Plataforma.csv', ['Rango Margen Plataforma', 'Productos Únicos', 'Facturación Total (USD)', 'Unidades Vendidas'], margin_plat_data)
    
    # Top 20 por margen FOB
    top_fob = sorted(margin_rows, key=lambda x: parse_decimal(x.get('% Margen sobre FOB', '0')), reverse=True)[:20]
    top_fob_data = []
    for row in top_fob:
        top_fob_data.append({
            'SKU': row.get('SKU', ''),
            'Producto': row.get('Nombre Producto', ''),
            'Marca': row.get('Brand Name CEG', ''),
            'Margen % FOB': format_number(parse_decimal(row.get('% Margen sobre FOB', '')), 2),
            'Facturación (USD)': format_number(parse_decimal(row.get('Total Item con IVA', '')), 2),
            'Unidades': format_number(parse_decimal(row.get('Cantidad Unitarias', '')), 0),
        })
    
    write_csv('07_Top_20_Margen_FOB.csv', ['SKU', 'Producto', 'Marca', 'Margen % FOB', 'Facturación (USD)', 'Unidades'], top_fob_data)
    
    # Top 20 por margen Plataforma
    top_plat = sorted(margin_rows, key=lambda x: parse_decimal(x.get('% Margen sobre Plataforma', '0')), reverse=True)[:20]
    top_plat_data = []
    for row in top_plat:
        top_plat_data.append({
            'SKU': row.get('SKU', ''),
            'Producto': row.get('Nombre Producto', ''),
            'Marca': row.get('Brand Name CEG', ''),
            'Margen % Plataforma': format_number(parse_decimal(row.get('% Margen sobre Plataforma', '')), 2),
            'Facturación (USD)': format_number(parse_decimal(row.get('Total Item con IVA', '')), 2),
            'Unidades': format_number(parse_decimal(row.get('Cantidad Unitarias', '')), 0),
        })
    
    write_csv('08_Top_20_Margen_Plataforma.csv', ['SKU', 'Producto', 'Marca', 'Margen % Plataforma', 'Facturación (USD)', 'Unidades'], top_plat_data)


def create_top_products_sheets(rows):
    """Crea CSVs con top productos."""
    print("📊 Creando Top Productos...")
    
    # Agrupar por SKU
    products = defaultdict(lambda: {
        'Nombre Producto': '',
        'Brand Name CEG': '',
        'Cantidad Unitarias': Decimal('0'),
        'Cantidad': Decimal('0'),
        'Total Item con IVA': Decimal('0'),
    })
    
    for row in rows:
        sku = row.get('SKU', '').strip()
        if not sku:
            continue
        
        if not products[sku]['Nombre Producto']:
            products[sku]['Nombre Producto'] = row.get('Nombre Producto', '')
            products[sku]['Brand Name CEG'] = row.get('Brand Name CEG', '')
        
        products[sku]['Cantidad Unitarias'] += parse_decimal(row.get('Cantidad Unitarias', ''))
        products[sku]['Cantidad'] += parse_decimal(row.get('Cantidad', ''))
        products[sku]['Total Item con IVA'] += parse_decimal(row.get('Total Item con IVA', ''))
    
    # Top 50 por facturación
    top_facturacion = sorted(products.items(), key=lambda x: x[1]['Total Item con IVA'], reverse=True)[:50]
    top_fact_data = []
    for sku, data in top_facturacion:
        top_fact_data.append({
            'SKU': sku,
            'Producto': data['Nombre Producto'],
            'Marca': data['Brand Name CEG'],
            'Facturación Total (USD)': format_number(data['Total Item con IVA'], 2),
            'Unidades': format_number(data['Cantidad Unitarias'], 0),
            'Cajas': format_number(data['Cantidad'], 0),
        })
    
    write_csv('09_Top_50_Facturacion.csv', ['SKU', 'Producto', 'Marca', 'Facturación Total (USD)', 'Unidades', 'Cajas'], top_fact_data)
    
    # Top 50 por unidades
    top_unidades = sorted(products.items(), key=lambda x: x[1]['Cantidad Unitarias'], reverse=True)[:50]
    top_uni_data = []
    for sku, data in top_unidades:
        top_uni_data.append({
            'SKU': sku,
            'Producto': data['Nombre Producto'],
            'Marca': data['Brand Name CEG'],
            'Unidades': format_number(data['Cantidad Unitarias'], 0),
            'Facturación Total (USD)': format_number(data['Total Item con IVA'], 2),
        })
    
    write_csv('10_Top_50_Unidades.csv', ['SKU', 'Producto', 'Marca', 'Unidades', 'Facturación Total (USD)'], top_uni_data)


def generate_report():
    """Genera todos los informes CSV."""
    print("🔄 Generando informes CSV...")
    
    # Cargar datos
    rows, headers = load_data()
    
    # Crear todos los informes
    create_summary_sheet(rows)
    create_by_product_sheet(rows)
    create_by_brand_sheet(rows)
    create_by_category_sheet(rows)
    create_margin_analysis_sheets(rows)
    create_top_products_sheets(rows)
    
    print(f"\n✨ Todos los informes CSV generados:")
    print(f"   01_Resumen_Ejecutivo.csv")
    print(f"   02_Por_Producto.csv")
    print(f"   03_Por_Marca.csv")
    print(f"   04_Por_Categoria.csv")
    print(f"   05_Margenes_FOB.csv")
    print(f"   06_Margenes_Plataforma.csv")
    print(f"   07_Top_20_Margen_FOB.csv")
    print(f"   08_Top_20_Margen_Plataforma.csv")
    print(f"   09_Top_50_Facturacion.csv")
    print(f"   10_Top_50_Unidades.csv")


if __name__ == "__main__":
    print("🔄 Iniciando generación de informes CSV...")
    generate_report()
    print("\n✨ Proceso completado!")
