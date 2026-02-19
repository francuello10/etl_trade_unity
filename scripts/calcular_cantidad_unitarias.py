#!/usr/bin/env python3
"""
Script para calcular cantidad unitarias a partir de cantidad de cajas.
Cantidad Unitarias = Cantidad (cajas) × Cantidad por Paquete Comercial
"""

import csv
from decimal import Decimal, InvalidOperation

# Archivos
INPUT_CSV = "ventas_historicas_items_FINAL.csv"
OUTPUT_CSV = "ventas_historicas_items_FINAL.csv"


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


def format_decimal(value: Decimal, decimals: int = 0) -> str:
    """Formatea Decimal a string con formato europeo (coma decimal)."""
    if value == 0:
        return ""
    
    # Redondear a decimales especificados
    value = round(value, decimals)
    
    # Si es entero, mostrar sin decimales
    if decimals == 0:
        return str(int(value))
    
    # Convertir a string y reemplazar punto por coma
    return str(value).replace(".", ",")


def calculate_unit_quantities():
    """Calcula cantidad unitarias multiplicando cantidad de cajas por cantidad por paquete."""
    
    print(f"📖 Leyendo CSV: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Agregar columna "Cantidad Unitarias" después de "Cantidad"
    if "Cantidad Unitarias" not in headers:
        # Encontrar posición de "Cantidad"
        try:
            cantidad_idx = headers.index("Cantidad")
            headers.insert(cantidad_idx + 1, "Cantidad Unitarias")
        except ValueError:
            # Si no encuentra "Cantidad", agregar al final
            headers.append("Cantidad Unitarias")
    
    # Estadísticas
    calculated_count = 0
    skipped_count = 0
    
    print(f"\n🔄 Calculando cantidades unitarias...")
    
    for row in rows:
        # Obtener cantidad de cajas y cantidad por paquete
        cantidad_cajas_str = row.get("Cantidad", "").strip()
        cantidad_paquete_str = row.get("Cantidad por Paquete Comercial", "").strip()
        
        if not cantidad_cajas_str or cantidad_cajas_str == "":
            row["Cantidad Unitarias"] = ""
            skipped_count += 1
            continue
        
        if not cantidad_paquete_str or cantidad_paquete_str == "":
            row["Cantidad Unitarias"] = ""
            skipped_count += 1
            continue
        
        try:
            cantidad_cajas = parse_decimal(cantidad_cajas_str)
            cantidad_paquete = parse_decimal(cantidad_paquete_str)
            
            if cantidad_cajas == 0 or cantidad_paquete == 0:
                row["Cantidad Unitarias"] = ""
                skipped_count += 1
                continue
            
            # Calcular: Cantidad Unitarias = Cantidad (cajas) × Cantidad por Paquete
            cantidad_unitarias = cantidad_cajas * cantidad_paquete
            
            # Guardar en formato entero (sin decimales)
            row["Cantidad Unitarias"] = format_decimal(cantidad_unitarias, 0)
            
            calculated_count += 1
            
        except Exception as e:
            row["Cantidad Unitarias"] = ""
            skipped_count += 1
    
    # Escribir CSV actualizado
    print(f"\n💾 Escribiendo CSV actualizado: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV actualizado generado")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total filas procesadas: {len(rows)}")
    print(f"   Cantidades unitarias calculadas: {calculated_count} ({calculated_count/len(rows)*100:.1f}%)")
    print(f"   Filas sin datos suficientes: {skipped_count} ({skipped_count/len(rows)*100:.1f}%)")
    
    print(f"\n✨ Nueva columna agregada:")
    print(f"   - Cantidad Unitarias (Cantidad cajas × Cantidad por Paquete Comercial)")
    
    print(f"\n💡 Ejemplo:")
    print(f"   Si vendiste 2 cajas de un producto que viene 100 unidades por caja:")
    print(f"   Cantidad Unitarias = 2 × 100 = 200 unidades")


if __name__ == "__main__":
    print("🔄 Iniciando cálculo de cantidades unitarias...")
    calculate_unit_quantities()
    print("\n✨ Proceso completado!")
