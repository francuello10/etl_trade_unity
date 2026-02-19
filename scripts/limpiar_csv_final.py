#!/usr/bin/env python3
"""
Script para limpiar el CSV final:
- Elimina columnas innecesarias
- Formatea CUIT sin guiones
- Formatea dinero sin signos, sin puntos, solo coma decimal
"""

import csv
import re
from decimal import Decimal, InvalidOperation

# Archivos
INPUT_CSV = "ventas_historicas_items_limpio_con_ceg.csv"
OUTPUT_CSV = "ventas_historicas_items.csv"

# Columnas a ELIMINAR
COLUMNS_TO_REMOVE = [
    "ID Orden",
    "Moneda Base",
]

# Columnas de DINERO (formatear sin $, sin puntos, solo coma decimal)
MONEY_COLUMNS = [
    "Total Orden",
    "Subtotal Orden",
    "Descuento Orden",
    "Envío",
    "Impuesto Orden",
    "Precio Original",
    "Precio Venta",
    "Precio con IVA",
    "Descuento Item",
    "Total Item",
    "Total Item con IVA",
    "Impuesto Item",
    "Base Price CEG",
    "FOB CEG",
]


def format_money(value: str) -> str:
    """Formatea dinero: sin signos, sin puntos, solo coma decimal."""
    if not value or value == "":
        return ""
    
    # Quitar signos $, espacios, comas
    value_str = str(value).replace("$", "").replace(",", "").replace(" ", "").strip()
    
    # Si está vacío después de limpiar
    if not value_str or value_str == "-":
        return ""
    
    try:
        # Convertir a decimal
        num = Decimal(value_str)
        
        # Formato: sin puntos para miles, coma para decimales
        # Ejemplo: 1234.56 -> "1234,56"
        num_str = str(num)
        
        # Si tiene punto decimal, reemplazar por coma
        if "." in num_str:
            num_str = num_str.replace(".", ",")
        
        return num_str
    except (InvalidOperation, ValueError):
        return value_str


def format_cuit(cuit: str) -> str:
    """Formatea CUIT: solo números, sin guiones."""
    if not cuit:
        return ""
    
    # Quitar guiones y espacios, dejar solo números
    cuit_clean = re.sub(r'[^\d]', '', str(cuit))
    return cuit_clean


def analyze_columns(rows: list, headers: list) -> dict:
    """Analiza las columnas para sugerir eliminaciones."""
    suggestions = {
        "always_empty": [],
        "always_same": [],
        "duplicates": [],
    }
    
    # Analizar cada columna
    for header in headers:
        if header in COLUMNS_TO_REMOVE:
            continue
        
        values = [str(row.get(header, "")).strip() for row in rows if row.get(header)]
        unique_values = set(values)
        
        # Si siempre está vacío
        if len(unique_values) == 0 or (len(unique_values) == 1 and "" in unique_values):
            suggestions["always_empty"].append(header)
        
        # Si siempre tiene el mismo valor
        elif len(unique_values) == 1:
            suggestions["always_same"].append((header, list(unique_values)[0]))
    
    # Detectar duplicados potenciales
    if "Marca" in headers and "Brand Name CEG" in headers:
        suggestions["duplicates"].append(("Marca", "Brand Name CEG", "Considerar mantener solo una"))
    
    if "Categorías" in headers and "Categoría CEG" in headers:
        suggestions["duplicates"].append(("Categorías", "Categoría CEG", "Considerar mantener solo una"))
    
    return suggestions


def clean_csv():
    """Limpia el CSV según especificaciones."""
    
    print("📖 Leyendo CSV...")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    print(f"   ✅ {len(headers)} columnas encontradas")
    
    # Analizar columnas para sugerencias
    print("\n🔍 Analizando columnas...")
    suggestions = analyze_columns(rows, headers)
    
    # Crear nuevas headers (sin las columnas a eliminar)
    new_headers = [h for h in headers if h not in COLUMNS_TO_REMOVE]
    
    print(f"\n🗑️  Eliminando columnas: {', '.join(COLUMNS_TO_REMOVE)}")
    
    # Procesar filas
    print("\n🔄 Procesando datos...")
    
    for row in rows:
        # Eliminar columnas no deseadas
        for col in COLUMNS_TO_REMOVE:
            row.pop(col, None)
        
        # Formatear CUIT
        if "CUIT Cliente" in row:
            row["CUIT Cliente"] = format_cuit(row.get("CUIT Cliente", ""))
        
        # Formatear columnas de dinero
        for col in MONEY_COLUMNS:
            if col in row:
                row[col] = format_money(row.get(col, ""))
    
    # Escribir CSV limpio
    print(f"\n💾 Escribiendo CSV limpio: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=new_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV limpio generado")
    
    # Mostrar sugerencias
    print(f"\n📊 Análisis de columnas:")
    print(f"   Columnas finales: {len(new_headers)}")
    
    if suggestions["always_empty"]:
        print(f"\n   ⚠️  Columnas siempre vacías (considerar eliminar):")
        for col in suggestions["always_empty"]:
            print(f"      - {col}")
    
    if suggestions["always_same"]:
        print(f"\n   ℹ️  Columnas con valor constante:")
        for col, value in suggestions["always_same"][:5]:  # Mostrar solo primeras 5
            value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"      - {col}: '{value_preview}'")
        if len(suggestions["always_same"]) > 5:
            print(f"      ... y {len(suggestions['always_same']) - 5} más")
    
    if suggestions["duplicates"]:
        print(f"\n   🔄 Columnas potencialmente duplicadas:")
        for col1, col2, note in suggestions["duplicates"]:
            print(f"      - {col1} vs {col2}: {note}")
    
    print(f"\n✨ Proceso completado!")
    print(f"\n💡 Sugerencias adicionales:")
    print(f"   - 'ID Item Padre': Generalmente vacío, podría eliminarse")
    print(f"   - 'Categorías IDs': Solo IDs numéricos, menos útil que nombres")
    print(f"   - 'Tasa Cambio': Si siempre es USD, podría no ser necesario")
    print(f"   - 'Marca' vs 'Brand Name CEG': Considerar mantener solo 'Brand Name CEG'")
    print(f"   - 'Categorías' vs 'Categoría CEG': Considerar mantener solo 'Categoría CEG'")


if __name__ == "__main__":
    print("🔄 Iniciando limpieza del CSV...")
    clean_csv()
