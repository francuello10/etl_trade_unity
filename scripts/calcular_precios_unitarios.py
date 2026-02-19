#!/usr/bin/env python3
"""
Script para calcular precios unitarios a partir de precios por caja de Magento.
Divide los precios de Magento por "Cantidad por Paquete Comercial" para obtener precios unitarios.
"""

import csv
from decimal import Decimal, InvalidOperation

# Archivos
INPUT_CSV = "ventas_historicas_items_FINAL.csv"
OUTPUT_CSV = "ventas_historicas_items_FINAL.csv"

# Columnas de precios por CAJA (de Magento) que hay que convertir a unitarios
PRECIOS_POR_CAJA = [
    "Precio Original",
    "Precio Venta",
    "Precio con IVA",
]

# Columna con la cantidad por paquete comercial
COL_CANTIDAD_PAQUETE = "Cantidad por Paquete Comercial"


def parse_decimal(value: str) -> Decimal:
    """Convierte string con formato europeo (coma decimal) a Decimal."""
    if not value or value == "":
        return Decimal("0")
    
    # Limpiar: quitar espacios, signos, etc.
    value_str = str(value).strip().replace("$", "").replace(" ", "")
    
    # Reemplazar coma por punto para Decimal
    value_str = value_str.replace(",", ".")
    
    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def format_decimal(value: Decimal) -> str:
    """Formatea Decimal a string con formato europeo (coma decimal)."""
    if value == 0:
        return ""
    
    # Convertir a string y reemplazar punto por coma
    return str(value).replace(".", ",")


def calculate_unit_prices():
    """Calcula precios unitarios dividiendo precios por caja por cantidad por paquete."""
    
    print(f"📖 Leyendo CSV: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Agregar nuevas columnas para precios unitarios
    new_columns = [
        "Precio Original Unitario",
        "Precio Venta Unitario",
        "Precio con IVA Unitario",
    ]
    
    new_headers = list(headers) + new_columns
    
    # Estadísticas
    calculated_count = 0
    skipped_count = 0
    errors = []
    
    print(f"\n🔄 Calculando precios unitarios...")
    
    for row in rows:
        # Obtener cantidad por paquete comercial
        cantidad_paquete_str = row.get(COL_CANTIDAD_PAQUETE, "").strip()
        
        if not cantidad_paquete_str or cantidad_paquete_str == "":
            # Si no hay cantidad por paquete, dejar vacío
            for col in new_columns:
                row[col] = ""
            skipped_count += 1
            continue
        
        try:
            cantidad_paquete = parse_decimal(cantidad_paquete_str)
            
            if cantidad_paquete == 0:
                # No se puede dividir por cero
                for col in new_columns:
                    row[col] = ""
                skipped_count += 1
                continue
            
            # Calcular precios unitarios
            precio_original_caja = parse_decimal(row.get("Precio Original", ""))
            precio_venta_caja = parse_decimal(row.get("Precio Venta", ""))
            precio_iva_caja = parse_decimal(row.get("Precio con IVA", ""))
            
            # Dividir por cantidad por paquete
            precio_original_unit = precio_original_caja / cantidad_paquete if precio_original_caja else Decimal("0")
            precio_venta_unit = precio_venta_caja / cantidad_paquete if precio_venta_caja else Decimal("0")
            precio_iva_unit = precio_iva_caja / cantidad_paquete if precio_iva_caja else Decimal("0")
            
            # Guardar en formato europeo
            row["Precio Original Unitario"] = format_decimal(precio_original_unit)
            row["Precio Venta Unitario"] = format_decimal(precio_venta_unit)
            row["Precio con IVA Unitario"] = format_decimal(precio_iva_unit)
            
            calculated_count += 1
            
        except Exception as e:
            # Si hay error, dejar vacío
            for col in new_columns:
                row[col] = ""
            skipped_count += 1
            errors.append(f"SKU {row.get('SKU', 'N/A')}: {str(e)}")
    
    # Escribir CSV con precios unitarios
    print(f"\n💾 Escribiendo CSV con precios unitarios: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=new_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV actualizado generado")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total filas procesadas: {len(rows)}")
    print(f"   Precios unitarios calculados: {calculated_count} ({calculated_count/len(rows)*100:.1f}%)")
    print(f"   Filas sin cantidad por paquete: {skipped_count} ({skipped_count/len(rows)*100:.1f}%)")
    
    if errors and len(errors) <= 10:
        print(f"\n   ⚠️  Errores encontrados (primeros 10):")
        for error in errors[:10]:
            print(f"      - {error}")
    elif errors:
        print(f"\n   ⚠️  {len(errors)} errores encontrados (mostrando primeros 5):")
        for error in errors[:5]:
            print(f"      - {error}")
    
    print(f"\n✨ Nuevas columnas agregadas:")
    for col in new_columns:
        print(f"   - {col}")
    
    print(f"\n💡 Nota: Los precios unitarios se calcularon dividiendo los precios por caja")
    print(f"   por la 'Cantidad por Paquete Comercial' del catálogo TU.")


if __name__ == "__main__":
    print("🔄 Iniciando cálculo de precios unitarios...")
    calculate_unit_prices()
    print("\n✨ Proceso completado!")
