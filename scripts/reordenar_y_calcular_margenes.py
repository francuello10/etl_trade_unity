#!/usr/bin/env python3
"""
Script para:
1. Reordenar columnas de forma lógica
2. Calcular márgenes sobre FOB y precio de plataforma
"""

import csv
from decimal import Decimal, InvalidOperation

# Archivos
INPUT_CSV = "ventas_historicas_items.csv"
OUTPUT_CSV = "ventas_historicas_items.csv"


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
    
    # Redondear a decimales especificados
    value = round(value, decimals)
    
    # Convertir a string y reemplazar punto por coma
    return str(value).replace(".", ",")


def format_percent(value: Decimal) -> str:
    """Formatea porcentaje."""
    if value == 0:
        return "0%"
    
    # Redondear a 2 decimales
    value = round(value, 2)
    return f"{value}%".replace(".", ",")


def reorder_and_calculate_margins():
    """Reordena columnas y calcula márgenes."""
    
    print(f"📖 Leyendo CSV: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Agregar columnas de márgenes a headers si no existen
    margin_columns = [
        "Margen sobre FOB",
        "% Margen sobre FOB",
        "Margen sobre Plataforma",
        "% Margen sobre Plataforma",
    ]
    for col in margin_columns:
        if col not in headers:
            headers.append(col)
    
    # Definir orden lógico de columnas
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
        
        # 3. INFORMACIÓN DE PRODUCTO
        "SKU",
        "Nombre Producto",
        "Cantidad",
        "Cantidad por Paquete Comercial",
        "Tipo Producto",
        "Categoría CEG",
        "Brand Name CEG",
        "Tipo de Marca",
        "Código CEG",
        "EAN",
        
        # 4. PRECIOS POR CAJA (Magento)
        "Precio Original",
        "Precio Venta",
        "Precio con IVA",
        
        # 5. PRECIOS UNITARIOS (Calculados)
        "Precio Original Unitario",
        "Precio Venta Unitario",
        "Precio con IVA Unitario",
        
        # 6. COSTOS
        "FOB CEG",
        "Base Price CEG",
        
        # 7. MÁRGENES (Nuevos cálculos)
        "Margen sobre FOB",
        "% Margen sobre FOB",
        "Margen sobre Plataforma",
        "% Margen sobre Plataforma",
        
        # 8. DESCUENTOS Y TOTALES
        "Descuento Item",
        "Descuento % Item",
        "Total Item",
        "Total Item con IVA",
        "IVA % Item",
        "Impuesto Item",
        
        # 9. TOTALES DE ORDEN
        "Total Orden",
        "Subtotal Orden",
        "Descuento Orden",
        "Envío",
        "Impuesto Orden",
        
        # 10. INFORMACIÓN ADICIONAL
        "Moneda Orden",
        "Tasa Cambio",
        "Volumen (box)",
        "Fecha Creación Magento",
        "Fecha Última Recepción CEG",
        "Última Importación",
        
        # 11. CAMPOS TÉCNICOS (al final)
        "ID Item",
        "ID Item Padre",
        "Categorías IDs",
        "Categorías",
        "Marca",
    ]
    
    # Agregar columnas que no estén en el orden lógico
    all_columns = set(headers)
    ordered_columns = set(logical_order)
    missing_columns = sorted(list(all_columns - ordered_columns))
    
    # Orden final: las ordenadas + las que faltan
    final_order = [col for col in logical_order if col in headers] + missing_columns
    
    print(f"\n🔄 Calculando márgenes...")
    
    calculated_count = 0
    skipped_count = 0
    
    for row in rows:
        # Obtener valores necesarios
        precio_venta_unit = parse_decimal(row.get("Precio Venta Unitario", ""))
        fob_ceg = parse_decimal(row.get("FOB CEG", ""))
        base_price_ceg = parse_decimal(row.get("Base Price CEG", ""))
        
        # Calcular margen sobre FOB
        if precio_venta_unit > 0 and fob_ceg > 0:
            margen_fob = precio_venta_unit - fob_ceg
            pct_margen_fob = (margen_fob / fob_ceg) * 100 if fob_ceg > 0 else Decimal("0")
            
            row["Margen sobre FOB"] = format_decimal(margen_fob, 4)
            row["% Margen sobre FOB"] = format_percent(pct_margen_fob)
            calculated_count += 1
        else:
            row["Margen sobre FOB"] = ""
            row["% Margen sobre FOB"] = ""
            skipped_count += 1
        
        # Calcular margen sobre Plataforma (Base Price CEG)
        if precio_venta_unit > 0 and base_price_ceg > 0:
            margen_plataforma = precio_venta_unit - base_price_ceg
            pct_margen_plataforma = (margen_plataforma / base_price_ceg) * 100 if base_price_ceg > 0 else Decimal("0")
            
            row["Margen sobre Plataforma"] = format_decimal(margen_plataforma, 4)
            row["% Margen sobre Plataforma"] = format_percent(pct_margen_plataforma)
        else:
            row["Margen sobre Plataforma"] = ""
            row["% Margen sobre Plataforma"] = ""
    
    # Escribir CSV reordenado
    print(f"\n💾 Escribiendo CSV reordenado: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=final_order, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV reordenado generado")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total filas procesadas: {len(rows)}")
    print(f"   Márgenes calculados: {calculated_count} ({calculated_count/len(rows)*100:.1f}%)")
    print(f"   Filas sin datos suficientes: {skipped_count} ({skipped_count/len(rows)*100:.1f}%)")
    
    print(f"\n✨ Nuevas columnas agregadas:")
    print(f"   - Margen sobre FOB (Precio Venta Unitario - FOB CEG)")
    print(f"   - % Margen sobre FOB")
    print(f"   - Margen sobre Plataforma (Precio Venta Unitario - Base Price CEG)")
    print(f"   - % Margen sobre Plataforma")
    
    print(f"\n📋 Columnas reordenadas en orden lógico:")
    print(f"   1. Información de Orden")
    print(f"   2. Información de Cliente")
    print(f"   3. Información de Producto")
    print(f"   4. Precios por Caja")
    print(f"   5. Precios Unitarios")
    print(f"   6. Costos (FOB, Base Price)")
    print(f"   7. Márgenes (sobre FOB y Plataforma)")
    print(f"   8. Descuentos y Totales")
    print(f"   9. Información Adicional")


if __name__ == "__main__":
    print("🔄 Iniciando reordenamiento y cálculo de márgenes...")
    reorder_and_calculate_margins()
    print("\n✨ Proceso completado!")
