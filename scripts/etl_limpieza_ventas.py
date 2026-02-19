#!/usr/bin/env python3
"""
Script de ETL y limpieza de datos de ventas históricas.
- Propaga datos de orden a todas las líneas de la misma orden
- Limpia y formatea datos para spreadsheet
- Normaliza formatos de fechas, números, CUIT, etc.
"""

import csv
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal, InvalidOperation

# Archivos
INPUT_CSV = "ventas_historicas_items_raw.csv"
OUTPUT_CSV = "ventas_historicas_items_limpio.csv"

# Campos que pertenecen a la ORDEN (se propagan a todas las líneas)
ORDER_FIELDS = [
    "increment_id", "entity_id", "created_at", "updated_at", "status",
    "customer_email", "customer_firstname", "customer_lastname", "customer_taxvat",
    "order_currency_code", "base_currency_code", "currency_rate",
    "grand_total", "subtotal", "discount_amount_order", "shipping_amount", "tax_amount_order",
]

# Campos que pertenecen al ITEM (únicos por línea)
ITEM_FIELDS = [
    "item_id", "parent_item_id", "product_type", "sku", "name", "qty_ordered",
    "original_price", "price", "price_incl_tax",
    "discount_amount_item", "discount_percent_item",
    "row_total", "row_total_incl_tax",
    "tax_percent_item", "tax_amount_item",
]

# Campos adicionales si existe el CSV enriquecido
ENRICHED_FIELDS = ["category_ids", "category_names", "brand"]


def normalize_cuit(cuit: str) -> str:
    """Normaliza CUIT: quita guiones y espacios, valida formato."""
    if not cuit:
        return ""
    cuit = str(cuit).strip().replace("-", "").replace(" ", "")
    # Si tiene formato XX-XXXXXXXX-X, lo normaliza a XXXXXXXXXXX
    if len(cuit) == 11 and cuit.isdigit():
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"
    return cuit


def normalize_date(date_str: str) -> str:
    """Normaliza fecha: YYYY-MM-DD HH:MM:SS -> DD/MM/YYYY HH:MM"""
    if not date_str:
        return ""
    try:
        # Intenta parsear formato Magento: "2024-07-22 18:43:31"
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str


def normalize_number(value: Any, decimals: int = 2) -> str:
    """Normaliza número: quita decimales innecesarios, formatea."""
    if value is None or value == "":
        return ""
    try:
        num = Decimal(str(value))
        if decimals == 0:
            return str(int(num))
        return f"{num:.{decimals}f}".rstrip("0").rstrip(".")
    except (InvalidOperation, ValueError):
        return str(value)


def normalize_percent(value: Any) -> str:
    """Normaliza porcentaje: agrega % si no lo tiene."""
    if not value or value == "" or value == "0":
        return "0%"
    try:
        num = float(str(value))
        if num == 0:
            return "0%"
        return f"{num:.2f}%".rstrip("0").rstrip(".").rstrip("%") + "%"
    except:
        return str(value)


def normalize_status(status: str) -> str:
    """Normaliza estado de orden a español legible."""
    status_map = {
        "closed": "Cerrada",
        "complete": "Completa",
        "processing": "Procesando",
        "pending": "Pendiente",
        "canceled": "Cancelada",
        "Entregado": "Entregado",
        "delivered": "Entregado",
    }
    status = str(status).strip()
    return status_map.get(status.lower(), status.title())


def clean_text(text: str) -> str:
    """Limpia texto: quita espacios extra, normaliza."""
    if not text:
        return ""
    return " ".join(str(text).strip().split())


def format_currency(value: Any, currency: str = "USD") -> str:
    """Formatea moneda con símbolo."""
    if not value or value == "":
        return ""
    try:
        num = float(str(value))
        if currency.upper() == "USD":
            return f"${num:,.2f}"
        elif currency.upper() == "ARS":
            return f"${num:,.2f}"
        else:
            return f"{num:,.2f} {currency}"
    except:
        return str(value)


