#!/usr/bin/env python3
"""
Script para:
1. Eliminar columnas innecesarias
2. Reordenar columnas (Código CEG y EAN pegadas a SKU)
3. Calcular Volumen del Item = Volumen (box) × Cantidad
4. Calcular días desde hoy para fechas de recepción e importación
5. Traer Categoría (2° Nivel) del catálogo TU
"""

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

# Archivos
TU_CSV = "fuentes/catalogo_trade_unity.csv"
INPUT_CSV = "inputs/ventas_historicas_items.csv"
OUTPUT_CSV = "inputs/ventas_historicas_items.csv"

# Columnas a ELIMINAR
COLUMNS_TO_REMOVE = [
    "Tipo Producto",
    "Precio con IVA",
    "Precio con IVA Unitario",
    "Descuento Orden",
    "Envío",
    "Impuesto Orden",
    "Marca",
]

# Columna de categoría a traer del catálogo TU
TU_CATEGORY_COLUMN = "Categoría (2° Nivel)"


def parse_decimal(value: str) -> Decimal:
    """Convierte string con formato europeo (coma decimal) a Decimal."""
    if not value or value == "":
        return Decimal("0")
    
    value_str = str(value).strip().replace("$", "").replace(" ", "")
    value_str = value_str.replace(",", ".")
    
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def format_decimal(value: Decimal, decimals: int = 4) -> str:
    """Formatea Decimal a string con formato europeo (coma decimal)."""
    if value == 0:
        return ""
    
    value = round(value, decimals)
    return str(value).replace(".", ",")


def parse_date(date_str: str) -> date:
    """Parsea fecha en formato YYYY-MM-DD a objeto date."""
    if not date_str or date_str == "":
        return None
    
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except:
        return None


def days_since_today(target_date: date) -> str:
    """Calcula días desde hoy hasta la fecha objetivo."""
    if not target_date:
        return ""
    
    today = date.today()
    delta = (today - target_date).days
    
    return str(delta)


