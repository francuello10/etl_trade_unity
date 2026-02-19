#!/usr/bin/env python3
"""
Script para:
1. Formatear fechas a formato estándar (YYYY-MM-DD) para cálculos
2. Enriquecer con datos del catálogo TU.csv
"""

import csv
import re
from datetime import datetime
from typing import Dict, Optional

# Archivos
TU_CSV = "fuentes/catalogo_trade_unity.csv"
INPUT_CSV = "inputs/ventas_historicas_items.csv"
OUTPUT_CSV = "inputs/ventas_historicas_items.csv"

# Columnas a traer del catálogo TU
TU_COLUMNS = {
    "Fecha de Creación (Magento)": "Fecha Creación Magento",
    "Cantidad por Paquete Comercial": "Cantidad por Paquete Comercial",
    "EAN": "EAN",
    "Tipo de Marca": "Tipo de Marca",
    "Fecha de última recepción CEG": "Fecha Última Recepción CEG",
    "Volumen (box)": "Volumen (box)",
}


def parse_date_to_standard(date_str: str) -> str:
    """Convierte fecha a formato estándar YYYY-MM-DD para cálculos en Excel/Sheets."""
    if not date_str or date_str.lower() in ["null", ""]:
        return ""
    
    date_str = str(date_str).strip()
    
    # Formato actual: "22/07/2024 18:43" o "07/09/2024"
    try:
        # Intentar formato "DD/MM/YYYY HH:MM" o "DD/MM/YYYY"
        if " " in date_str:
            date_part = date_str.split()[0]
        else:
            date_part = date_str
        
        # Parsear DD/MM/YYYY
        parts = date_part.split("/")
        if len(parts) == 3:
            day, month, year = parts
            # Validar y formatear
            if len(year) == 2:
                year = "20" + year if int(year) < 50 else "19" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    
    # Intentar otros formatos comunes
    formats_to_try = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    
    # Si no se puede parsear, devolver original
    return date_str


def parse_tu_date(date_str: str) -> str:
    """Parsea fechas del formato TU (ej: "12/1/02, 8:06 PM" o "7/20/24, 1:00 PM")."""
    if not date_str or date_str.lower() in ["null", ""]:
        return ""
    
    date_str = str(date_str).strip()
    
    # Formato TU: "12/1/02, 8:06 PM" o "7/20/24, 1:00 PM"
    try:
        # Separar fecha y hora
        if "," in date_str:
            date_part = date_str.split(",")[0].strip()
        else:
            date_part = date_str
        
        # Parsear M/D/YY o MM/DD/YY
        parts = date_part.split("/")
        if len(parts) == 3:
            month, day, year = parts
            # Ajustar año
            if len(year) == 2:
                year_int = int(year)
                year = f"20{year}" if year_int < 50 else f"19{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    
    return ""


