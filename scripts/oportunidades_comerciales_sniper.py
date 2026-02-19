#!/usr/bin/env python3
"""
Oportunidades Comerciales Tipo Sniper - Trade Unity

Análisis para identificar oportunidades de venta puntual:
1. Clientes que "barren stock" - compraron significativamente SKUs que ahora están en stock 0
2. Clientes que compraron fuerte un SKU y ahora hay stock nuevo disponible
3. Oportunidades de precio - clientes que compraron más barato que precio actual publicado

Genera Excel con oportunidades comerciales accionables para el equipo de ventas.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import os

try:
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# Archivos
VENTAS_CSV = "inputs/ventas_historicas_items_FINAL.csv"
STOCK_ERP = "fuentes/stock erp.csv"
CATALOGO_TU = "fuentes/Catalogo TU.csv"
PUBLICACIONES_CSV = "fuentes/Publicaciones de productos.csv"
OUTPUT_DIR = "outputs"
OUTPUT_EXCEL = f"{OUTPUT_DIR}/TradeUnity Oportunidades Comerciales Sniper.xlsx"


def parse_decimal(value: str) -> float:
    """Convierte string a float."""
    if not value or value == "" or pd.isna(value):
        return 0.0
    
    value_str = str(value).strip().replace("$", "").replace(" ", "").replace("%", "")
    value_str = value_str.replace(",", ".")
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return 0.0


def auto_adjust_column_widths(writer, sheet_name, df):
    """Ajusta automáticamente el ancho de las columnas en Excel."""
    try:
        worksheet = writer.sheets[sheet_name]
        
        for idx, col in enumerate(df.columns, 1):
            column_letter = worksheet.cell(row=1, column=idx).column_letter
            try:
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            except:
                # Si hay problemas con una columna, usar ancho por defecto
                worksheet.column_dimensions[column_letter].width = 15
    except Exception as e:
        print(f"   ⚠️  No se pudo ajustar columnas en {sheet_name}: {e}")


def load_ventas():
    """Carga datos de ventas."""
    print("📖 Cargando datos de ventas...")
    
    if not os.path.exists(VENTAS_CSV):
        print(f"   ⚠️  Archivo de ventas no encontrado: {VENTAS_CSV}")
        return pd.DataFrame()
    
    df = pd.read_csv(VENTAS_CSV, encoding='utf-8-sig')
    
    # Convertir fechas
    if 'Fecha Creación' in df.columns:
        df['Fecha Creación'] = pd.to_datetime(df['Fecha Creación'], errors='coerce')
    
    # Convertir numéricos
    numeric_cols = [
        'Cantidad Unitarias', 'Total Item con IVA', 'Precio Venta Unitario',
        'Precio Original', 'Precio Venta', 'FOB CEG', 'Base Price CEG'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('$', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    print(f"   ✅ {len(df)} registros de ventas cargados")
    return df


def load_stock():
    """Carga stock actual del ERP."""
    print("📖 Cargando stock del ERP...")
    
    if not os.path.exists(STOCK_ERP):
        print(f"   ⚠️  Archivo de stock no encontrado: {STOCK_ERP}")
        return pd.DataFrame()
    
    df = pd.read_csv(STOCK_ERP, encoding='utf-8-sig')
    
    # Limpiar y convertir
    df['Pronosticado con pendiente'] = pd.to_numeric(
        df['Pronosticado con pendiente'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0)
    
    df['Box Qty'] = pd.to_numeric(
        df['Box Qty'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    ).fillna(1)
    
    # Calcular unidades
    df['Stock Unidades'] = df['Pronosticado con pendiente'] * df['Box Qty']
    
    print(f"   ✅ {len(df)} productos con stock cargados")
    return df


def load_catalog():
    """Carga catálogo TU para obtener rubro y marca."""
    print("📖 Cargando catálogo TU...")
    
    if not os.path.exists(CATALOGO_TU):
        print(f"   ⚠️  Archivo de catálogo no encontrado: {CATALOGO_TU}")
        return pd.DataFrame()
    
    df = pd.read_csv(CATALOGO_TU, encoding='utf-8-sig')
    
    print(f"   ✅ {len(df)} productos en catálogo")
    return df


def load_precios_actuales():
    """Carga precios actuales (liquidación enero/febrero 2026)."""
    print("📖 Cargando precios actuales (liquidación enero/febrero 2026)...")
    
    if not os.path.exists(PUBLICACIONES_CSV):
        print(f"   ⚠️  Archivo de publicaciones no encontrado: {PUBLICACIONES_CSV}")
        return pd.DataFrame()
    
    df = pd.read_csv(PUBLICACIONES_CSV, encoding='utf-8-sig')
    
    # Obtener precio actual (última columna: liquidación enero/febrero 2026)
    precio_col = 'Precio LIQUIDACION ENERO/FEBRERO 2026  unitario neto'
    
    if precio_col in df.columns:
        df['Precio Actual Publicado'] = pd.to_numeric(
            df[precio_col].astype(str).str.replace(',', '.').str.replace('$', '').str.strip(),
            errors='coerce'
        ).fillna(0)
    else:
        # Si no existe, buscar la última columna de precio
        precio_cols = [col for col in df.columns if 'Precio' in col and 'unitario' in col.lower()]
        if precio_cols:
            ultima_col = precio_cols[-1]
            df['Precio Actual Publicado'] = pd.to_numeric(
                df[ultima_col].astype(str).str.replace(',', '.').str.replace('$', '').str.strip(),
                errors='coerce'
            ).fillna(0)
        else:
            df['Precio Actual Publicado'] = 0
    
    print(f"   ✅ Precios actuales cargados")
    return df[['sku', 'Precio Actual Publicado']]


def analizar_clientes_barren_stock(ventas_df, stock_df, catalog_df):
    """
    Identifica clientes que compraron significativamente SKUs que ahora están en stock 0.
    Estos son clientes con capacidad de "limpiar stocks".
    """
    print("🎯 Analizando clientes que barren stock...")
    
    # Obtener SKUs en stock 0
    stock_cero = stock_df[stock_df['Stock Unidades'] == 0].copy()
    skus_stock_cero = set(stock_cero['D365 Reference'].str.upper().str.strip())
    
    # Agregar SKU desde catálogo si no está en stock
    if 'sku' in catalog_df.columns and 'Código de Producto (D365)' in catalog_df.columns:
        catalog_sku_map = dict(zip(
            catalog_df['Código de Producto (D365)'].str.upper().str.strip(),
            catalog_df['sku'].str.upper().str.strip()
        ))
        skus_adicionales = set()
        for d365_ref in list(skus_stock_cero):  # Convertir a lista para evitar modificar durante iteración
            if d365_ref in catalog_sku_map:
                skus_adicionales.add(catalog_sku_map[d365_ref])
        skus_stock_cero.update(skus_adicionales)
    
    # Filtrar ventas de SKUs que ahora están en stock 0
    ventas_df['SKU_Upper'] = ventas_df['SKU'].str.upper().str.strip()
    ventas_stock_cero = ventas_df[ventas_df['SKU_Upper'].isin(skus_stock_cero)].copy()
    
    if len(ventas_stock_cero) == 0:
        print("   ⚠️  No se encontraron ventas de SKUs en stock 0")
        return pd.DataFrame()
    
    # Agrupar por cliente y SKU para identificar compras significativas
    # "Significativo" = percentil 75 de unidades compradas por SKU
    umbral_significativo = ventas_stock_cero.groupby('SKU')['Cantidad Unitarias'].quantile(0.75)
    
    # También calcular mediana para identificar compradores fuertes
    mediana_por_sku = ventas_stock_cero.groupby('SKU')['Cantidad Unitarias'].median()
    
    oportunidades = []
    
    for (email, sku), group in ventas_stock_cero.groupby(['Email Cliente', 'SKU']):
        total_unidades = group['Cantidad Unitarias'].sum()
        total_facturacion = group['Total Item con IVA'].sum()
        ultima_compra = group['Fecha Creación'].max()
        num_ordenes = group['Número de Orden'].nunique()
        precio_promedio = group['Precio Venta Unitario'].mean()
        
        # Obtener umbral para este SKU
        umbral = umbral_significativo.get(sku, 0)
        mediana = mediana_por_sku.get(sku, 0)
        
        # Si compró más que el umbral O más que la mediana x 2, es una oportunidad
        # Mínimo 50 unidades para considerar "significativo"
        if total_unidades >= max(umbral, mediana * 2, 50):
            # Obtener info del producto
            producto_info = group.iloc[0]
            
            # Calcular capacidad de compra (unidades promedio por orden)
            capacidad_compra = total_unidades / num_ordenes if num_ordenes > 0 else total_unidades
            
            oportunidades.append({
                'Email Cliente': email,
                'Nombre Cliente': producto_info.get('Nombre Cliente', ''),
                'SKU': sku,
                'Nombre Producto': producto_info.get('Nombre Producto', ''),
                'Categoría (2° Nivel)': producto_info.get('Categoría (2° Nivel)', ''),
                'Brand Name CEG': producto_info.get('Brand Name CEG', ''),
                'Total Unidades Compradas': total_unidades,
                'Unidades Promedio por Orden': capacidad_compra,
                'Total Facturación Histórica (USD)': total_facturacion,
                'Precio Promedio Histórico (USD)': precio_promedio,
                'Número de Órdenes': num_ordenes,
                'Última Compra': ultima_compra,
                'Días desde Última Compra': (datetime.now() - ultima_compra).days if pd.notna(ultima_compra) else None,
                'Stock Actual': 0,
                'Tipo Oportunidad': 'Barre Stock',
                'Prioridad': 'ALTA' if total_unidades >= 200 else 'MEDIA',
                'Mensaje Comercial': f"Cliente compró {int(total_unidades)} unidades. SKU ahora en stock 0. Oportunidad de liquidación o reposición."
            })
    
    df_oportunidades = pd.DataFrame(oportunidades)
    
    if len(df_oportunidades) > 0:
        # Ordenar por unidades compradas (descendente)
        df_oportunidades = df_oportunidades.sort_values('Total Unidades Compradas', ascending=False)
        print(f"   ✅ {len(df_oportunidades)} oportunidades de clientes que barren stock identificadas")
    else:
        print("   ⚠️  No se encontraron oportunidades de clientes que barren stock")
    
    return df_oportunidades


def analizar_stock_nuevo_recompra(ventas_df, stock_df, catalog_df):
    """
    Identifica clientes que compraron fuerte un SKU y ahora hay stock nuevo disponible.
    Oportunidad de recompra.
    """
    print("🎯 Analizando oportunidades de recompra (stock nuevo)...")
    
    # Obtener SKUs con stock disponible (>0)
    stock_disponible = stock_df[stock_df['Stock Unidades'] > 0].copy()
    skus_con_stock = set(stock_disponible['D365 Reference'].str.upper().str.strip())
    
    # Agregar SKU desde catálogo
    if 'sku' in catalog_df.columns and 'Código de Producto (D365)' in catalog_df.columns:
        catalog_sku_map = dict(zip(
            catalog_df['Código de Producto (D365)'].str.upper().str.strip(),
            catalog_df['sku'].str.upper().str.strip()
        ))
        skus_adicionales = set()
        for d365_ref in list(skus_con_stock):  # Convertir a lista para evitar modificar durante iteración
            if d365_ref in catalog_sku_map:
                skus_adicionales.add(catalog_sku_map[d365_ref])
        skus_con_stock.update(skus_adicionales)
    
    # Filtrar ventas de SKUs que ahora tienen stock
    ventas_df['SKU_Upper'] = ventas_df['SKU'].str.upper().str.strip()
    ventas_con_stock = ventas_df[ventas_df['SKU_Upper'].isin(skus_con_stock)].copy()
    
    if len(ventas_con_stock) == 0:
        print("   ⚠️  No se encontraron ventas de SKUs con stock disponible")
        return pd.DataFrame()
    
    # Agrupar por cliente y SKU
    # "Compró fuerte" = percentil 75 de unidades compradas por SKU
    umbral_fuerte = ventas_con_stock.groupby('SKU')['Cantidad Unitarias'].quantile(0.75)
    mediana_por_sku = ventas_con_stock.groupby('SKU')['Cantidad Unitarias'].median()
    
    # Merge con stock actual
    stock_map = dict(zip(
        stock_disponible['D365 Reference'].str.upper().str.strip(),
        stock_disponible['Stock Unidades']
    ))
    
    oportunidades = []
    
    for (email, sku), group in ventas_con_stock.groupby(['Email Cliente', 'SKU']):
        total_unidades = group['Cantidad Unitarias'].sum()
        total_facturacion = group['Total Item con IVA'].sum()
        ultima_compra = group['Fecha Creación'].max()
        num_ordenes = group['Número de Orden'].nunique()
        precio_promedio = group['Precio Venta Unitario'].mean()
        
        # Obtener umbral para este SKU
        umbral = umbral_fuerte.get(sku, 0)
        mediana = mediana_por_sku.get(sku, 0)
        
        # Si compró más que el umbral O más que la mediana x 2, es una oportunidad
        if total_unidades >= max(umbral, mediana * 2, 50):  # Mínimo 50 unidades
            # Obtener stock actual
            stock_actual = stock_map.get(sku, 0)
            
            # Obtener info del producto
            producto_info = group.iloc[0]
            
            # Calcular capacidad de compra
            capacidad_compra = total_unidades / num_ordenes if num_ordenes > 0 else total_unidades
            
            # Potencial de venta (mínimo entre stock disponible y capacidad histórica)
            potencial_venta = min(stock_actual, capacidad_compra * 1.2)  # 20% más que promedio histórico
            
            oportunidades.append({
                'Email Cliente': email,
                'Nombre Cliente': producto_info.get('Nombre Cliente', ''),
                'SKU': sku,
                'Nombre Producto': producto_info.get('Nombre Producto', ''),
                'Categoría (2° Nivel)': producto_info.get('Categoría (2° Nivel)', ''),
                'Brand Name CEG': producto_info.get('Brand Name CEG', ''),
                'Total Unidades Compradas Histórico': total_unidades,
                'Unidades Promedio por Orden': capacidad_compra,
                'Stock Actual Disponible': stock_actual,
                'Potencial de Venta (Unidades)': potencial_venta,
                'Total Facturación Histórica (USD)': total_facturacion,
                'Precio Promedio Histórico (USD)': precio_promedio,
                'Número de Órdenes': num_ordenes,
                'Última Compra': ultima_compra,
                'Días desde Última Compra': (datetime.now() - ultima_compra).days if pd.notna(ultima_compra) else None,
                'Tipo Oportunidad': 'Stock Nuevo - Recompra',
                'Prioridad': 'ALTA' if total_unidades >= 200 and stock_actual >= 100 else 'MEDIA',
                'Mensaje Comercial': f"Cliente compró {int(total_unidades)} unidades históricamente. Stock nuevo disponible: {int(stock_actual)} unidades. Oportunidad de recompra."
            })
    
    df_oportunidades = pd.DataFrame(oportunidades)
    
    if len(df_oportunidades) > 0:
        # Ordenar por unidades compradas (descendente)
        df_oportunidades = df_oportunidades.sort_values('Total Unidades Compradas Histórico', ascending=False)
        print(f"   ✅ {len(df_oportunidades)} oportunidades de recompra identificadas")
    else:
        print("   ⚠️  No se encontraron oportunidades de recompra")
    
    return df_oportunidades


def analizar_oportunidades_precio(ventas_df, precios_df):
    """
    Identifica clientes que compraron un producto a precio más barato que el precio actual publicado.
    Oportunidad de venta con precio atractivo.
    """
    print("🎯 Analizando oportunidades de precio...")
    
    # Merge ventas con precios actuales
    ventas_df['SKU_Upper'] = ventas_df['SKU'].str.upper().str.strip()
    precios_df['sku_upper'] = precios_df['sku'].str.upper().str.strip()
    
    ventas_con_precio = ventas_df.merge(
        precios_df[['sku_upper', 'Precio Actual Publicado']],
        left_on='SKU_Upper',
        right_on='sku_upper',
        how='inner'
    )
    
    # Filtrar solo productos con precio actual > 0
    ventas_con_precio = ventas_con_precio[ventas_con_precio['Precio Actual Publicado'] > 0]
    
    if len(ventas_con_precio) == 0:
        print("   ⚠️  No se encontraron ventas con precios actuales")
        return pd.DataFrame()
    
    # Identificar compras donde precio histórico < precio actual
    # Esto significa que compró más barato, ahora puede comprar al precio actual (más caro) o negociar
    ventas_con_precio['Precio Histórico Unitario'] = ventas_con_precio['Precio Venta Unitario']
    ventas_con_precio['Diferencia Precio'] = ventas_con_precio['Precio Actual Publicado'] - ventas_con_precio['Precio Histórico Unitario']
    ventas_con_precio['% Diferencia'] = (ventas_con_precio['Diferencia Precio'] / ventas_con_precio['Precio Histórico Unitario'] * 100).fillna(0)
    
    # Filtrar: compró más barato que precio actual (diferencia > 0)
    oportunidades_precio = ventas_con_precio[ventas_con_precio['Diferencia Precio'] > 0].copy()
    
    if len(oportunidades_precio) == 0:
        print("   ⚠️  No se encontraron oportunidades de precio")
        return pd.DataFrame()
    
    # Agrupar por cliente y SKU
    oportunidades = []
    
    for (email, sku), group in oportunidades_precio.groupby(['Email Cliente', 'SKU']):
        total_unidades = group['Cantidad Unitarias'].sum()
        total_facturacion = group['Total Item con IVA'].sum()
        ultima_compra = group['Fecha Creación'].max()
        precio_historico_promedio = group['Precio Histórico Unitario'].mean()
        precio_actual = group['Precio Actual Publicado'].iloc[0]
        diferencia_pct = group['% Diferencia'].mean()
        
        # Obtener info del producto
        producto_info = group.iloc[0]
        
        # Calcular ahorro potencial si compra al precio histórico
        ahorro_potencial = (precio_actual - precio_historico_promedio) * total_unidades
        
        oportunidades.append({
            'Email Cliente': email,
            'Nombre Cliente': producto_info.get('Nombre Cliente', ''),
            'SKU': sku,
            'Nombre Producto': producto_info.get('Nombre Producto', ''),
            'Categoría (2° Nivel)': producto_info.get('Categoría (2° Nivel)', ''),
            'Brand Name CEG': producto_info.get('Brand Name CEG', ''),
            'Total Unidades Compradas': total_unidades,
            'Precio Histórico Promedio (USD)': precio_historico_promedio,
            'Precio Actual Publicado (USD)': precio_actual,
            'Diferencia Precio (USD)': precio_actual - precio_historico_promedio,
            '% Diferencia Precio': diferencia_pct,
            'Ahorro Potencial si Precio Histórico (USD)': ahorro_potencial,
            'Total Facturación Histórica (USD)': total_facturacion,
            'Última Compra': ultima_compra,
            'Días desde Última Compra': (datetime.now() - ultima_compra).days if pd.notna(ultima_compra) else None,
            'Tipo Oportunidad': 'Oportunidad Precio',
            'Prioridad': 'ALTA' if diferencia_pct > 20 else 'MEDIA',
            'Mensaje Comercial': f"Cliente compró a ${precio_historico_promedio:.2f} USD. Precio actual: ${precio_actual:.2f} USD ({diferencia_pct:.1f}% más caro). Oportunidad de negociación o mantener precio histórico."
        })
    
    df_oportunidades = pd.DataFrame(oportunidades)
    
    if len(df_oportunidades) > 0:
        # Ordenar por diferencia de precio (descendente)
        df_oportunidades = df_oportunidades.sort_values('% Diferencia Precio', ascending=False)
        print(f"   ✅ {len(df_oportunidades)} oportunidades de precio identificadas")
    else:
        print("   ⚠️  No se encontraron oportunidades de precio")
    
    return df_oportunidades


def generar_resumen_por_rubro_marca(df_oportunidades):
    """Genera resumen de oportunidades por rubro y marca."""
    if len(df_oportunidades) == 0:
        return pd.DataFrame()
    
    # Identificar columna de unidades (puede tener nombres diferentes)
    unidades_col = None
    for col in ['Total Unidades Compradas', 'Total Unidades Compradas Histórico']:
        if col in df_oportunidades.columns:
            unidades_col = col
            break
    
    if unidades_col is None:
        print("   ⚠️  No se encontró columna de unidades")
        return pd.DataFrame()
    
    resumen = df_oportunidades.groupby(['Categoría (2° Nivel)', 'Brand Name CEG']).agg({
        'Email Cliente': 'nunique',
        'SKU': 'nunique',
        unidades_col: 'sum',
        'Total Facturación Histórica (USD)': 'sum'
    }).reset_index()
    
    resumen.columns = [
        'Categoría (2° Nivel)',
        'Brand Name CEG',
        'Clientes Únicos',
        'SKUs Únicos',
        'Total Unidades',
        'Total Facturación (USD)'
    ]
    
    resumen = resumen.sort_values('Total Facturación (USD)', ascending=False)
    
    return resumen


def generate_sniper_report():
    """Genera reporte completo de oportunidades comerciales tipo sniper."""
    print("🚀 Generando Reporte de Oportunidades Comerciales Sniper...")
    print("=" * 70)
    
    # Cargar datos
    ventas_df = load_ventas()
    stock_df = load_stock()
    catalog_df = load_catalog()
    precios_df = load_precios_actuales()
    
    if len(ventas_df) == 0:
        print("❌ No hay datos de ventas. Abortando.")
        return
    
    # Análisis 1: Clientes que barren stock
    oportunidades_barren = analizar_clientes_barren_stock(ventas_df, stock_df, catalog_df)
    
    # Análisis 2: Stock nuevo - recompra
    oportunidades_recompra = analizar_stock_nuevo_recompra(ventas_df, stock_df, catalog_df)
    
    # Análisis 3: Oportunidades de precio
    oportunidades_precio = analizar_oportunidades_precio(ventas_df, precios_df)
    
    # Crear Excel
    print(f"\n💾 Creando archivo Excel: {OUTPUT_EXCEL}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Hoja 1: Resumen Ejecutivo
        todas_oportunidades = pd.concat([
            oportunidades_barren,
            oportunidades_recompra,
            oportunidades_precio
        ], ignore_index=True)
        
        resumen_data = {
            'Métrica': [
                'Clientes que Barren Stock',
                'Oportunidades de Recompra (Stock Nuevo)',
                'Oportunidades de Precio',
                '',
                'Total Oportunidades Únicas',
                'Total Clientes Únicos',
                'Total SKUs Únicos',
                '',
                '⚠️ NOTA IMPORTANTE',
                '',
                'Este análisis identifica oportunidades comerciales tipo "sniper" para venta puntual.',
                'Los datos de stock son del momento actual. No tenemos historial de stock durante el tiempo.',
                'Las oportunidades se basan en:',
                '1. Clientes que compraron significativamente SKUs que ahora están en stock 0',
                '2. Clientes que compraron fuerte un SKU y ahora hay stock nuevo disponible',
                '3. Clientes que compraron a precio más barato que el actual publicado (liquidación enero/febrero 2026)'
            ],
            'Cantidad': [
                len(oportunidades_barren),
                len(oportunidades_recompra),
                len(oportunidades_precio),
                '',
                len(todas_oportunidades.drop_duplicates(subset=['Email Cliente', 'SKU'])),
                len(todas_oportunidades['Email Cliente'].unique()),
                len(todas_oportunidades['SKU'].unique()),
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                ''
            ]
        }
        resumen_df = pd.DataFrame(resumen_data)
        resumen_df.to_excel(writer, sheet_name='00_Resumen Ejecutivo', index=False)
        auto_adjust_column_widths(writer, '00_Resumen Ejecutivo', resumen_df)
        
        # Hoja 2: Clientes que Barren Stock
        if len(oportunidades_barren) > 0:
            oportunidades_barren.to_excel(writer, sheet_name='01_Barren Stock', index=False)
            auto_adjust_column_widths(writer, '01_Barren Stock', oportunidades_barren)
            
            # Resumen por rubro y marca
            resumen_barren = generar_resumen_por_rubro_marca(oportunidades_barren)
            if len(resumen_barren) > 0:
                resumen_barren.to_excel(writer, sheet_name='02_Resumen Barren Stock (Rubro-Marca)', index=False)
                auto_adjust_column_widths(writer, '02_Resumen Barren Stock (Rubro-Marca)', resumen_barren)
        
        # Hoja 3: Stock Nuevo - Recompra
        if len(oportunidades_recompra) > 0:
            oportunidades_recompra.to_excel(writer, sheet_name='03_Stock Nuevo Recompra', index=False)
            auto_adjust_column_widths(writer, '03_Stock Nuevo Recompra', oportunidades_recompra)
            
            # Resumen por rubro y marca
            resumen_recompra = generar_resumen_por_rubro_marca(oportunidades_recompra)
            if len(resumen_recompra) > 0:
                resumen_recompra.to_excel(writer, sheet_name='04_Resumen Recompra (Rubro-Marca)', index=False)
                auto_adjust_column_widths(writer, '04_Resumen Recompra (Rubro-Marca)', resumen_recompra)
        
        # Hoja 4: Oportunidades de Precio
        if len(oportunidades_precio) > 0:
            oportunidades_precio.to_excel(writer, sheet_name='05_Oportunidades Precio', index=False)
            auto_adjust_column_widths(writer, '05_Oportunidades Precio', oportunidades_precio)
        
        # Hoja 5: Todas las Oportunidades (Vista Sniper)
        if len(todas_oportunidades) > 0:
            # Ordenar por prioridad y facturación histórica
            todas_oportunidades['Prioridad_Num'] = todas_oportunidades['Prioridad'].map({'ALTA': 1, 'MEDIA': 2, 'BAJA': 3})
            todas_oportunidades = todas_oportunidades.sort_values(['Prioridad_Num', 'Total Facturación Histórica (USD)'], ascending=[True, False])
            todas_oportunidades = todas_oportunidades.drop('Prioridad_Num', axis=1)
            
            todas_oportunidades.to_excel(writer, sheet_name='06_Todas Oportunidades Sniper', index=False)
            auto_adjust_column_widths(writer, '06_Todas Oportunidades Sniper', todas_oportunidades)
    
    print(f"\n✅ Reporte generado: {OUTPUT_EXCEL}")
    print(f"\n📊 Resumen:")
    print(f"   - Clientes que barren stock: {len(oportunidades_barren)}")
    print(f"   - Oportunidades de recompra: {len(oportunidades_recompra)}")
    print(f"   - Oportunidades de precio: {len(oportunidades_precio)}")
    print(f"   - Total oportunidades: {len(todas_oportunidades)}")


if __name__ == "__main__":
    if not HAS_OPENPYXL:
        print("❌ Error: openpyxl no está instalado. Ejecuta: pip install openpyxl")
        exit(1)
    
    generate_sniper_report()
