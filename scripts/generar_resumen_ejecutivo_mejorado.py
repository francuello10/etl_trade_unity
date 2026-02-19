#!/usr/bin/env python3
"""
Script para generar resumen ejecutivo mejorado con análisis por trimestres.
Incluye: valores totales, análisis por año/trimestre, clientes únicos, promedio de orden.
"""

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from collections import defaultdict

# Archivos
VENTAS_CSV = "ventas_historicas_items.csv"
OUTPUT_CSV = "00_Resumen_Ejecutivo.csv"


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
        # Entero: solo punto para miles
        return f"{int(value):,}".replace(",", ".")
    else:
        # Decimal: punto para miles, coma para decimales
        formatted = f"{float(value):,.{decimals}f}"
        # Separar parte entera y decimal
        parts = formatted.split(".")
        if len(parts) == 2:
            integer_part = parts[0].replace(",", ".")
            decimal_part = parts[1]
            return f"{integer_part},{decimal_part}"
        else:
            return formatted.replace(",", ".")


def parse_date(date_str: str) -> date:
    """Parsea fecha en formato YYYY-MM-DD."""
    if not date_str or date_str == "":
        return None
    
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except:
        return None


def get_quarter(date_obj: date) -> str:
    """Obtiene trimestre de una fecha."""
    if not date_obj:
        return None
    quarter = (date_obj.month - 1) // 3 + 1
    return f"Q{quarter}"


