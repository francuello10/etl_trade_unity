#!/usr/bin/env python3
"""
Script para filtrar el CSV y eliminar órdenes canceladas y cerradas.
Mantiene solo órdenes confirmadas/abiertas: Entregado, Completa, Pendiente, 
Procesando, En_Transito
"""

import csv

# Archivos
INPUT_CSV = "ventas_historicas_items.csv"
OUTPUT_CSV = "ventas_historicas_items.csv"

# Estados a ELIMINAR
STATES_TO_REMOVE = [
    "Cancelada",
    "Cerrada",
]

# Estados a MANTENER (todos los demás se eliminan también)
STATES_TO_KEEP = [
    "Entregado",
    "Completa",
    "Pendiente",
    "Procesando",
    "En_Transito",
]


def filter_orders():
    """Filtra el CSV eliminando órdenes canceladas y cerradas."""
    
    print(f"📖 Leyendo CSV: {INPUT_CSV}")
    rows = []
    headers = []
    
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    
    print(f"   ✅ {len(rows)} filas leídas")
    
    # Contar estados antes
    states_before = {}
    for row in rows:
        estado = row.get("Estado", "").strip()
        states_before[estado] = states_before.get(estado, 0) + 1
    
    print(f"\n📊 Estados antes del filtrado:")
    for estado, count in sorted(states_before.items(), key=lambda x: -x[1]):
        print(f"   {estado}: {count} filas")
    
    # Filtrar filas
    filtered_rows = []
    removed_count = 0
    
    for row in rows:
        estado = row.get("Estado", "").strip()
        
        # Mantener si está en la lista de estados a mantener
        if estado in STATES_TO_KEEP:
            filtered_rows.append(row)
        else:
            removed_count += 1
    
    print(f"\n🗑️  Filtrando órdenes...")
    print(f"   Filas eliminadas: {removed_count}")
    print(f"   Filas mantenidas: {len(filtered_rows)}")
    
    # Contar estados después
    states_after = {}
    for row in filtered_rows:
        estado = row.get("Estado", "").strip()
        states_after[estado] = states_after.get(estado, 0) + 1
    
    print(f"\n📊 Estados después del filtrado:")
    for estado, count in sorted(states_after.items(), key=lambda x: -x[1]):
        print(f"   {estado}: {count} filas")
    
    # Escribir CSV filtrado
    print(f"\n💾 Escribiendo CSV filtrado: {OUTPUT_CSV}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filtered_rows)
    
    print(f"   ✅ CSV filtrado generado")
    
    # Estadísticas finales
    print(f"\n✨ Resumen:")
    print(f"   Total filas originales: {len(rows)}")
    print(f"   Filas eliminadas: {removed_count} ({removed_count/len(rows)*100:.1f}%)")
    print(f"   Filas mantenidas: {len(filtered_rows)} ({len(filtered_rows)/len(rows)*100:.1f}%)")
    
    # Contar órdenes únicas
    ordenes_antes = len(set(row.get("Número de Orden", "") for row in rows))
    ordenes_despues = len(set(row.get("Número de Orden", "") for row in filtered_rows))
    
    print(f"\n   Órdenes únicas antes: {ordenes_antes}")
    print(f"   Órdenes únicas después: {ordenes_despues}")
    print(f"   Órdenes eliminadas: {ordenes_antes - ordenes_despues}")


if __name__ == "__main__":
    print("🔄 Iniciando filtrado de órdenes...")
    filter_orders()
    print("\n✨ Proceso completado!")
