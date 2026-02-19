#!/usr/bin/env python3
"""
Script para generar Excel completo de VENTAS con análisis por cliente detallado.
Incluye todas las hojas de análisis de ventas + nueva hoja de clientes.
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
OUTPUT_EXCEL = "EXCEL_COMPLETO_VENTAS_TradeUnity.xlsx"


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


def format_number(value, decimals=2):
    """Formatea número para mostrar."""
    if value == 0 or value == "":
        return 0
    return round(float(value), decimals)


def load_data():
    """Carga datos del CSV."""
    print(f"📖 Cargando datos de ventas desde: {VENTAS_CSV}")
    
    df = pd.read_csv(VENTAS_CSV, encoding='utf-8-sig')
    
    # Convertir columnas numéricas
    numeric_cols = [
        'Cantidad', 'Cantidad Unitarias', 'Cantidad por Paquete Comercial',
        'Precio Original', 'Precio Venta', 'Precio Original Unitario', 
        'Precio Venta Unitario', 'FOB CEG', 'Base Price CEG',
        'Margen sobre FOB', '% Margen sobre FOB', 
        'Margen sobre Plataforma', '% Margen sobre Plataforma',
        'Total Item', 'Total Item con IVA', 'Volumen del Item',
        'Días desde Última Recepción CEG', 'Días desde Última Importación'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    print(f"   ✅ {len(df)} filas cargadas")
    return df


def create_summary_sheet(df, writer):
    """Crea hoja de resumen ejecutivo."""
    print("📊 Creando Resumen Ejecutivo...")
    
    summary_data = {
        'Métrica': [
            'Total Órdenes',
            'Total Items Vendidos',
            'Total Unidades Vendidas',
            'Total Facturado (USD)',
            'Total Facturado con IVA (USD)',
            'Clientes Únicos',
            'Productos Únicos Vendidos',
            'Marcas Únicas',
            'Categorías Únicas',
            'Margen Promedio sobre FOB (%)',
            'Margen Promedio sobre Plataforma (%)',
            'Volumen Total (m³)',
            'Promedio de Orden (USD)',
        ],
        'Valor': [
            df['Número de Orden'].nunique(),
            len(df),
            df['Cantidad Unitarias'].sum(),
            df['Total Item'].sum(),
            df['Total Item con IVA'].sum(),
            df['Email Cliente'].nunique(),
            df['SKU'].nunique(),
            df['Brand Name CEG'].nunique(),
            df['Categoría (2° Nivel)'].nunique(),
            df['% Margen sobre FOB'].mean(),
            df['% Margen sobre Plataforma'].mean(),
            df['Volumen del Item'].sum(),
            df.groupby('Número de Orden')['Total Item con IVA'].sum().mean(),
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_df['Valor'] = summary_df['Valor'].apply(lambda x: format_number(x, 2))
    
    summary_df.to_excel(writer, sheet_name='00_Resumen Ejecutivo', index=False)
    
    worksheet = writer.sheets['00_Resumen Ejecutivo']
    worksheet.column_dimensions['A'].width = 40
    worksheet.column_dimensions['B'].width = 20


def create_ventas_sheet(df, writer):
    """Crea hoja con todas las ventas originales."""
    print("📊 Creando hoja de Ventas...")
    
    df_ventas = df.sort_values(['Número de Orden', 'Fecha Creación'])
    df_ventas.to_excel(writer, sheet_name='01_Ventas', index=False)
    
    worksheet = writer.sheets['01_Ventas']
    worksheet.column_dimensions['A'].width = 15
    worksheet.column_dimensions['I'].width = 15


def create_clientes_sheet(df, writer):
    """Crea hoja detallada de análisis por cliente."""
    print("📊 Creando análisis detallado por Cliente...")
    
    # Preparar datos por cliente
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
    
    df_clientes.to_excel(writer, sheet_name='03_Análisis por Cliente', index=False)
    
    # También crear resumen por cliente
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
    resumen_clientes.to_excel(writer, sheet_name='04_Resumen por Cliente', index=False)


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
    
    product_analysis.to_excel(writer, sheet_name='05_Por Producto', index=False)


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
    
    brand_analysis.to_excel(writer, sheet_name='06_Por Marca', index=False)


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
    
    category_analysis.to_excel(writer, sheet_name='07_Por Categoría', index=False)


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
    
    margin_fob_analysis.to_excel(writer, sheet_name='08_Márgenes FOB', index=False)
    margin_plat_analysis.to_excel(writer, sheet_name='09_Márgenes Plataforma', index=False)
    top_margin_fob.to_excel(writer, sheet_name='10_Top 20 Margen FOB', index=False)
    top_margin_plat.to_excel(writer, sheet_name='11_Top 20 Margen Plataforma', index=False)


def create_cliente_producto_sheet(df, writer):
    """Crea hoja de análisis desglosado por Cliente y Producto (SKU)."""
    print("📊 Creando análisis Cliente-Producto...")
    
    # Agrupar por cliente y SKU
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
    
    # Aplanar nombres de columnas
    cliente_producto.columns = [
        'Email Cliente', 'SKU', 'Nombre Cliente', 'Apellido Cliente', 'CUIT Cliente',
        'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
        'Número de Órdenes', 'Cantidad Cajas Total', 'Cantidad Unidades Total',
        'Precio Unitario Promedio', 'Precio Unitario Máximo', 'Precio Unitario Mínimo',
        'Precio Caja Promedio', 'FOB Unitario', 'Precio Plataforma Unitario',
        'Total Facturado (USD)', 'Total Facturado con IVA (USD)', 'Volumen Total (m³)',
        'Primera Compra', 'Última Compra'
    ]
    
    # Calcular diferencias y porcentajes
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
    
    # Reordenar columnas
    column_order = [
        'Email Cliente', 'Nombre Cliente', 'Apellido Cliente', 'CUIT Cliente',
        'SKU', 'Nombre Producto', 'Marca', 'Categoría (2° Nivel)', 'Categoría CEG',
        'Número de Órdenes', 'Cantidad Cajas Total', 'Cantidad Unidades Total',
        'Precio Unitario Promedio', 'Precio Unitario Máximo', 'Precio Unitario Mínimo',
        'Precio Caja Promedio', 'FOB Unitario', 'Precio Plataforma Unitario',
        'Diferencia vs FOB', '% Diferencia vs FOB',
        'Diferencia vs Plataforma', '% Diferencia vs Plataforma',
        'Total Facturado (USD)', 'Total Facturado con IVA (USD)', 'Volumen Total (m³)',
        'Primera Compra', 'Última Compra'
    ]
    
    cliente_producto = cliente_producto[column_order]
    
    # Ordenar por cliente y facturación
    cliente_producto = cliente_producto.sort_values(
        ['Email Cliente', 'Total Facturado con IVA (USD)'], 
        ascending=[True, False]
    )
    
    cliente_producto.to_excel(writer, sheet_name='02_Cliente Producto', index=False)


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
    
    top_facturacion.to_excel(writer, sheet_name='12_Top 50 Facturación', index=False)
    top_unidades.to_excel(writer, sheet_name='13_Top 50 Unidades', index=False)


def generate_complete_excel():
    """Genera Excel completo de ventas."""
    print("🔄 Generando Excel completo de VENTAS...")
    
    # Cargar datos
    df = load_data()
    
    # Crear archivo Excel
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Crear todas las hojas
        create_summary_sheet(df, writer)
        create_ventas_sheet(df, writer)
        create_cliente_producto_sheet(df, writer)  # Nueva hoja Cliente-Producto
        create_clientes_sheet(df, writer)
        create_by_product_sheet(df, writer)
        create_by_brand_sheet(df, writer)
        create_by_category_sheet(df, writer)
        create_margin_analysis_sheet(df, writer)
        create_top_products_sheet(df, writer)
    
    print(f"   ✅ Archivo Excel generado: {OUTPUT_EXCEL}")
    
    print(f"\n📋 Hojas creadas:")
    print(f"   00. Resumen Ejecutivo")
    print(f"   01. Ventas (datos originales)")
    print(f"   02. Cliente-Producto (DESGLOSADO por cliente y SKU)")
    print(f"   03. Análisis por Cliente (DETALLADO)")
    print(f"   04. Resumen por Cliente")
    print(f"   05. Por Producto")
    print(f"   06. Por Marca")
    print(f"   07. Por Categoría")
    print(f"   08. Márgenes FOB")
    print(f"   09. Márgenes Plataforma")
    print(f"   10. Top 20 Margen FOB")
    print(f"   11. Top 20 Margen Plataforma")
    print(f"   12. Top 50 Facturación")
    print(f"   13. Top 50 Unidades")


if __name__ == "__main__":
    if not HAS_PANDAS:
        print("Instalando pandas...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pandas", "openpyxl", "--break-system-packages"])
        import pandas as pd
    
    print("🔄 Iniciando generación de Excel completo de VENTAS...")
    generate_complete_excel()
    print("\n✨ Proceso completado!")