def load_tu_categories() -> dict:
    """Carga categorías de segundo nivel del catálogo TU indexadas por SKU."""
    categories = {}
    
    print(f"📖 Cargando categorías desde: {TU_CSV}")
    
    try:
        with open(TU_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                sku = str(row.get("sku", "")).strip().upper()
                category = str(row.get(TU_CATEGORY_COLUMN, "")).strip()
                
                if sku and category:
                    categories[sku] = category
                    count += 1
        
        print(f"   ✅ {count} categorías cargadas")
        
    except FileNotFoundError:
        print(f"   ⚠️  Archivo no encontrado: {TU_CSV}")
        return {}
    except Exception as e:
        print(f"   ❌ Error cargando catálogo: {e}")
        return {}
    
    return categories


def clean_and_enrich():
    """Limpia, reordena y enriquece el CSV."""
    
    # Cargar categorías del catálogo TU
    tu_categories = load_tu_categories()
    
    print(f"\n📖 Leyendo CSV: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Eliminar columnas no deseadas
    print(f"\n🗑️  Eliminando columnas: {', '.join(COLUMNS_TO_REMOVE)}")
    
    for col in COLUMNS_TO_REMOVE:
        if col in headers:
            headers.remove(col)
    
    # Agregar nuevas columnas
    new_columns = [
        "Categoría (2° Nivel)",
        "Volumen del Item",
        "Días desde Última Recepción CEG",
        "Días desde Última Importación",
    ]
    
    for col in new_columns:
        if col not in headers:
            headers.append(col)
    
    # Definir orden lógico (con Código CEG y EAN pegadas a SKU)
    logical_order = [
        # 1. INFORMACIÓN DE ORDEN
        "Número de Orden",
        "Fecha Creación",
        "Fecha Actualización",
        "Estado",
        
        # 2. INFORMACIÓN DE CLIENTE
        "Email Cliente",
        "Nombre Cliente",
        "Apellido Cliente",
        "CUIT Cliente",
        
        # 3. INFORMACIÓN DE PRODUCTO (con Código CEG y EAN pegadas a SKU)
        "SKU",
        "Código CEG",
        "EAN",
        "Nombre Producto",
        "Cantidad",
        "Cantidad Unitarias",
        "Cantidad por Paquete Comercial",
        "Categoría (2° Nivel)",
        "Categoría CEG",
        "Brand Name CEG",
        "Tipo de Marca",
        
        # 4. PRECIOS POR CAJA
        "Precio Original",
        "Precio Venta",
        
        # 5. PRECIOS UNITARIOS
        "Precio Original Unitario",
        "Precio Venta Unitario",
        
        # 6. COSTOS
        "FOB CEG",
        "Base Price CEG",
        
        # 7. MÁRGENES
        "Margen sobre FOB",
        "% Margen sobre FOB",
        "Margen sobre Plataforma",
        "% Margen sobre Plataforma",
        
        # 8. VOLUMEN Y FECHAS
        "Volumen (box)",
        "Volumen del Item",
        "Fecha Última Recepción CEG",
        "Días desde Última Recepción CEG",
        "Última Importación",
        "Días desde Última Importación",
        
        # 9. DESCUENTOS Y TOTALES
        "Descuento Item",
        "Descuento % Item",
        "Total Item",
        "Total Item con IVA",
        "IVA % Item",
        "Impuesto Item",
        
        # 10. TOTALES DE ORDEN
        "Total Orden",
        "Subtotal Orden",
        
        # 11. INFORMACIÓN ADICIONAL
        "Moneda Orden",
        "Tasa Cambio",
        "Fecha Creación Magento",
        
        # 12. CAMPOS TÉCNICOS (al final)
        "ID Item",
        "ID Item Padre",
        "Categorías IDs",
        "Categorías",
    ]
    
    # Agregar columnas que no estén en el orden lógico
    all_columns = set(headers)
    ordered_columns = set(logical_order)
    missing_columns = sorted(list(all_columns - ordered_columns))
    
    # Orden final
    final_order = [col for col in logical_order if col in headers] + missing_columns
    
    print(f"\n🔄 Procesando datos...")
    
    calculated_volumen = 0
    calculated_dias = 0
    enriched_categories = 0
    
    for row in rows:
        # Eliminar columnas no deseadas
        for col in COLUMNS_TO_REMOVE:
            row.pop(col, None)
        
        # Enriquecer con categoría de segundo nivel
        sku = str(row.get("SKU", "")).strip().upper()
        if sku and sku in tu_categories:
            row["Categoría (2° Nivel)"] = tu_categories[sku]
            enriched_categories += 1
        else:
            row["Categoría (2° Nivel)"] = ""
        
        # Calcular Volumen del Item = Volumen (box) × Cantidad
        volumen_box_str = row.get("Volumen (box)", "").strip()
        cantidad_str = row.get("Cantidad", "").strip()
        
        if volumen_box_str and cantidad_str:
            try:
                volumen_box = parse_decimal(volumen_box_str)
                cantidad = parse_decimal(cantidad_str)
                
                if volumen_box > 0 and cantidad > 0:
                    volumen_item = volumen_box * cantidad
                    row["Volumen del Item"] = format_decimal(volumen_item, 6)
                    calculated_volumen += 1
                else:
                    row["Volumen del Item"] = ""
            except:
                row["Volumen del Item"] = ""
        else:
            row["Volumen del Item"] = ""
        
        # Calcular días desde última recepción CEG
        fecha_recepcion_str = row.get("Fecha Última Recepción CEG", "").strip()
        fecha_recepcion = parse_date(fecha_recepcion_str)
        if fecha_recepcion:
            row["Días desde Última Recepción CEG"] = days_since_today(fecha_recepcion)
            calculated_dias += 1
        else:
            row["Días desde Última Recepción CEG"] = ""
        
        # Calcular días desde última importación
        fecha_importacion_str = row.get("Última Importación", "").strip()
        fecha_importacion = parse_date(fecha_importacion_str)
        if fecha_importacion:
            row["Días desde Última Importación"] = days_since_today(fecha_importacion)
            calculated_dias += 1
        else:
            row["Días desde Última Importación"] = ""
    
    # Escribir CSV actualizado
    print(f"\n💾 Escribiendo CSV actualizado: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=final_order, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV actualizado generado")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total filas procesadas: {len(rows)}")
    print(f"   Columnas eliminadas: {len(COLUMNS_TO_REMOVE)}")
    print(f"   Categorías (2° Nivel) enriquecidas: {enriched_categories} ({enriched_categories/len(rows)*100:.1f}%)")
    print(f"   Volúmenes del Item calculados: {calculated_volumen} ({calculated_volumen/len(rows)*100:.1f}%)")
    print(f"   Días calculados: {calculated_dias} ({calculated_dias/(len(rows)*2)*100:.1f}% de fechas)")
    
    print(f"\n✨ Cambios realizados:")
    print(f"   - Columnas eliminadas: {len(COLUMNS_TO_REMOVE)}")
    print(f"   - Código CEG y EAN ahora están pegadas a SKU")
    print(f"   - Categoría (2° Nivel) agregada antes de Categoría CEG")
    print(f"   - Volumen del Item = Volumen (box) × Cantidad")
    print(f"   - Días desde hoy calculados para fechas de recepción e importación")


if __name__ == "__main__":
    print("🔄 Iniciando limpieza y enriquecimiento final...")
    clean_and_enrich()
    print("\n✨ Proceso completado!")