def generate_improved_summary():
    """Genera resumen ejecutivo mejorado."""
    print("📖 Cargando datos de ventas...")
    
    rows = []
    
    with open(VENTAS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"   ✅ {len(rows)} filas cargadas")
    
    # Calcular métricas totales
    ordenes_unicas = set()
    clientes_unicos = set()
    total_items = len(rows)
    total_unidades = Decimal('0')
    total_facturado = Decimal('0')
    total_facturado_iva = Decimal('0')
    productos_unicos = set()
    marcas_unicas = set()
    categorias_unicas = set()
    volumen_total = Decimal('0')
    
    # Análisis por año y trimestre
    ventas_por_trimestre = defaultdict(lambda: {
        'ordenes': set(),
        'clientes': set(),
        'items': 0,
        'unidades': Decimal('0'),
        'facturado': Decimal('0'),
        'facturado_iva': Decimal('0'),
    })
    
    # Análisis por orden
    ordenes_data = defaultdict(lambda: {
        'fecha': None,
        'total': Decimal('0'),
        'cliente': '',
    })
    
    print("\n🔄 Calculando métricas...")
    
    for row in rows:
        # Métricas totales
        orden_id = row.get('Número de Orden', '').strip()
        cliente = row.get('Email Cliente', '').strip()
        sku = row.get('SKU', '').strip()
        marca = row.get('Brand Name CEG', '').strip()
        categoria = row.get('Categoría (2° Nivel)', '').strip()
        
        if orden_id:
            ordenes_unicas.add(orden_id)
        if cliente:
            clientes_unicos.add(cliente)
        if sku:
            productos_unicos.add(sku)
        if marca:
            marcas_unicas.add(marca)
        if categoria:
            categorias_unicas.add(categoria)
        
        total_unidades += parse_decimal(row.get('Cantidad Unitarias', ''))
        total_facturado += parse_decimal(row.get('Total Item', ''))
        total_facturado_iva += parse_decimal(row.get('Total Item con IVA', ''))
        volumen_total += parse_decimal(row.get('Volumen del Item', ''))
        
        # Análisis por trimestre
        fecha_creacion = parse_date(row.get('Fecha Creación', ''))
        if fecha_creacion:
            año = fecha_creacion.year
            trimestre = get_quarter(fecha_creacion)
            key = f"{año}-{trimestre}"
            
            ventas_por_trimestre[key]['ordenes'].add(orden_id)
            ventas_por_trimestre[key]['clientes'].add(cliente)
            ventas_por_trimestre[key]['items'] += 1
            ventas_por_trimestre[key]['unidades'] += parse_decimal(row.get('Cantidad Unitarias', ''))
            ventas_por_trimestre[key]['facturado'] += parse_decimal(row.get('Total Item', ''))
            ventas_por_trimestre[key]['facturado_iva'] += parse_decimal(row.get('Total Item con IVA', ''))
        
        # Datos por orden
        if orden_id:
            ordenes_data[orden_id]['fecha'] = fecha_creacion
            ordenes_data[orden_id]['total'] += parse_decimal(row.get('Total Item con IVA', ''))
            ordenes_data[orden_id]['cliente'] = cliente
    
    # Calcular promedio de orden
    totales_ordenes = [data['total'] for data in ordenes_data.values() if data['total'] > 0]
    promedio_orden = sum(totales_ordenes) / len(totales_ordenes) if totales_ordenes else Decimal('0')
    
    # Calcular márgenes promedio
    margenes_fob = [parse_decimal(r.get('% Margen sobre FOB', '')) for r in rows if r.get('% Margen sobre FOB')]
    margen_prom_fob = sum(margenes_fob) / len(margenes_fob) if margenes_fob else Decimal('0')
    
    margenes_plat = [parse_decimal(r.get('% Margen sobre Plataforma', '')) for r in rows if r.get('% Margen sobre Plataforma')]
    margen_prom_plat = sum(margenes_plat) / len(margenes_plat) if margenes_plat else Decimal('0')
    
    # Crear estructura de datos para el CSV
    summary_data = []
    
    # Fila de totales
    summary_data.append({
        'Métrica': 'TOTAL GENERAL',
        'Valor': '',
        '2024-Q1': '',
        '2024-Q2': '',
        '2024-Q3': '',
        '2024-Q4': '',
        '2025-Q1': '',
        '2025-Q2': '',
        '2025-Q3': '',
        '2025-Q4': '',
        '2026-Q1': '',
        '2026-Q2': '',
        '2026-Q3': '',
        '2026-Q4': '',
        'Incremental vs Año Anterior': '',
    })
    
    # Total Órdenes
    row_ordenes = {'Métrica': 'Total Órdenes', 'Valor': str(len(ordenes_unicas))}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            count = len(ventas_por_trimestre[key]['ordenes'])
            row_ordenes[key] = str(count) if count > 0 else ''
    
    # Calcular incremental
    total_2024 = sum(len(ventas_por_trimestre[f"2024-Q{q}"]['ordenes']) for q in [1,2,3,4])
    total_2025 = sum(len(ventas_por_trimestre[f"2025-Q{q}"]['ordenes']) for q in [1,2,3,4])
    if total_2024 > 0:
        incremental = ((total_2025 - total_2024) / total_2024 * 100)
        row_ordenes['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_ordenes['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_ordenes)
    
    # Total Items
    row_items = {'Métrica': 'Total Items Vendidos', 'Valor': str(total_items)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            count = ventas_por_trimestre[key]['items']
            row_items[key] = str(count) if count > 0 else ''
    
    total_items_2024 = sum(ventas_por_trimestre[f"2024-Q{q}"]['items'] for q in [1,2,3,4])
    total_items_2025 = sum(ventas_por_trimestre[f"2025-Q{q}"]['items'] for q in [1,2,3,4])
    if total_items_2024 > 0:
        incremental = ((total_items_2025 - total_items_2024) / total_items_2024 * 100)
        row_items['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_items['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_items)
    
    # Total Unidades
    row_unidades = {'Métrica': 'Total Unidades Vendidas', 'Valor': format_number_european(total_unidades, 0)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            unidades = ventas_por_trimestre[key]['unidades']
            row_unidades[key] = format_number_european(unidades, 0) if unidades > 0 else ''
    
    total_unidades_2024 = sum(ventas_por_trimestre[f"2024-Q{q}"]['unidades'] for q in [1,2,3,4])
    total_unidades_2025 = sum(ventas_por_trimestre[f"2025-Q{q}"]['unidades'] for q in [1,2,3,4])
    if total_unidades_2024 > 0:
        incremental = ((total_unidades_2025 - total_unidades_2024) / total_unidades_2024 * 100)
        row_unidades['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_unidades['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_unidades)
    
    # Total Facturado
    row_facturado = {'Métrica': 'Total Facturado (USD)', 'Valor': format_number_european(total_facturado, 2)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            facturado = ventas_por_trimestre[key]['facturado']
            row_facturado[key] = format_number_european(facturado, 2) if facturado > 0 else ''
    
    total_facturado_2024 = sum(ventas_por_trimestre[f"2024-Q{q}"]['facturado'] for q in [1,2,3,4])
    total_facturado_2025 = sum(ventas_por_trimestre[f"2025-Q{q}"]['facturado'] for q in [1,2,3,4])
    if total_facturado_2024 > 0:
        incremental = ((total_facturado_2025 - total_facturado_2024) / total_facturado_2024 * 100)
        row_facturado['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_facturado['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_facturado)
    
    # Total Facturado con IVA
    row_facturado_iva = {'Métrica': 'Total Facturado con IVA (USD)', 'Valor': format_number_european(total_facturado_iva, 2)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            facturado = ventas_por_trimestre[key]['facturado_iva']
            row_facturado_iva[key] = format_number_european(facturado, 2) if facturado > 0 else ''
    
    total_facturado_iva_2024 = sum(ventas_por_trimestre[f"2024-Q{q}"]['facturado_iva'] for q in [1,2,3,4])
    total_facturado_iva_2025 = sum(ventas_por_trimestre[f"2025-Q{q}"]['facturado_iva'] for q in [1,2,3,4])
    if total_facturado_iva_2024 > 0:
        incremental = ((total_facturado_iva_2025 - total_facturado_iva_2024) / total_facturado_iva_2024 * 100)
        row_facturado_iva['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_facturado_iva['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_facturado_iva)
    
    # Clientes Únicos
    row_clientes = {'Métrica': 'Clientes Únicos', 'Valor': str(len(clientes_unicos))}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            count = len(ventas_por_trimestre[key]['clientes'])
            row_clientes[key] = str(count) if count > 0 else ''
    
    clientes_2024 = len(set().union(*[ventas_por_trimestre[f"2024-Q{q}"]['clientes'] for q in [1,2,3,4]]))
    clientes_2025 = len(set().union(*[ventas_por_trimestre[f"2025-Q{q}"]['clientes'] for q in [1,2,3,4]]))
    if clientes_2024 > 0:
        incremental = ((clientes_2025 - clientes_2024) / clientes_2024 * 100)
        row_clientes['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_clientes['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_clientes)
    
    # Promedio de Orden
    row_promedio = {'Métrica': 'Promedio de Orden (USD)', 'Valor': format_number_european(promedio_orden, 2)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            key = f"{year}-Q{q}"
            ordenes = ventas_por_trimestre[key]['ordenes']
            facturado = ventas_por_trimestre[key]['facturado_iva']
            if len(ordenes) > 0:
                prom = facturado / len(ordenes)
                row_promedio[key] = format_number_european(prom, 2)
            else:
                row_promedio[key] = ''
    
    # Calcular promedio por año
    prom_2024 = total_facturado_iva_2024 / total_2024 if total_2024 > 0 else 0
    prom_2025 = total_facturado_iva_2025 / total_2025 if total_2025 > 0 else 0
    if prom_2024 > 0:
        incremental = ((prom_2025 - prom_2024) / prom_2024 * 100)
        row_promedio['Incremental vs Año Anterior'] = f"{incremental:.1f}%"
    else:
        row_promedio['Incremental vs Año Anterior'] = ''
    
    summary_data.append(row_promedio)
    
    # Productos Únicos
    row_productos = {'Métrica': 'Productos Únicos Vendidos', 'Valor': str(len(productos_unicos))}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_productos[f"{year}-Q{q}"] = ''
    row_productos['Incremental vs Año Anterior'] = ''
    summary_data.append(row_productos)
    
    # Marcas Únicas
    row_marcas = {'Métrica': 'Marcas Únicas', 'Valor': str(len(marcas_unicas))}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_marcas[f"{year}-Q{q}"] = ''
    row_marcas['Incremental vs Año Anterior'] = ''
    summary_data.append(row_marcas)
    
    # Categorías Únicas
    row_categorias = {'Métrica': 'Categorías Únicas', 'Valor': str(len(categorias_unicas))}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_categorias[f"{year}-Q{q}"] = ''
    row_categorias['Incremental vs Año Anterior'] = ''
    summary_data.append(row_categorias)
    
    # Margen Promedio FOB
    row_margen_fob = {'Métrica': 'Margen Promedio sobre FOB (%)', 'Valor': f"{margen_prom_fob:.2f}"}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_margen_fob[f"{year}-Q{q}"] = ''
    row_margen_fob['Incremental vs Año Anterior'] = ''
    summary_data.append(row_margen_fob)
    
    # Margen Promedio Plataforma
    row_margen_plat = {'Métrica': 'Margen Promedio sobre Plataforma (%)', 'Valor': f"{margen_prom_plat:.2f}"}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_margen_plat[f"{year}-Q{q}"] = ''
    row_margen_plat['Incremental vs Año Anterior'] = ''
    summary_data.append(row_margen_plat)
    
    # Volumen Total
    row_volumen = {'Métrica': 'Volumen Total (m³)', 'Valor': format_number_european(volumen_total, 2)}
    for year in [2024, 2025, 2026]:
        for q in [1, 2, 3, 4]:
            row_volumen[f"{year}-Q{q}"] = ''
    row_volumen['Incremental vs Año Anterior'] = ''
    summary_data.append(row_volumen)
    
    # Escribir CSV
    headers = ['Métrica', 'Valor', '2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4',
               '2025-Q1', '2025-Q2', '2025-Q3', '2025-Q4',
               '2026-Q1', '2026-Q2', '2026-Q3', '2026-Q4',
               'Incremental vs Año Anterior']
    
    print(f"\n💾 Escribiendo CSV: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(summary_data)
    
    print(f"   ✅ CSV generado: {OUTPUT_CSV}")
    
    print(f"\n📊 Resumen:")
    print(f"   Total órdenes: {len(ordenes_unicas)}")
    print(f"   Clientes únicos: {len(clientes_unicos)}")
    print(f"   Promedio de orden: ${promedio_orden:,.2f}")
    print(f"   Total facturado: ${total_facturado_iva:,.2f}")


if __name__ == "__main__":
    print("🔄 Generando resumen ejecutivo mejorado...")
    generate_improved_summary()
    print("\n✨ Proceso completado!")
