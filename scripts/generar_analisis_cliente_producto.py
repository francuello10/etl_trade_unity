#!/usr/bin/env python3
"""
Script para generar análisis desglosado por Cliente y Producto (SKU).
Agrupa ventas por cliente y SKU con todas las métricas agregadas.
"""

import csv
from decimal import Decimal, InvalidOperation
from collections import defaultdict

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Archivos
VENTAS_CSV = "ventas_historicas_items.csv"
OUTPUT_CSV = "Analisis_Cliente_Producto.csv"


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


def format_number_european(value, decimals=2):
    """Formatea número en formato europeo: punto para miles, coma para decimales."""
    if value == 0 or value == "":
        return ""
    
    if decimals == 0:
        return f"{int(value):,}".replace(",", ".")
    else:
        formatted = f"{float(value):,.{decimals}f}"
        parts = formatted.split(".")
        if len(parts) == 2:
            integer_part = parts[0].replace(",", ".")
            decimal_part = parts[1]
            return f"{integer_part},{decimal_part}"
        else:
            return formatted.replace(",", ".")


def generate_cliente_producto_analysis():
    """Genera análisis desglosado por cliente y producto."""
    print("📖 Cargando datos de ventas...")
    
    rows = []
    
    with open(VENTAS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"   ✅ {len(rows)} filas cargadas")
    
    # Agrupar por cliente y SKU
    cliente_producto = defaultdict(lambda: {
        'email': '',
        'nombre': '',
        'apellido': '',
        'cuit': '',
        'sku': '',
        'nombre_producto': '',
        'marca': '',
        'categoria_2': '',
        'categoria_ceg': '',
        'ordenes': set(),
        'fechas_compra': [],
        'cantidad_cajas': Decimal('0'),
        'cantidad_unidades': Decimal('0'),
        'precios_unitarios': [],
        'precios_caja': [],
        'precio_unitario_promedio': Decimal('0'),
        'precio_unitario_max': Decimal('0'),
        'precio_unitario_min': Decimal('0'),
        'precio_caja_promedio': Decimal('0'),
        'fob_unitario': Decimal('0'),
        'precio_plataforma_unitario': Decimal('0'),
        'total_item': Decimal('0'),
        'total_item_iva': Decimal('0'),
        'volumen_total': Decimal('0'),
        'margen_fob': Decimal('0'),
        'margen_plataforma': Decimal('0'),
        'pct_margen_fob': Decimal('0'),
        'pct_margen_plataforma': Decimal('0'),
        'primera_compra': None,
        'ultima_compra': None,
    })
    
    print("\n🔄 Agrupando por Cliente y Producto...")
    
    for row in rows:
        email = row.get('Email Cliente', '').strip()
        sku = row.get('SKU', '').strip().upper()
        
        if not email or not sku:
            continue
        
        key = f"{email}|{sku}"
        
        # Datos del cliente (solo primera vez)
        if not cliente_producto[key]['email']:
            cliente_producto[key]['email'] = email
            cliente_producto[key]['nombre'] = row.get('Nombre Cliente', '').strip()
            cliente_producto[key]['apellido'] = row.get('Apellido Cliente', '').strip()
            cliente_producto[key]['cuit'] = row.get('CUIT Cliente', '').strip()
            cliente_producto[key]['sku'] = sku
            cliente_producto[key]['nombre_producto'] = row.get('Nombre Producto', '').strip()
            cliente_producto[key]['marca'] = row.get('Brand Name CEG', '').strip()
            cliente_producto[key]['categoria_2'] = row.get('Categoría (2° Nivel)', '').strip()
            cliente_producto[key]['categoria_ceg'] = row.get('Categoría CEG', '').strip()
            cliente_producto[key]['fob_unitario'] = parse_decimal(row.get('FOB CEG', ''))
            cliente_producto[key]['precio_plataforma_unitario'] = parse_decimal(row.get('Base Price CEG', ''))
        
        # Agregar datos de venta
        orden_id = row.get('Número de Orden', '').strip()
        fecha_creacion = row.get('Fecha Creación', '').strip()
        
        cliente_producto[key]['ordenes'].add(orden_id)
        cliente_producto[key]['fechas_compra'].append(fecha_creacion)
        
        cantidad_cajas = parse_decimal(row.get('Cantidad', ''))
        cantidad_unidades = parse_decimal(row.get('Cantidad Unitarias', ''))
        precio_unitario = parse_decimal(row.get('Precio Venta Unitario', ''))
        precio_caja = parse_decimal(row.get('Precio Venta', ''))
        
        cliente_producto[key]['cantidad_cajas'] += cantidad_cajas
        cliente_producto[key]['cantidad_unidades'] += cantidad_unidades
        cliente_producto[key]['total_item'] += parse_decimal(row.get('Total Item', ''))
        cliente_producto[key]['total_item_iva'] += parse_decimal(row.get('Total Item con IVA', ''))
        cliente_producto[key]['volumen_total'] += parse_decimal(row.get('Volumen del Item', ''))
        
        if precio_unitario > 0:
            cliente_producto[key]['precios_unitarios'].append(precio_unitario)
        if precio_caja > 0:
            cliente_producto[key]['precios_caja'].append(precio_caja)
    
    # Calcular métricas finales
    print("🔄 Calculando métricas...")
    
    analysis_data = []
    
    for key, data in cliente_producto.items():
        # Calcular promedios, max, min
        if data['precios_unitarios']:
            data['precio_unitario_promedio'] = sum(data['precios_unitarios']) / len(data['precios_unitarios'])
            data['precio_unitario_max'] = max(data['precios_unitarios'])
            data['precio_unitario_min'] = min(data['precios_unitarios'])
        
        if data['precios_caja']:
            data['precio_caja_promedio'] = sum(data['precios_caja']) / len(data['precios_caja'])
        
        # Calcular márgenes
        if data['precio_unitario_promedio'] > 0 and data['fob_unitario'] > 0:
            data['margen_fob'] = data['precio_unitario_promedio'] - data['fob_unitario']
            data['pct_margen_fob'] = (data['margen_fob'] / data['fob_unitario'] * 100) if data['fob_unitario'] > 0 else Decimal('0')
        
        if data['precio_unitario_promedio'] > 0 and data['precio_plataforma_unitario'] > 0:
            data['margen_plataforma'] = data['precio_unitario_promedio'] - data['precio_plataforma_unitario']
            data['pct_margen_plataforma'] = (data['margen_plataforma'] / data['precio_plataforma_unitario'] * 100) if data['precio_plataforma_unitario'] > 0 else Decimal('0')
        
        # Fechas primera y última compra
        if data['fechas_compra']:
            fechas_sorted = sorted(data['fechas_compra'])
            data['primera_compra'] = fechas_sorted[0]
            data['ultima_compra'] = fechas_sorted[-1]
        
        analysis_data.append({
            'Email Cliente': data['email'],
            'Nombre Cliente': data['nombre'],
            'Apellido Cliente': data['apellido'],
            'CUIT Cliente': data['cuit'],
            'SKU': data['sku'],
            'Nombre Producto': data['nombre_producto'],
            'Marca': data['marca'],
            'Categoría (2° Nivel)': data['categoria_2'],
            'Categoría CEG': data['categoria_ceg'],
            'Número de Órdenes': len(data['ordenes']),
            'Cantidad Cajas Total': format_number_european(data['cantidad_cajas'], 0),
            'Cantidad Unidades Total': format_number_european(data['cantidad_unidades'], 0),
            'Precio Unitario Promedio': format_number_european(data['precio_unitario_promedio'], 4),
            'Precio Unitario Máximo': format_number_european(data['precio_unitario_max'], 4),
            'Precio Unitario Mínimo': format_number_european(data['precio_unitario_min'], 4),
            'Precio Caja Promedio': format_number_european(data['precio_caja_promedio'], 2),
            'FOB Unitario': format_number_european(data['fob_unitario'], 4),
            'Precio Plataforma Unitario': format_number_european(data['precio_plataforma_unitario'], 4),
            'Diferencia vs FOB': format_number_european(data['margen_fob'], 4),
            '% Diferencia vs FOB': format_number_european(data['pct_margen_fob'], 2),
            'Diferencia vs Plataforma': format_number_european(data['margen_plataforma'], 4),
            '% Diferencia vs Plataforma': format_number_european(data['pct_margen_plataforma'], 2),
            'Total Facturado (USD)': format_number_european(data['total_item'], 2),
            'Total Facturado con IVA (USD)': format_number_european(data['total_item_iva'], 2),
            'Volumen Total (m³)': format_number_european(data['volumen_total'], 6),
            'Primera Compra': data['primera_compra'] or '',
            'Última Compra': data['ultima_compra'] or '',
        })
    
    # Ordenar por cliente y luego por facturación
    analysis_data.sort(key=lambda x: (x['Email Cliente'], parse_decimal(x['Total Facturado con IVA (USD)'])), reverse=True)
    
    # Escribir CSV
    headers = [
        'Email Cliente', 'Nombre Cliente', 'Apellido Cliente', 'CUIT Cliente',
        'SKU', 'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
        'Número de Órdenes', 'Cantidad Cajas Total', 'Cantidad Unidades Total',
        'Precio Unitario Promedio', 'Precio Unitario Máximo', 'Precio Unitario Mínimo',
        'Precio Caja Promedio', 'FOB Unitario', 'Precio Plataforma Unitario',
        'Diferencia vs FOB', '% Diferencia vs FOB',
        'Diferencia vs Plataforma', '% Diferencia vs Plataforma',
        'Total Facturado (USD)', 'Total Facturado con IVA (USD)', 'Volumen Total (m³)',
        'Primera Compra', 'Última Compra',
    ]
    
    print(f"\n💾 Escribiendo CSV: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(analysis_data)
    
    print(f"   ✅ CSV generado: {OUTPUT_CSV}")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total combinaciones Cliente-Producto: {len(analysis_data)}")
    print(f"   Clientes únicos: {len(set(d['Email Cliente'] for d in analysis_data))}")
    print(f"   Productos únicos: {len(set(d['SKU'] for d in analysis_data))}")
    
    # Top clientes por número de productos
    productos_por_cliente = defaultdict(int)
    for d in analysis_data:
        productos_por_cliente[d['Email Cliente']] += 1
    
    top_clientes = sorted(productos_por_cliente.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\n   Top 5 clientes por variedad de productos:")
    for email, count in top_clientes:
        print(f"      {email}: {count} productos diferentes")


if __name__ == "__main__":
    print("🔄 Generando análisis Cliente-Producto...")
    generate_cliente_producto_analysis()
    print("\n✨ Proceso completado!")
