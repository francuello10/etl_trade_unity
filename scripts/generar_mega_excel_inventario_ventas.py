#!/usr/bin/env python3
"""
MEGA EXCEL: Análisis completo de Inventario + Ventas
Incluye análisis por SKU con clientes potenciales y probabilidades de compra.
"""

import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import datetime, timedelta
import math

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Archivos
VENTAS_CSV = "ventas_historicas_items_FINAL.csv"
STOCK_ERP = "fuentes/stock erp.csv"
CATALOGO_TU = "fuentes/Catalogo TU.csv"
OUTPUT_EXCEL = "MEGA_ANALISIS_INVENTARIO_VENTAS_TradeUnity.xlsx"


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
    
    ventas_data = []
    
    with open(VENTAS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ventas_data.append(row)
    
    print(f"   ✅ {len(ventas_data)} registros de ventas cargados")
    return ventas_data


def calculate_purchase_probability(cliente_data, hoy):
    """
    Calcula probabilidad de compra basada en:
    - Frecuencia de compra histórica
    - Días desde última compra
    - Cantidad promedio comprada
    - Variabilidad en compras
    """
    if not cliente_data['compras']:
        return Decimal('0')
    
    compras = cliente_data['compras']
    num_compras = len(compras)
    
    if num_compras == 0:
        return Decimal('0')
    
    # Días desde última compra
    ultima_compra = max(c['fecha'] for c in compras if c['fecha'])
    if ultima_compra:
        dias_desde_ultima = days_between(ultima_compra, hoy)
        if dias_desde_ultima is None:
            dias_desde_ultima = 999
    else:
        dias_desde_ultima = 999
    
    # Frecuencia promedio (días entre compras)
    fechas_ordenadas = sorted([c['fecha'] for c in compras if c['fecha']])
    if len(fechas_ordenadas) > 1:
        intervalos = []
        for i in range(1, len(fechas_ordenadas)):
            intervalo = days_between(fechas_ordenadas[i-1], fechas_ordenadas[i])
            if intervalo and intervalo > 0:
                intervalos.append(intervalo)
        
        if intervalos:
            frecuencia_promedio = sum(intervalos) / len(intervalos)
        else:
            frecuencia_promedio = 180  # Default 6 meses
    else:
        frecuencia_promedio = 180
    
    # Cantidad promedio comprada
    cantidades = [c['cantidad_unidades'] for c in compras if c['cantidad_unidades'] > 0]
    cantidad_promedio = sum(cantidades) / len(cantidades) if cantidades else Decimal('0')
    
    # Factor de frecuencia (más compras = mayor probabilidad)
    factor_frecuencia = min(num_compras / 10, 1.0)  # Máximo 1.0
    
    # Factor de tiempo (mientras más cerca de la frecuencia promedio, mayor probabilidad)
    if frecuencia_promedio > 0:
        factor_tiempo = max(0, 1 - (abs(dias_desde_ultima - frecuencia_promedio) / frecuencia_promedio))
        factor_tiempo = min(factor_tiempo, 1.0)
    else:
        factor_tiempo = 0.5
    
    # Factor de recencia (mientras más reciente, mayor probabilidad)
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
    
    # Probabilidad combinada (peso: frecuencia 30%, tiempo 30%, recencia 40%)
    probabilidad = (
        factor_frecuencia * 0.3 +
        factor_tiempo * 0.3 +
        factor_recencia * 0.4
    )
    
    return Decimal(str(probabilidad))


def create_sku_clientes_potenciales(ventas_data, stock_data, catalog, writer):
    """
    Crea hoja de análisis por SKU con clientes potenciales.
    Para cada SKU con stock, muestra clientes que lo compraron antes.
    """
    print("📊 Creando análisis SKU - Clientes Potenciales...")
    
    hoy = datetime.now().date()
    
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
        d365_ref = str(row.get('Código CEG', '')).strip()
        
        if not sku or not email:
            continue
        
        fecha_str = row.get('Fecha Creación', '').strip()
        fecha = parse_date(fecha_str)
        cantidad_unidades = parse_decimal(row.get('Cantidad Unitarias', ''))
        precio_unitario = parse_decimal(row.get('Precio Venta Unitario', ''))
        total_item = parse_decimal(row.get('Total Item con IVA', ''))
        
        # Guardar datos del cliente (primera vez)
        if not sku_clientes[sku][email]['nombre']:
            sku_clientes[sku][email]['nombre'] = str(row.get('Nombre Cliente', '')).strip()
            sku_clientes[sku][email]['apellido'] = str(row.get('Apellido Cliente', '')).strip()
            sku_clientes[sku][email]['cuit'] = str(row.get('CUIT Cliente', '')).strip()
        
        sku_clientes[sku][email]['compras'].append({
            'fecha': fecha,
            'cantidad_unidades': cantidad_unidades,
            'precio_unitario': precio_unitario,
            'total_item': total_item,
            'orden': row.get('Número de Orden', ''),
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
    
    # Obtener SKUs con stock
    skus_con_stock = set()
    
    for d365_ref, stock_info in stock_data.items():
        # Buscar SKU por D365 Reference
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                skus_con_stock.add(sku)
                break
    
    # Para cada SKU con stock, listar clientes potenciales
    for sku in sorted(skus_con_stock):
        if sku not in sku_clientes:
            continue
        
        cat_info = catalog.get(sku, {})
        d365_ref = cat_info.get('d365_reference', '')
        stock_info = stock_data.get(d365_ref, {})
        
        stock_cajas = stock_info.get('stock_cajas', Decimal('0'))
        box_qty = stock_info.get('box_qty', Decimal('1'))
        stock_unidades = stock_cajas * box_qty
        
        # Para cada cliente que compró este SKU
        for email, cliente_data in sku_clientes[sku].items():
            # Calcular probabilidad de compra
            probabilidad = calculate_purchase_probability(cliente_data, hoy)
            
            # Cantidad esperada (basada en promedio histórico)
            cantidad_esperada = cliente_data['total_unidades'] / len(cliente_data['compras']) if cliente_data['compras'] else Decimal('0')
            
            # Stock restante después de venta esperada
            stock_restante = stock_unidades - (cantidad_esperada * probabilidad)
            
            # Última compra
            ultima_compra_info = max(
                cliente_data['compras'],
                key=lambda x: x['fecha'] if x['fecha'] else datetime(1900, 1, 1).date()
            )
            ultima_fecha = ultima_compra_info['fecha']
            dias_desde_ultima = days_between(ultima_fecha, hoy) if ultima_fecha else None
            
            # Calcular precio FOB y Plataforma para comparación
            fob_unitario = cat_info.get('fob_unitario', Decimal('0'))
            precio_plataforma = cat_info.get('precio_plataforma_unitario', Decimal('0'))
            precio_promedio = cliente_data['precio_promedio']
            
            # Margen histórico del cliente
            margen_vs_fob = precio_promedio - fob_unitario if precio_promedio > 0 and fob_unitario > 0 else Decimal('0')
            margen_vs_plataforma = precio_promedio - precio_plataforma if precio_promedio > 0 and precio_plataforma > 0 else Decimal('0')
            
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
                'Margen vs FOB': float(margen_vs_fob),
                'Margen vs Plataforma': float(margen_vs_plataforma),
                'Total Facturado Histórico': float(cliente_data['total_facturado']),
                'Probabilidad de Compra (%)': float(probabilidad * 100),
                'Cantidad Esperada (Probabilística)': float(cantidad_esperada * probabilidad),
                'Stock Restante Esperado': float(stock_restante),
            })
    
    # Crear DataFrame y ordenar
    df_resultados = pd.DataFrame(resultados)
    
    if len(df_resultados) > 0:
        df_resultados = df_resultados.sort_values(
            ['SKU', 'Probabilidad de Compra (%)'],
            ascending=[True, False]
        )
        
        df_resultados.to_excel(writer, sheet_name='SKU Clientes Potenciales', index=False)
        print(f"   ✅ {len(df_resultados)} registros creados")
    else:
        print("   ⚠️  No se encontraron datos para esta hoja")


def create_inventory_sales_summary(ventas_data, stock_data, catalog, writer):
    """Crea resumen de inventario con datos de ventas."""
    print("📊 Creando resumen Inventario-Ventas...")
    
    # Agrupar ventas por SKU
    ventas_por_sku = defaultdict(lambda: {
        'total_unidades': Decimal('0'),
        'total_facturado': Decimal('0'),
        'clientes_unicos': set(),
        'ordenes': set(),
        'precio_promedio': Decimal('0'),
        'ultima_venta': None,
    })
    
    for row in ventas_data:
        sku = str(row.get('SKU', '')).strip().upper()
        if not sku:
            continue
        
        email = str(row.get('Email Cliente', '')).strip()
        orden = str(row.get('Número de Orden', '')).strip()
        cantidad = parse_decimal(row.get('Cantidad Unitarias', ''))
        total = parse_decimal(row.get('Total Item con IVA', ''))
        precio = parse_decimal(row.get('Precio Venta Unitario', ''))
        fecha_str = row.get('Fecha Creación', '').strip()
        fecha = parse_date(fecha_str)
        
        ventas_por_sku[sku]['total_unidades'] += cantidad
        ventas_por_sku[sku]['total_facturado'] += total
        ventas_por_sku[sku]['clientes_unicos'].add(email)
        ventas_por_sku[sku]['ordenes'].add(orden)
        
        if fecha and (not ventas_por_sku[sku]['ultima_venta'] or fecha > ventas_por_sku[sku]['ultima_venta']):
            ventas_por_sku[sku]['ultima_venta'] = fecha
        
        if precio > 0:
            # Calcular promedio ponderado
            if ventas_por_sku[sku]['precio_promedio'] == 0:
                ventas_por_sku[sku]['precio_promedio'] = precio
            else:
                ventas_por_sku[sku]['precio_promedio'] = (
                    ventas_por_sku[sku]['precio_promedio'] * Decimal('0.7') + precio * Decimal('0.3')
                )
    
    # Crear resumen combinado
    resultados = []
    
    for d365_ref, stock_info in stock_data.items():
        # Buscar SKU
        sku_encontrado = None
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                sku_encontrado = sku
                break
        
        if not sku_encontrado:
            continue
        
        cat_info = catalog[sku_encontrado]
        ventas_info = ventas_por_sku.get(sku_encontrado, {})
        
        stock_cajas = stock_info['stock_cajas']
        box_qty = stock_info['box_qty']
        stock_unidades = stock_cajas * box_qty
        
        resultados.append({
            'SKU': sku_encontrado,
            'Nombre Producto': cat_info.get('nombre', ''),
            'Marca': cat_info.get('marca', ''),
            'Categoría': cat_info.get('categoria_2', ''),
            'Stock Cajas': float(stock_cajas),
            'Stock Unidades': float(stock_unidades),
            'Unidades Vendidas Históricas': float(ventas_info.get('total_unidades', Decimal('0'))),
            'Facturación Histórica': float(ventas_info.get('total_facturado', Decimal('0'))),
            'Clientes Únicos': len(ventas_info.get('clientes_unicos', set())),
            'Órdenes Totales': len(ventas_info.get('ordenes', set())),
            'Precio Promedio Vendido': float(ventas_info.get('precio_promedio', Decimal('0'))),
            'Última Venta': ventas_info.get('ultima_venta').strftime('%Y-%m-%d') if ventas_info.get('ultima_venta') else '',
            'FOB Unitario': float(cat_info.get('fob_unitario', Decimal('0'))),
            'Precio Plataforma Unitario': float(cat_info.get('precio_plataforma_unitario', Decimal('0'))),
            'Volumen Box (m³)': float(cat_info.get('volumen_box', Decimal('0'))),
        })
    
    df_resumen = pd.DataFrame(resultados)
    df_resumen = df_resumen.sort_values('Stock Unidades', ascending=False)
    
    df_resumen.to_excel(writer, sheet_name='00_Inventario Ventas', index=False)
    print(f"   ✅ {len(df_resumen)} productos en resumen")


def create_data_ninja_suggestions(ventas_data, stock_data, catalog, writer):
    """Crea hoja con sugerencias de análisis avanzado (DATA NINJA)."""
    print("📊 Creando sugerencias DATA NINJA...")
    
    sugerencias = []
    
    # 1. Productos con stock alto y ventas bajas
    ventas_por_sku = defaultdict(lambda: {'unidades': Decimal('0'), 'clientes': set()})
    for row in ventas_data:
        sku = str(row.get('SKU', '')).strip().upper()
        if sku:
            ventas_por_sku[sku]['unidades'] += parse_decimal(row.get('Cantidad Unitarias', ''))
            ventas_por_sku[sku]['clientes'].add(str(row.get('Email Cliente', '')).strip())
    
    for d365_ref, stock_info in stock_data.items():
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                stock_unidades = stock_info['stock_cajas'] * stock_info['box_qty']
                ventas_info = ventas_por_sku.get(sku, {})
                unidades_vendidas = ventas_info.get('unidades', Decimal('0'))
                
                if stock_unidades > 100 and unidades_vendidas < 10:
                    sugerencias.append({
                        'Tipo Análisis': 'Stock Alto / Ventas Bajas',
                        'SKU': sku,
                        'Producto': cat_info.get('nombre', ''),
                        'Marca': cat_info.get('marca', ''),
                        'Stock Unidades': float(stock_unidades),
                        'Unidades Vendidas': float(unidades_vendidas),
                        'Sugerencia': f'Considerar promoción o descuento. Stock {float(stock_unidades):.0f} unidades vs {float(unidades_vendidas):.0f} vendidas.',
                        'Prioridad': 'ALTA',
                    })
                break
    
    # 2. Productos con rotación rápida y stock bajo
    hoy = datetime.now().date()
    for sku, ventas_info in ventas_por_sku.items():
        if sku not in catalog:
            continue
        
        cat_info = catalog[sku]
        d365_ref = cat_info.get('d365_reference', '')
        stock_info = stock_data.get(d365_ref, {})
        
        if not stock_info:
            continue
        
        stock_unidades = stock_info['stock_cajas'] * stock_info['box_qty']
        unidades_vendidas = ventas_info['unidades']
        clientes = len(ventas_info['clientes'])
        
        # Calcular rotación (ventas / stock)
        if stock_unidades > 0:
            rotacion = unidades_vendidas / stock_unidades
            if rotacion > 2 and stock_unidades < 50 and clientes > 5:
                sugerencias.append({
                    'Tipo Análisis': 'Rotación Alta / Stock Bajo',
                    'SKU': sku,
                    'Producto': cat_info.get('nombre', ''),
                    'Marca': cat_info.get('marca', ''),
                    'Stock Unidades': float(stock_unidades),
                    'Unidades Vendidas': float(unidades_vendidas),
                    'Rotación': float(rotacion),
                    'Sugerencia': f'Reponer stock urgentemente. Rotación {float(rotacion):.2f}x, solo {float(stock_unidades):.0f} unidades disponibles.',
                    'Prioridad': 'URGENTE',
                })
    
    # 3. Clientes VIP (más compras)
    clientes_vip = defaultdict(lambda: {'compras': 0, 'facturado': Decimal('0'), 'productos': set()})
    for row in ventas_data:
        email = str(row.get('Email Cliente', '')).strip()
        if email:
            clientes_vip[email]['compras'] += 1
            clientes_vip[email]['facturado'] += parse_decimal(row.get('Total Item con IVA', ''))
            clientes_vip[email]['productos'].add(str(row.get('SKU', '')).strip().upper())
    
    top_clientes = sorted(clientes_vip.items(), key=lambda x: x[1]['facturado'], reverse=True)[:10]
    for email, info in top_clientes:
        sugerencias.append({
            'Tipo Análisis': 'Cliente VIP',
            'SKU': 'N/A',
            'Producto': f'Cliente: {email}',
            'Marca': 'N/A',
            'Stock Unidades': info['compras'],
            'Unidades Vendidas': len(info['productos']),
            'Rotación': float(info['facturado']),
            'Sugerencia': f'Cliente VIP con ${float(info["facturado"]):,.2f} facturado. Ofrecer descuentos exclusivos o productos nuevos.',
            'Prioridad': 'MEDIA',
        })
    
    # 4. Productos sin ventas pero con stock
    skus_con_stock = set()
    for d365_ref in stock_data:
        for sku, cat_info in catalog.items():
            if cat_info['d365_reference'] == d365_ref:
                skus_con_stock.add(sku)
                break
    
    skus_sin_ventas = skus_con_stock - set(ventas_por_sku.keys())
    for sku in list(skus_sin_ventas)[:20]:  # Top 20
        cat_info = catalog[sku]
        d365_ref = cat_info.get('d365_reference', '')
        stock_info = stock_data.get(d365_ref, {})
        stock_unidades = stock_info['stock_cajas'] * stock_info['box_qty']
        
        sugerencias.append({
            'Tipo Análisis': 'Sin Ventas / Con Stock',
            'SKU': sku,
            'Producto': cat_info.get('nombre', ''),
            'Marca': cat_info.get('marca', ''),
            'Stock Unidades': float(stock_unidades),
            'Unidades Vendidas': 0,
            'Rotación': 0,
            'Sugerencia': f'Producto nunca vendido con {float(stock_unidades):.0f} unidades. Revisar precio, descripción o considerar liquidación.',
            'Prioridad': 'ALTA',
        })
    
    df_sugerencias = pd.DataFrame(sugerencias)
    df_sugerencias.to_excel(writer, sheet_name='DATA NINJA Sugerencias', index=False)
    print(f"   ✅ {len(sugerencias)} sugerencias generadas")


def generate_mega_excel():
    """Genera el mega Excel completo."""
    print("🔄 Generando MEGA EXCEL Inventario + Ventas...")
    
    # Cargar datos
    catalog = load_catalog()
    stock_data = load_stock()
    ventas_data = load_ventas()
    
    # Crear Excel
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        create_inventory_sales_summary(ventas_data, stock_data, catalog, writer)
        create_sku_clientes_potenciales(ventas_data, stock_data, catalog, writer)
        create_data_ninja_suggestions(ventas_data, stock_data, catalog, writer)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    print(f"\n📋 Hojas creadas:")
    print(f"   00. Inventario Ventas (resumen combinado)")
    print(f"   SKU Clientes Potenciales (análisis por SKU)")
    print(f"   DATA NINJA Sugerencias (análisis avanzado)")


if __name__ == "__main__":
    if not HAS_PANDAS:
        print("Instalando pandas...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    print("🔄 Iniciando generación de MEGA EXCEL...")
    generate_mega_excel()
    print("\n✨ Proceso completado!")
