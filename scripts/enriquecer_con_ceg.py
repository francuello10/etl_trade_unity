#!/usr/bin/env python3
"""
Script para enriquecer el CSV limpio con datos del catálogo CEG.
Hace match por SKU y agrega: código CEG, brand_name, category_name, 
last_importation_date, base_price, fob.
"""

import csv
from typing import Dict, Optional
from datetime import datetime

# Archivos
CEG_CSV = "fuentes/Productos plataforma CEG_base price unit & fob_Tabla (2).csv"
INPUT_CSV = "ventas_historicas_items_limpio.csv"
OUTPUT_CSV = "ventas_historicas_items_limpio_con_ceg.csv"


def parse_date(date_str: str) -> str:
    """Convierte fecha del formato CEG a formato estándar."""
    if not date_str or date_str.lower() == "null":
        return ""
    
    date_str = str(date_str).strip()
    
    # Formato: "9 sept 2022, 21:00:00" o "12 sept 2025, 21:00:00"
    try:
        # Mapeo de meses en español
        meses = {
            "ene": "01", "jan": "01",
            "feb": "02", "feb": "02",
            "mar": "03", "mar": "03",
            "abr": "04", "apr": "04",
            "may": "05", "may": "05",
            "jun": "06", "jun": "06",
            "jul": "07", "jul": "07",
            "ago": "08", "aug": "08",
            "sep": "09", "sept": "09",
            "oct": "10", "oct": "10",
            "nov": "11", "nov": "11",
            "dic": "12", "dec": "12",
        }
        
        # Intentar parsear formato "9 sept 2022, 21:00:00"
        parts = date_str.split(",")
        if len(parts) >= 1:
            date_part = parts[0].strip()
            date_parts = date_part.split()
            if len(date_parts) >= 3:
                day = date_parts[0].zfill(2)
                month_str = date_parts[1].lower()[:3]
                year = date_parts[2]
                month = meses.get(month_str, "01")
                return f"{day}/{month}/{year}"
    except:
        pass
    
    return date_str


def load_ceg_catalog() -> Dict[str, Dict[str, str]]:
    """Carga el catálogo CEG y lo indexa por SKU."""
    catalog: Dict[str, Dict[str, str]] = {}
    
    print(f"📖 Cargando catálogo CEG desde: {CEG_CSV}")
    
    try:
        with open(CEG_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                sku = str(row.get("sku", "")).strip()
                if not sku:
                    continue
                
                # Normalizar SKU (mayúsculas, sin espacios extra)
                sku = sku.upper().strip()
                
                catalog[sku] = {
                    "code": str(row.get("code", "")).strip(),
                    "brand_name": str(row.get("brand_name", "")).strip(),
                    "category_name": str(row.get("category_name", "")).strip(),
                    "last_importation_date": parse_date(row.get("last_importation_date", "")),
                    "base_price": str(row.get("base_price", "")).strip(),
                    "fob": str(row.get("fob", "")).strip(),
                }
                count += 1
                
                # Si hay múltiples SKUs iguales, mantener el último (o podrías hacer merge)
                # Por ahora mantenemos el último encontrado
        print(f"   ✅ {count} productos cargados del catálogo CEG")
        
    except FileNotFoundError:
        print(f"   ⚠️  Archivo no encontrado: {CEG_CSV}")
        print("   Verificando ruta alternativa...")
        # Intentar sin el subdirectorio
        try:
            alt_path = "Productos plataforma CEG_base price unit & fob_Tabla (2).csv"
            with open(alt_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    sku = str(row.get("sku", "")).strip().upper()
                    if not sku:
                        continue
                    catalog[sku] = {
                        "code": str(row.get("code", "")).strip(),
                        "brand_name": str(row.get("brand_name", "")).strip(),
                        "category_name": str(row.get("category_name", "")).strip(),
                        "last_importation_date": parse_date(row.get("last_importation_date", "")),
                        "base_price": str(row.get("base_price", "")).strip(),
                        "fob": str(row.get("fob", "")).strip(),
                    }
                    count += 1
                print(f"   ✅ {count} productos cargados del catálogo CEG (ruta alternativa)")
        except FileNotFoundError:
            print(f"   ❌ No se pudo encontrar el archivo CEG")
            return {}
    
    return catalog


def enrich_csv():
    """Enriquece el CSV limpio con datos del catálogo CEG."""
    
    # Cargar catálogo CEG
    ceg_catalog = load_ceg_catalog()
    
    if not ceg_catalog:
        print("❌ No se pudo cargar el catálogo CEG. Abortando.")
        return
    
    # Leer CSV limpio
    print(f"\n📖 Leyendo CSV limpio: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Agregar nuevas columnas
    new_headers = list(headers) + [
        "Código CEG",
        "Brand Name CEG",
        "Categoría CEG",
        "Última Importación",
        "Base Price CEG",
        "FOB CEG"
    ]
    
    # Procesar filas
    matched_count = 0
    unmatched_skus = set()
    
    print(f"\n🔄 Enriqueciendo datos...")
    
    for row in rows:
        sku = str(row.get("SKU", "")).strip().upper()
        
        if sku and sku in ceg_catalog:
            ceg_data = ceg_catalog[sku]
            row["Código CEG"] = ceg_data["code"]
            row["Brand Name CEG"] = ceg_data["brand_name"]
            row["Categoría CEG"] = ceg_data["category_name"]
            row["Última Importación"] = ceg_data["last_importation_date"]
            row["Base Price CEG"] = ceg_data["base_price"]
            row["FOB CEG"] = ceg_data["fob"]
            matched_count += 1
        else:
            # Si no hay match, dejar vacío
            row["Código CEG"] = ""
            row["Brand Name CEG"] = ""
            row["Categoría CEG"] = ""
            row["Última Importación"] = ""
            row["Base Price CEG"] = ""
            row["FOB CEG"] = ""
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
    print(f"   SKUs con match en CEG: {matched_count} ({matched_count/len(rows)*100:.1f}%)")
    print(f"   SKUs sin match: {len(unmatched_skus)}")
    
    if unmatched_skus and len(unmatched_skus) <= 20:
        print(f"\n   SKUs sin match (primeros 20):")
        for sku in sorted(list(unmatched_skus))[:20]:
            print(f"      - {sku}")
    elif unmatched_skus:
        print(f"\n   SKUs sin match: {len(unmatched_skus)} (mostrando primeros 10)")
        for sku in sorted(list(unmatched_skus))[:10]:
            print(f"      - {sku}")


if __name__ == "__main__":
    print("🔄 Iniciando enriquecimiento con datos CEG...")
    enrich_csv()
    print("\n✨ Proceso completado!")
