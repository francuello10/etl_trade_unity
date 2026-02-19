# 🚀 ETL Trade Unity - Análisis de Datos Estratégicos

> **Repositorio de análisis de datos avanzado** para extraer insights valiosos de Trade Unity (TU), el ecommerce B2B mayorista del grupo CEG. Sistema ETL completo con análisis de ventas, inventario, clientes, pricing y oportunidades comerciales.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Análisis Generados](#-análisis-generados)
- [Estructura del Repositorio](#-estructura-del-repositorio)
- [Instalación y Uso](#-instalación-y-uso)
- [Stack Tecnológico](#-stack-tecnológico)
- [Sobre Trade Unity](#-sobre-trade-unity)
- [Roadmap y Arquitectura](#-roadmap-y-arquitectura)

---

## 🎯 Descripción

Este repositorio contiene un **sistema ETL completo** para analizar datos históricos de Trade Unity y generar insights accionables para:

- 📊 **Análisis de Ventas**: Facturación histórica, tendencias, ticket promedio, composición de órdenes
- 👥 **Inteligencia de Clientes**: Segmentación RFV, LTV, oportunistas, fans de marca, fieles a verticales
- 📦 **Análisis de Inventario**: Stock crítico, valuación, márgenes, rotación, productos estrella y "clavos"
- 💰 **Pricing Intelligence**: Análisis de publicaciones, márgenes FOB y Plataforma, impacto comercial
- 📅 **Calendario Comercial 2026**: Sugerencias inteligentes de productos por evento comercial

### 🎯 Objetivo

Proporcionar **análisis profundo y accionable** para:
- Optimizar inventario y liberar capital inmovilizado
- Identificar oportunidades de crecimiento en clientes
- Maximizar rentabilidad mediante análisis de márgenes
- Planificar calendario comercial 2026 con datos históricos

---

## 📊 Análisis Generados

Todos los archivos se generan en la carpeta `outputs/` con nombres profesionales:

### 📄 Documento Master

- **`TradeUnity Executive Report.md`** 
  - Informe ejecutivo completo (1,200+ líneas)
  - Análisis de ventas, clientes, inventario y oportunidades
  - Highlights críticos y acciones prioritarias
  - **Tiempo de lectura:** 5 min (highlights) / 30-45 min (completo)

### 📊 Archivos Excel

- **`TradeUnity Customer Intelligence.xlsx`** (17 hojas)
  - TOP 100 clientes, oportunistas, fans de marca, fieles a verticales
  - Análisis RFV, segmentación CMO, métricas de marketing
  - Clientes ideales, exprimidores, oportunidades de crecimiento

- **`TradeUnity Sales Inventory Analysis.xlsx`** (16 hojas)
  - Resumen ejecutivo con métricas trimestrales
  - Ventas desglosadas, análisis por cliente, producto, marca, categoría
  - Márgenes FOB y Plataforma, top productos

- **`TradeUnity Inventory Deep Dive.xlsx`**
  - Inventario completo con valuación (FOB, Plataforma, TU)
  - Análisis de riesgo por antigüedad de stock
  - Mejores productos y "clavos grandes" identificados

- **`TradeUnity Pricing Intelligence.xlsx`**
  - Análisis de publicaciones y pricing histórico
  - Impacto comercial de cambios de precio
  - Comparación de períodos y mix de productos

- **`TradeUnity Commercial Calendar 2026.xlsx`**
  - Sugerencias inteligentes de productos por evento comercial
  - Scoring basado en stock, ventas históricas y márgenes
  - Calendario completo 2026 con oportunidades identificadas

**Características:**
- ✅ Nombres profesionales en spanglish (fácil identificación)
- ✅ Autoajuste automático de columnas en todas las hojas
- ✅ Proporciones correctas de tablas para mejor visualización
- ✅ Formato listo para Google Drive (Markdown se lee directamente)

---

## 📁 Estructura del Repositorio

```
ETL Trade Unity/
├── 📊 outputs/              # Análisis generados (6 archivos)
│   ├── TradeUnity Executive Report.md
│   ├── TradeUnity Customer Intelligence.xlsx
│   ├── TradeUnity Sales Inventory Analysis.xlsx
│   ├── TradeUnity Inventory Deep Dive.xlsx
│   ├── TradeUnity Pricing Intelligence.xlsx
│   └── TradeUnity Commercial Calendar 2026.xlsx
│
├── 📁 fuentes/              # Datos fuente
│   ├── catalogo_trade_unity.csv
│   ├── stock_erp.csv
│   ├── precios_plataforma_ceg.csv
│   ├── publicaciones_productos.csv
│   ├── calendario_comercial_2026.csv
│   └── trade_unity_documento_base.md
│
├── 📁 inputs/               # Datos procesados
│   ├── ventas_historicas_items.csv
│   └── ventas.xlsx
│
├── 🛠️ scripts/              # Scripts Python de análisis
│   ├── analisis_inventario.py
│   ├── sugerencias_productos_eventos_comerciales.py
│   ├── generar_mega_excel_completo_final.py
│   ├── analisis_inteligencia_comercial_publicaciones.py
│   ├── analisis_clientes_completo.py
│   └── export_ventas_tradeunity.py
│
├── 📄 README.md             # Este archivo
├── requirements.txt         # Dependencias Python
└── venv/                   # Entorno virtual (no se commitea)
```

---

## 🚀 Instalación y Uso

### 🎯 Opciones de Ejecución

**Opción 1: Google Colab (Recomendado - 100% en línea)** ⭐
- ✅ Spreadsheets automáticos en Google Sheets
- ✅ Accesible desde cualquier lugar
- ✅ No requiere instalación local
- ✅ Automatización con Apps Script
- Ver: [colab_setup.md](./colab_setup.md)

**Opción 2: Local (Cursor/IDE)**
- ✅ Desarrollo y testing
- ✅ Control total del entorno
- ✅ Requiere instalación local

### Requisitos

**Para Local:**
- Python 3.12+
- pandas
- openpyxl

**Para Colab:**
- Solo necesitas cuenta Google (gratis)
- Todo se instala automáticamente en el notebook

### Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/francuello10/etl_trade_unity.git
cd etl_trade_unity

# Crear entorno virtual (si no existe)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Setup en Google Colab

Ver guía completa en [colab_setup.md](./colab_setup.md)

**Resumen rápido:**
1. Crear notebook en [Google Colab](https://colab.research.google.com/)
2. Instalar dependencias (primera celda)
3. Configurar autenticación (Google Cloud, APIs)
4. Ejecutar pipeline completo
5. Spreadsheets se actualizan automáticamente

### Generar Análisis

```bash
# Activar entorno virtual
source venv/bin/activate

# 1. Análisis de Inventario
python3 scripts/analisis_inventario.py

# 2. Sugerencias por Eventos Comerciales
python3 scripts/sugerencias_productos_eventos_comerciales.py

# 3. Mega Excel Completo (requiere ventas_historicas_items.csv)
python3 scripts/generar_mega_excel_completo_final.py

# 4. Análisis de Inteligencia Comercial
python3 scripts/analisis_inteligencia_comercial_publicaciones.py

# 5. Análisis Completo de Clientes
python3 scripts/analisis_clientes_completo.py
```

Los archivos se generarán en la carpeta `outputs/` con nombres normativos y columnas autoajustadas.

### Exportar Ventas

Si necesitas actualizar los datos de ventas desde la API de Trade Unity:

```bash
python3 scripts/export_ventas_tradeunity.py
```

Esto generará `inputs/ventas_historicas_items.csv` con los datos históricos.

---

## 🔧 Stack Tecnológico

### Trade Unity (Sistema Analizado)

- **Ecommerce**: Magento 2
- **ERP**: Odoo 17/18
- **Marketing**: Connectif
- **Datos**: Google Sheets, Google Apps Script, Looker Studio, BigQuery

### Este Repositorio

- **Lenguaje**: Python 3.12+
- **Librerías**: pandas, openpyxl
- **Formato de Salida**: Excel (.xlsx), Markdown (.md)

---

## 🏢 Sobre Trade Unity

**Trade Unity (TU)** es un **ecommerce B2B** orientado a **venta mayorista** y **operaciones corporativas**, diseñado para habilitar compras de volumen con **reglas comerciales** (precios por escala, descuentos por rangos, condiciones por medio de pago), e integrado con un **ERP** para ejecutar la operación end‑to‑end.

### Rubros Principales

- **Máquinas y Herramientas**
- **Hogar y Bazar**
- **Electricidad e Iluminación**
- **Sanitarios y Griferías**
- **Outdoor y Camping**

### Marcas Propias del Grupo CEG

- **Kuest** - movilidad, deportes y fitness
- **Barovo** - máquinas y herramientas (incluye plataforma inalámbrica "ION MAX")
- **Kushiro** - outdoor/camping y línea térmica
- **Miyawa** - maquinaria y herramientas
- **Etheos** - electricidad e iluminación
- **Gloa** - sanitarios, griferías, vanitory y accesorios
- **Vonne** - hogar / cocina (electro y equipamiento)

### Relación con CEG

Trade Unity es una **empresa hermana** de **Comprando en Grupo (CEG)**:
- **CEG** es la compañía "madre" del ecosistema: diseña y opera modelos de importación
- **TU** es el **canal ecommerce B2B** para comercializar ese mix de productos de forma digital y escalable

Ver [fuentes/trade_unity_documento_base.md](./fuentes/trade_unity_documento_base.md) para más detalles.

---

## 📈 Métricas Clave Analizadas

Los análisis incluyen:

- **Inventario**: Stock, valuación (FOB, Plataforma, TU), margen, ganancia potencial, clasificación por riesgo, volumen (m³)
- **Ventas**: Facturación histórica, unidades vendidas, clientes únicos, rotación, LTV, ticket promedio
- **Clientes**: Segmentación RFV, oportunistas, fans de marca, fieles a verticales, exprimidores, clientes ideales
- **Publicaciones**: Impacto de pricing, comparación de períodos, mix de productos
- **Sugerencias**: Productos recomendados por evento comercial con scoring inteligente

---

## 📝 Notas Importantes

### Metodología de Precios

⚠️ **Importante**: Los análisis de márgenes comparan **ventas históricas** (con precios de venta del momento) contra **precios actuales de Plataforma CEG (mejor escala) y FOB actualizados al 18.02.2026**.

**Contexto:** Los precios de plataforma y FOB tienden a la baja en muchos casos, lo cual puede explicar parcialmente los márgenes negativos observados. **Queda pendiente el cruce con los costos históricos reales** al momento de cada venta para un análisis más preciso de rentabilidad histórica.

### 🆚 Colab vs Local vs Looker

| Característica | **Colab** | **Local** | **Looker** |
|---------------|-----------|-----------|------------|
| **Accesibilidad** | ✅ 100% en línea | ❌ Requiere máquina | ✅ 100% en línea |
| **Spreadsheets** | ✅ Automáticos | ❌ Manual | ✅ Dashboards |
| **ETL Completo** | ✅ Sí | ✅ Sí | ❌ Solo visualización |
| **Análisis Profundo** | ✅ Sí | ✅ Sí | ⚠️ Limitado |
| **Costo** | ✅ Gratis | ✅ Gratis | 💰 Pago |
| **Enfoque** | ETL + Análisis | ETL + Análisis | Dashboards visuales |

**Nota:** Colab y Looker son **complementarios**. Colab hace el ETL y análisis profundo, Looker visualiza los resultados en dashboards interactivos.

### Requisitos de Datos

- Los scripts requieren que los archivos fuente estén en `fuentes/`
- Algunos scripts requieren `inputs/ventas_historicas_items.csv` (generado por `export_ventas_tradeunity.py`)
- Todos los outputs se generan en `outputs/` con nombres normativos
- Las columnas se autoajustan automáticamente para mejor visualización

---

## 🤝 Contribuciones

Este es un repositorio interno para análisis de Trade Unity. Para contribuciones o sugerencias, contactar al equipo de datos.

---

## 📄 Licencia

Este proyecto es de uso interno del grupo CEG.

---

## 🗺️ Roadmap y Arquitectura

### Estado Actual

✅ **Sistema funcionando** con datos estáticos (CSV/Excel)  
🚧 **En desarrollo:** Migración a sistema en tiempo real con Google Colab

### Próximos Pasos

Ver documentación completa:
- **[roadmap_arquitectura.md](./roadmap_arquitectura.md)** - Plan completo de integración de fuentes
- **[colab_setup.md](./colab_setup.md)** - Guía de setup en Google Colab

### Fuentes a Integrar

1. **BigQuery Trade Unity** (ventas) - 🎯 PRIORIDAD ALTA
2. **Magento API** (productos) - 🎯 PRIORIDAD ALTA
3. **CEG** (precios, ventas, clientes) - 🎯 PRIORIDAD ALTA
4. **Connectif** (marketing) - 🎯 PRIORIDAD MEDIA-ALTA
5. **GA4** (comportamiento web) - 🎯 PRIORIDAD MEDIA

**Objetivo:** Sistema 100% en línea con spreadsheets automáticos actualizados.

---

**Última actualización:** Febrero 2026  
**Repositorio:** [github.com/francuello10/etl_trade_unity](https://github.com/francuello10/etl_trade_unity)