def load_tu_catalog() -> Dict[str, Dict[str, str]]:
    """Carga el catálogo TU y lo indexa por SKU."""
    catalog: Dict[str, Dict[str, str]] = {}
    
    print(f"📖 Cargando catálogo TU desde: {TU_CSV}")
    
    try:
        with open(TU_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                sku = str(row.get("sku", "")).strip().upper()
                if not sku:
                    continue
                
                # Extraer las columnas necesarias
                catalog[sku] = {
                    "Fecha Creación Magento": parse_tu_date(row.get("Fecha de Creación (Magento)", "")),
                    "Cantidad por Paquete Comercial": str(row.get("Cantidad por Paquete Comercial", "")).strip(),
                    "EAN": str(row.get("EAN", "")).strip(),
                    "Tipo de Marca": str(row.get("Tipo de Marca", "")).strip(),
                    "Fecha Última Recepción CEG": parse_tu_date(row.get("Fecha de última recepción CEG", "")),
                    "Volumen (box)": str(row.get("Volumen (box)", "")).strip(),
                }
                count += 1
                
        print(f"   ✅ {count} productos cargados del catálogo TU")
        
    except FileNotFoundError:
        print(f"   ⚠️  Archivo no encontrado: {TU_CSV}")
        return {}
    except Exception as e:
        print(f"   ❌ Error cargando catálogo: {e}")
        return {}
    
    return catalog


def enrich_and_format_dates():
    """Enriquece el CSV con datos TU y formatea fechas."""
    
    # Cargar catálogo TU
    tu_catalog = load_tu_catalog()
    
    if not tu_catalog:
        print("❌ No se pudo cargar el catálogo TU. Abortando.")
        return
    
    # Leer CSV final
    print(f"\n📖 Leyendo CSV final: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Agregar nuevas columnas al final
    new_headers = list(headers) + list(TU_COLUMNS.values())
    
    # Columnas de fecha a formatear
    date_columns = [
        "Fecha Creación",
        "Fecha Actualización",
        "Última Importación",
    ]
    
    # Procesar filas
    matched_count = 0
    unmatched_skus = set()
    
    print(f"\n🔄 Procesando datos...")
    
    for row in rows:
        # Formatear fechas existentes
        for date_col in date_columns:
            if date_col in row:
                row[date_col] = parse_date_to_standard(row.get(date_col, ""))
        
        # Enriquecer con datos TU
        sku = str(row.get("SKU", "")).strip().upper()
        
        if sku and sku in tu_catalog:
            tu_data = tu_catalog[sku]
            row["Fecha Creación Magento"] = tu_data["Fecha Creación Magento"]
            row["Cantidad por Paquete Comercial"] = tu_data["Cantidad por Paquete Comercial"]
            row["EAN"] = tu_data["EAN"]
            row["Tipo de Marca"] = tu_data["Tipo de Marca"]
            row["Fecha Última Recepción CEG"] = tu_data["Fecha Última Recepción CEG"]
            row["Volumen (box)"] = tu_data["Volumen (box)"]
            matched_count += 1
        else:
            # Si no hay match, dejar vacío
            row["Fecha Creación Magento"] = ""
            row["Cantidad por Paquete Comercial"] = ""
            row["EAN"] = ""
            row["Tipo de Marca"] = ""
            row["Fecha Última Recepción CEG"] = ""
            row["Volumen (box)"] = ""
            if sku:
                unmatched_skus.add(sku)
    
    # Escribir CSV enriquecido
    print(f"\n💾 Escribiendo CSV enriquecido: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=new_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"   ✅ CSV enriquecido generado")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total filas procesadas: {len(rows)}")
    print(f"   SKUs con match en TU: {matched_count} ({matched_count/len(rows)*100:.1f}%)")
    print(f"   SKUs sin match: {len(unmatched_skus)}")
    
    print(f"\n📅 Fechas formateadas a formato estándar (YYYY-MM-DD):")
    print(f"   - Fecha Creación")
    print(f"   - Fecha Actualización")
    print(f"   - Última Importación")
    print(f"   - Fecha Creación Magento (nueva)")
    print(f"   - Fecha Última Recepción CEG (nueva)")
    print(f"\n   💡 Ahora podés usar fórmulas como: =HOY()-A2 (donde A2 es la celda con la fecha)")
    
    if unmatched_skus and len(unmatched_skus) <= 20:
        print(f"\n   SKUs sin match en TU (primeros 20):")
        for sku in sorted(list(unmatched_skus))[:20]:
            print(f"      - {sku}")
    elif unmatched_skus:
        print(f"\n   SKUs sin match: {len(unmatched_skus)} (mostrando primeros 10)")
        for sku in sorted(list(unmatched_skus))[:10]:
            print(f"      - {sku}")


if __name__ == "__main__":
    print("🔄 Iniciando enriquecimiento con catálogo TU y formateo de fechas...")
    enrich_and_format_dates()
    print("\n✨ Proceso completado!")