def process_csv():
    """Procesa el CSV: propaga datos de orden y limpia."""
    
    # Detectar si existe CSV enriquecido
    try:
        with open("ventas_historicas_items_enriched.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            has_enriched = True
            enriched_headers = reader.fieldnames
    except FileNotFoundError:
        has_enriched = False
        enriched_headers = None
    
    input_file = "ventas_historicas_items_enriched.csv" if has_enriched else INPUT_CSV
    
    # Leer CSV
    rows: List[Dict[str, str]] = []
    with open(input_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    
    if not rows:
        print("ERROR: CSV vacío o no encontrado")
        return
    
    # Headers finales (ordenados lógicamente)
    final_headers = [
        # Orden
        "Número de Orden", "ID Orden", "Fecha Creación", "Fecha Actualización", "Estado",
        "Email Cliente", "Nombre Cliente", "Apellido Cliente", "CUIT Cliente",
        "Moneda Orden", "Moneda Base", "Tasa Cambio",
        "Total Orden", "Subtotal Orden", "Descuento Orden", "Envío", "Impuesto Orden",
        # Item
        "ID Item", "ID Item Padre", "Tipo Producto", "SKU", "Nombre Producto", "Cantidad",
        "Precio Original", "Precio Venta", "Precio con IVA",
        "Descuento Item", "Descuento % Item",
        "Total Item", "Total Item con IVA",
        "IVA % Item", "Impuesto Item",
    ]
    
    if has_enriched and "category_ids" in (enriched_headers or []):
        final_headers.extend(["Categorías IDs", "Categorías", "Marca"])
    
    # Procesar: propagar datos de orden
    current_order_data: Dict[str, str] = {}
    output_rows: List[Dict[str, str]] = []
    
    for row in rows:
        increment_id = row.get("increment_id", "").strip()
        
        # Si cambió la orden, actualizar datos de orden
        if increment_id and increment_id != current_order_data.get("increment_id"):
            for field in ORDER_FIELDS:
                current_order_data[field] = row.get(field, "")
        
        # Crear fila de salida
        out_row: Dict[str, str] = {}
        
        # Datos de orden (normalizados)
        out_row["Número de Orden"] = current_order_data.get("increment_id", "")
        out_row["ID Orden"] = normalize_number(current_order_data.get("entity_id", ""), 0)
        out_row["Fecha Creación"] = normalize_date(current_order_data.get("created_at", ""))
        out_row["Fecha Actualización"] = normalize_date(current_order_data.get("updated_at", ""))
        out_row["Estado"] = normalize_status(current_order_data.get("status", ""))
        
        out_row["Email Cliente"] = clean_text(current_order_data.get("customer_email", ""))
        out_row["Nombre Cliente"] = clean_text(current_order_data.get("customer_firstname", ""))
        out_row["Apellido Cliente"] = clean_text(current_order_data.get("customer_lastname", ""))
        out_row["CUIT Cliente"] = normalize_cuit(current_order_data.get("customer_taxvat", ""))
        
        currency = current_order_data.get("order_currency_code", "USD")
        out_row["Moneda Orden"] = currency
        out_row["Moneda Base"] = current_order_data.get("base_currency_code", currency)
        out_row["Tasa Cambio"] = normalize_number(current_order_data.get("currency_rate", ""), 4)
        
        out_row["Total Orden"] = format_currency(current_order_data.get("grand_total", ""), currency)
        out_row["Subtotal Orden"] = format_currency(current_order_data.get("subtotal", ""), currency)
        out_row["Descuento Orden"] = format_currency(current_order_data.get("discount_amount_order", ""), currency)
        out_row["Envío"] = format_currency(current_order_data.get("shipping_amount", ""), currency)
        out_row["Impuesto Orden"] = format_currency(current_order_data.get("tax_amount_order", ""), currency)
        
        # Datos de item
        out_row["ID Item"] = normalize_number(row.get("item_id", ""), 0)
        out_row["ID Item Padre"] = normalize_number(row.get("parent_item_id", ""), 0) if row.get("parent_item_id") else ""
        out_row["Tipo Producto"] = clean_text(row.get("product_type", ""))
        out_row["SKU"] = clean_text(row.get("sku", ""))
        out_row["Nombre Producto"] = clean_text(row.get("name", ""))
        out_row["Cantidad"] = normalize_number(row.get("qty_ordered", ""), 0)
        
        out_row["Precio Original"] = format_currency(row.get("original_price", ""), currency)
        out_row["Precio Venta"] = format_currency(row.get("price", ""), currency)
        out_row["Precio con IVA"] = format_currency(row.get("price_incl_tax", ""), currency)
        
        out_row["Descuento Item"] = format_currency(row.get("discount_amount_item", ""), currency)
        out_row["Descuento % Item"] = normalize_percent(row.get("discount_percent_item", ""))
        
        out_row["Total Item"] = format_currency(row.get("row_total", ""), currency)
        out_row["Total Item con IVA"] = format_currency(row.get("row_total_incl_tax", ""), currency)
        
        out_row["IVA % Item"] = normalize_percent(row.get("tax_percent_item", ""))
        out_row["Impuesto Item"] = format_currency(row.get("tax_amount_item", ""), currency)
        
        # Datos enriquecidos (si existen)
        if has_enriched:
            out_row["Categorías IDs"] = clean_text(row.get("category_ids", ""))
            out_row["Categorías"] = clean_text(row.get("category_names", ""))
            out_row["Marca"] = clean_text(row.get("brand", ""))
        
        output_rows.append(out_row)
    
    # Escribir CSV limpio
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig para Excel
        writer = csv.DictWriter(f, fieldnames=final_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"✅ CSV limpio generado: {OUTPUT_CSV}")
    print(f"   Total de filas procesadas: {len(output_rows)}")
    print(f"   Total de órdenes únicas: {len(set(r.get('Número de Orden', '') for r in output_rows))}")
    print(f"\n📊 Columnas generadas:")
    for i, header in enumerate(final_headers, 1):
        print(f"   {i:2d}. {header}")


if __name__ == "__main__":
    print("🔄 Iniciando ETL y limpieza de datos...")
    process_csv()
    print("\n✨ Proceso completado!")
