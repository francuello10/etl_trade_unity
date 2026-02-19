# 🏗️ Roadmap de Arquitectura de Datos - ETL Trade Unity

> **Arquitecto de Datos:** Sistema ETL completo para integración de todas las fuentes de Trade Unity y CEG  
> **Fecha:** Febrero 2026  
> **Objetivo:** Convertir sistema de "fotos estáticas" (CSV manuales) a **sistema en tiempo real** con conectores BigQuery/APIs  
> **Plataforma:** **Google Colab** (100% en línea, spreadsheets automáticos, accesible desde cualquier lugar)  
> **Filosofía:** Reportes profesionales actualizables on-demand, código compartible y escalable, **diferente a Looker** (este es ETL + análisis, Looker es dashboards)

---

## 📋 Tabla de Contenidos

- [Estado Actual](#-estado-actual)
- [Fuentes de Datos a Integrar](#-fuentes-de-datos-a-integrar)
- [Arquitectura Propuesta](#-arquitectura-propuesta)
- [Fases de Implementación](#-fases-de-implementación)
- [Consideraciones Técnicas](#-consideraciones-técnicas)
- [Próximos Pasos](#-próximos-pasos)

---

## 🎯 Estado Actual

### ✅ Lo que ya tenemos funcionando

**Desarrollo Local (Cursor):**
- ✅ Catálogo Trade Unity (`fuentes/catalogo_trade_unity.csv`)
- ✅ Stock ERP (`fuentes/stock_erp.csv`)
- ✅ Precios CEG Plataforma/FOB (`fuentes/precios_plataforma_ceg.csv`)
- ✅ Publicaciones históricas (`fuentes/publicaciones_productos.csv`)
- ✅ Ventas históricas Trade Unity (`inputs/ventas_historicas_items.csv`)

**Análisis Generados:**
- ✅ 6 outputs profesionales (Executive Report + 5 Excel files)
- ✅ Scripts Python funcionales para análisis estático
- ✅ Sistema ETL básico para procesamiento de datos locales

### ⚠️ Limitaciones Actuales

- ❌ **Datos estáticos**: Requieren exportación manual
- ❌ **Sin actualización automática**: No hay conexión en tiempo real
- ❌ **Fuentes fragmentadas**: Cada fuente requiere proceso manual
- ❌ **Sin cruces avanzados**: No hay integración entre CEG y TU
- ❌ **Sin datos de comportamiento**: No hay GA4 ni Connectif
- ❌ **Local only**: Requiere ejecutar en máquina local
- ❌ **Sin automatización**: No hay ejecución programada

### 🎯 Solución: Google Colab

**Ventajas de Colab:**
- ✅ **100% en línea**: Accesible desde cualquier lugar
- ✅ **Spreadsheets automáticos**: Escribe directo a Google Sheets
- ✅ **Ejecución programada**: Google Apps Script puede triggerear Colab
- ✅ **Gratis**: No requiere infraestructura propia
- ✅ **Compartible**: Fácil compartir notebooks con el equipo
- ✅ **Integración nativa**: BigQuery, GA4, Sheets funcionan perfecto
- ✅ **Diferente a Looker**: Este es ETL + análisis profundo, Looker es dashboards visuales

---

## 📊 Fuentes de Datos a Integrar

### 1. **BigQuery - Ventas Trade Unity** 🎯 PRIORIDAD ALTA

**Descripción:**
- Base de datos de ventas históricas y en tiempo real de Trade Unity
- Órdenes, items, clientes, productos vendidos
- Datos transaccionales completos

**Datos Clave:**
- Órdenes y items de venta
- Fechas, montos, cantidades
- Clientes (email, nombre, empresa)
- Productos (SKU, nombre, categoría)
- Estados de órdenes (activa, cancelada, completada)

**Conexión Propuesta:**
```python
# Usar google-cloud-bigquery
from google.cloud import bigquery

client = bigquery.Client(project="trade-unity-project")
query = """
    SELECT 
        order_id,
        created_at,
        customer_email,
        sku,
        quantity,
        price,
        total
    FROM `trade-unity.sales.orders`
    WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
"""
```

**Frecuencia de Actualización:** Diaria (o en tiempo real si es necesario)

---

### 2. **Magento - Base de Productos** 🎯 PRIORIDAD ALTA

**Descripción:**
- Catálogo completo de productos publicados en Trade Unity
- Precios, stock, categorías, atributos
- Estado de publicación y visibilidad

**Datos Clave:**
- SKU, nombre, descripción
- Precios (por escala)
- Stock disponible
- Categorías y atributos
- Estado de publicación
- Imágenes y metadata

**Conexión Propuesta:**
```python
# Opción 1: API REST de Magento 2
import requests

MAGENTO_API_URL = "https://tradeunity.com/rest/default/V1"
headers = {
    "Authorization": "Bearer {token}",
    "Content-Type": "application/json"
}

# Opción 2: Exportación directa desde base de datos MySQL
# Conectar a MySQL de Magento y exportar catálogo
```

**Frecuencia de Actualización:** Diaria (o cuando hay cambios en catálogo)

---

### 3. **CEG - Base de Productos con Precios Actualizados** 🎯 PRIORIDAD ALTA

**Descripción:**
- Catálogo CEG con precios FOB y Plataforma actualizados
- Precios por escala (mejor escala, escalas intermedias)
- Actualizaciones de precios en tiempo real

**Datos Clave:**
- SKU CEG
- Precio FOB actualizado
- Precio Plataforma (mejor escala)
- Precios por escalas
- Fechas de actualización

**Conexión Propuesta:**
```python
# Opción 1: API CEG (si existe)
# Opción 2: BigQuery CEG (si comparten proyecto)
# Opción 3: Exportación automática desde sistema CEG
# Opción 4: Google Sheets con Apps Script que se actualiza automáticamente

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Conectar a Google Sheets que se actualiza desde CEG
SHEET_ID = "ceg-prices-sheet-id"
service = build('sheets', 'v4', credentials=creds)
```

**Frecuencia de Actualización:** Diaria (o cuando hay cambios de precio)

---

### 4. **CEG - Ventas Históricas** 🎯 PRIORIDAD MEDIA

**Descripción:**
- Ventas históricas de CEG (tradicional y express)
- Comparación de comportamiento entre CEG y TU
- Identificación de clientes que compran en ambos canales

**Datos Clave:**
- Órdenes CEG
- Clientes CEG
- Productos vendidos
- Fechas y montos
- Canal (tradicional, express)

**Conexión Propuesta:**
```python
# Similar a BigQuery Trade Unity
# O desde sistema ERP de CEG
# O desde base de datos compartida
```

**Frecuencia de Actualización:** Semanal o mensual (según necesidad)

---

### 5. **CEG - Base de Clientes** 🎯 PRIORIDAD ALTA

**Descripción:**
- Clientes registrados en CEG
- Historial de compras CEG
- Segmentación y comportamiento

**Datos Clave:**
- Email, nombre, empresa
- Historial de compras
- Segmentación
- Última compra, frecuencia, ticket promedio

**Conexión Propuesta:**
```python
# Desde BigQuery CEG o base de datos compartida
# Cruce con clientes TU para identificar:
# - Clientes TU que nunca compraron pero sí en CEG
# - Clientes CEG que nunca compraron pero sí en TU
# - Clientes que compran en ambos
```

**Frecuencia de Actualización:** Semanal

---

### 6. **Trade Unity - Base de Clientes** 🎯 PRIORIDAD ALTA

**Descripción:**
- Clientes registrados en Trade Unity
- Información de cuenta, preferencias
- Historial completo de compras

**Datos Clave:**
- Email, nombre, empresa
- Tipo de cuenta (B2B, corporativo)
- Preferencias y configuración
- Historial de compras TU

**Conexión Propuesta:**
```python
# Desde BigQuery Trade Unity
# O desde API de Magento (clientes)
```

**Frecuencia de Actualización:** Diaria

---

### 7. **Connectif - Marketing Automation** 🎯 PRIORIDAD MEDIA-ALTA

**Descripción:**
- Datos de comportamiento de marketing
- Campañas enviadas, abiertas, clickeadas
- Segmentación y scoring de clientes
- Engagement y conversión por campaña

**Datos Clave:**
- Campañas enviadas
- Tasa de apertura, clicks
- Conversiones atribuidas
- Segmentos activos
- Scoring de clientes

**Conexión Propuesta:**
```python
# API de Connectif
import requests

CONNECTIF_API_URL = "https://api.connectif.io/v1"
headers = {
    "Authorization": "Bearer {connectif_token}",
    "Content-Type": "application/json"
}

# Endpoints clave:
# - /campaigns (campañas)
# - /contacts (contactos y scoring)
# - /events (eventos de engagement)
```

**Frecuencia de Actualización:** Diaria o en tiempo real (según necesidad)

---

### 8. **GA4 - Google Analytics 4** 🎯 PRIORIDAD MEDIA

**Descripción:**
- Comportamiento web de usuarios
- Tráfico, sesiones, páginas vistas
- Eventos de conversión
- Fuentes de tráfico y atribución

**Datos Clave:**
- Sesiones y usuarios
- Páginas vistas
- Eventos (add to cart, checkout, purchase)
- Fuentes de tráfico
- Dispositivos y ubicaciones
- Funnels de conversión

**Conexión Propuesta:**
```python
# Google Analytics Data API (GA4)
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

client = BetaAnalyticsDataClient()
property_id = "trade-unity-ga4-property-id"

request = RunReportRequest(
    property=f"properties/{property_id}",
    date_ranges=[DateRange(start_date="2024-01-01", end_date="today")],
    dimensions=[Dimension(name="eventName")],
    metrics=[Metric(name="eventCount")]
)
```

**Frecuencia de Actualización:** Diaria

---

## 🏗️ Arquitectura Propuesta

### Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  BigQuery TU    │  Magento API    │  CEG Prices    │  CEG Sales │
│  (Ventas)       │  (Productos)    │  (Precios)      │  (Ventas)  │
│                 │                 │                 │            │
│  CEG Clients    │  TU Clients     │  Connectif     │  GA4       │
│  (Clientes)     │  (Clientes)     │  (Marketing)   │  (Web)     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ETL LAYER (Python Scripts)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Extractors (conexiones a fuentes)                            │
│     - bigquery_extractor.py                                      │
│     - magento_extractor.py                                       │
│     - ceg_extractor.py                                           │
│     - connectif_extractor.py                                     │
│     - ga4_extractor.py                                           │
│                                                                   │
│  2. Transformers (limpieza y enriquecimiento)                   │
│     - data_cleaner.py                                            │
│     - data_enricher.py                                           │
│     - data_merger.py                                             │
│                                                                   │
│  3. Loaders (guardado en formato unificado)                     │
│     - data_loader.py                                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA WAREHOUSE (Staging Area)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  - Parquet files (formato eficiente)                             │
│  - Particionado por fecha                                        │
│  - Estructura: data/warehouse/{source}/{date}/                  │
│                                                                   │
│  Estructura:                                                     │
│  data/warehouse/                                                 │
│    ├── bigquery_tu/                                             │
│    │   ├── 2026/02/18/sales.parquet                            │
│    │   └── 2026/02/19/sales.parquet                            │
│    ├── magento/                                                 │
│    │   └── products.parquet                                    │
│    ├── ceg/                                                     │
│    │   ├── prices.parquet                                       │
│    │   └── sales.parquet                                        │
│    └── ...                                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ANALYSIS LAYER (Scripts Actuales)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  - analisis_inventario.py                                        │
│  - analisis_clientes_completo.py                                 │
│  - generar_mega_excel_completo_final.py                          │
│  - (todos los scripts actuales)                                  │
│                                                                   │
│  Estos scripts ahora leen desde el Data Warehouse                │
│  en lugar de CSVs estáticos                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUTS (outputs/)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  - TradeUnity Executive Report.md                                │
│  - TradeUnity Customer Intelligence.xlsx                         │
│  - (todos los outputs actuales)                                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico Propuesto (Google Colab)

**Plataforma:**
- **Google Colab** - Notebook principal (gratis, en línea)
- **Google Drive** - Almacenamiento de outputs
- **Google Sheets** - Spreadsheets automáticos
- **Google Apps Script** - Automatización y triggers

**Conexiones (en Colab):**
- `google-cloud-bigquery` - BigQuery TU y CEG (nativo en Colab)
- `google-cloud-analytics-data` - GA4 (nativo en Colab)
- `gspread` - Escribir a Google Sheets
- `google-auth` - Autenticación Google
- `requests` / `httpx` - APIs REST (Magento, Connectif)

**Procesamiento:**
- `pandas` - Manipulación de datos
- `numpy` - Cálculos numéricos
- `openpyxl` - Generar Excel (subir a Drive)

**Almacenamiento:**
- **Google Sheets** - Datos tabulares (automático)
- **Google Drive** - Archivos Excel y MD (automático)
- **Colab Variables** - Cache temporal durante ejecución

**Automatización:**
- **Google Apps Script** - Triggerear Colab notebook
- **Colab Scheduler** (opcional) - Ejecución programada directa

---

## 🚀 Fases de Implementación (Tiempos Realistas con Cursor)

> **Nota:** Tiempos estimados asumiendo desarrollo con Cursor AI, conocimiento del dominio ya adquirido, y enfoque en hacerlo "como la gente" (profesional y compartible).

### **FASE 1: Fundación - BigQuery + Magento (3-4 días)** 🎯 PRIORIDAD CRÍTICA

**Objetivo:** Establecer infraestructura base y conectar fuentes críticas en tiempo real

**Tareas y Tiempos:**
1. **Día 1 - Setup y BigQuery (4-6 horas)**
   - ✅ Crear estructura de Data Warehouse (`data/warehouse/`)
   - ✅ Configurar autenticación Google Cloud (service account)
   - ✅ Implementar extractor BigQuery Trade Unity (ventas)
   - ✅ Probar conexión y extraer datos de prueba
   - ✅ Guardar en Parquet (formato eficiente)

2. **Día 2 - Magento API (4-6 horas)**
   - ✅ Implementar extractor Magento (productos, precios, stock)
   - ✅ Manejar paginación y rate limiting
   - ✅ Probar y validar datos extraídos
   - ✅ Integrar con Data Warehouse

3. **Día 3 - Refactor Scripts Actuales (4-6 horas)**
   - ✅ Modificar scripts de análisis para leer desde Data Warehouse
   - ✅ Mantener compatibilidad con CSVs (fallback)
   - ✅ Probar que los outputs se generen correctamente
   - ✅ Documentar cambios

4. **Día 4 - Testing y Documentación (2-4 horas)**
   - ✅ Testing end-to-end
   - ✅ Documentar configuración y setup
   - ✅ Crear `.env.example`
   - ✅ README actualizado

**Entregables:**
- ✅ Scripts de extracción BigQuery + Magento funcionando
- ✅ Data Warehouse con datos en tiempo real
- ✅ Scripts de análisis actualizados (leen desde warehouse)
- ✅ Documentación completa de setup

**Tiempo Total:** 3-4 días de trabajo enfocado

---

### **FASE 2: Integración CEG (2-3 días)** 🎯 PRIORIDAD ALTA

**Objetivo:** Conectar fuentes CEG y crear cruces inteligentes

**Tareas y Tiempos:**
1. **Día 1 - Precios CEG (4-6 horas)**
   - ✅ Identificar fuente de precios CEG (BigQuery, Sheets, API)
   - ✅ Implementar extractor de precios CEG actualizados
   - ✅ Validar datos y formato
   - ✅ Integrar con Data Warehouse

2. **Día 2 - Ventas y Clientes CEG (4-6 horas)**
   - ✅ Implementar extractor de ventas CEG
   - ✅ Implementar extractor de clientes CEG
   - ✅ Crear módulo de cruce CEG-TU
   - ✅ Probar cruces y validar resultados

3. **Día 3 - Análisis de Cruces (2-4 horas)**
   - ✅ Análisis: clientes que compran en ambos canales
   - ✅ Análisis: clientes TU que nunca compraron pero sí en CEG
   - ✅ Análisis: oportunidades de cross-sell
   - ✅ Agregar insights a outputs

**Entregables:**
- ✅ Datos CEG integrados en tiempo real
- ✅ Scripts de cruce CEG-TU funcionando
- ✅ Análisis de oportunidades en outputs

**Tiempo Total:** 2-3 días

---

### **FASE 3: Marketing y Comportamiento (2-3 días)** 🎯 PRIORIDAD MEDIA-ALTA

**Objetivo:** Integrar datos de marketing y comportamiento web

**Tareas y Tiempos:**
1. **Día 1 - Connectif (4-6 horas)**
   - ✅ Investigar API Connectif (documentación)
   - ✅ Implementar extractor Connectif (campañas, engagement)
   - ✅ Validar datos y formato
   - ✅ Integrar con Data Warehouse

2. **Día 2 - GA4 (4-6 horas)**
   - ✅ Configurar Google Analytics Data API
   - ✅ Implementar extractor GA4 (sesiones, eventos, conversiones)
   - ✅ Validar datos y formato
   - ✅ Integrar con Data Warehouse

3. **Día 3 - Atribución y Scoring (2-4 horas)**
   - ✅ Crear módulo de atribución (campaña → venta)
   - ✅ Análisis de engagement vs conversión
   - ✅ Scoring de clientes basado en comportamiento
   - ✅ Agregar a outputs

**Entregables:**
- ✅ Datos Connectif y GA4 en tiempo real
- ✅ Análisis de ROI de campañas
- ✅ Scoring de clientes actualizado

**Tiempo Total:** 2-3 días

---

### **FASE 4: Automatización y CLI (1-2 días)** 🎯 PRIORIDAD MEDIA

**Objetivo:** Hacer el sistema fácil de usar y actualizable on-demand

**Tareas y Tiempos:**
1. **Día 1 - CLI y Orquestación (4-6 horas)**
   - ✅ Crear CLI principal (`python etl.py update --all`)
   - ✅ Comandos: `update`, `analyze`, `status`
   - ✅ Sistema de logging profesional
   - ✅ Manejo de errores robusto

2. **Día 2 - Scheduler y Alertas (2-4 horas)**
   - ✅ Scheduler opcional (ejecuciones automáticas)
   - ✅ Sistema de alertas básico (errores, datos faltantes)
   - ✅ Documentación de uso
   - ✅ Testing

**Entregables:**
- ✅ CLI profesional y fácil de usar
- ✅ Sistema actualizable on-demand
- ✅ Scheduler opcional para automatización

**Tiempo Total:** 1-2 días

---

### **FASE 5: Polish y Compartibilidad (1 día)** 🎯 PRIORIDAD MEDIA

**Objetivo:** Hacer el repo compartible y profesional

**Tareas y Tiempos:**
1. **Día 1 - Documentación y Cleanup (4-6 horas)**
   - ✅ README completo y profesional
   - ✅ Documentación de cada extractor
   - ✅ Ejemplos de uso
   - ✅ Cleanup de código (comentarios, type hints)
   - ✅ Requirements.txt actualizado
   - ✅ .gitignore completo

**Entregables:**
- ✅ Repo listo para compartir
- ✅ Documentación completa
- ✅ Código limpio y profesional

**Tiempo Total:** 1 día

---

### **RESUMEN DE TIEMPOS**

| Fase | Descripción | Tiempo Estimado |
|------|-------------|-----------------|
| **Fase 1** | BigQuery + Magento + Refactor | 3-4 días |
| **Fase 2** | Integración CEG | 2-3 días |
| **Fase 3** | Connectif + GA4 | 2-3 días |
| **Fase 4** | Automatización y CLI | 1-2 días |
| **Fase 5** | Polish y Compartibilidad | 1 día |
| **TOTAL** | **Sistema completo en tiempo real** | **9-13 días** |

**Nota:** Tiempos asumen trabajo enfocado con Cursor. Si trabajas part-time, multiplicar por 2-3x.

---

## 🔧 Consideraciones Técnicas

### Autenticación y Seguridad

**Google Cloud:**
```python
# Usar service account con permisos mínimos necesarios
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account-key.json',
    scopes=['https://www.googleapis.com/auth/bigquery.readonly']
)
```

**APIs Externas:**
- Guardar tokens/keys en variables de entorno (`.env`)
- Nunca commitear credenciales
- Usar rotación de tokens si es posible

### Manejo de Volumen de Datos

**Estrategias:**
- **Incremental loads**: Solo cargar datos nuevos/modificados
- **Particionado por fecha**: Organizar datos por fecha para queries eficientes
- **Compresión**: Usar Parquet para reducir tamaño
- **Caché**: Cachear datos que no cambian frecuentemente (catálogo)

### Error Handling y Resiliencia

**Implementar:**
- Retry logic para conexiones
- Logging detallado de errores
- Notificaciones cuando falla extracción
- Fallback a datos anteriores si falla actualización

### Performance

**Optimizaciones:**
- Procesamiento paralelo para fuentes independientes
- Queries optimizadas en BigQuery
- Uso de índices en Data Warehouse
- Limpieza de datos antiguos (retention policy)

---

## 📝 Plan de Implementación Inmediato

### 🎯 Objetivo: Sistema en Tiempo Real (9-13 días)

**Filosofía:**
- ✅ **On-demand updates**: `python etl.py update --all` actualiza todo
- ✅ **Reportes profesionales**: Excel/MD que se regeneran con datos frescos
- ✅ **Código compartible**: Bien documentado, limpio, fácil de entender
- ✅ **Escalable**: Fácil agregar nuevas fuentes

### 📅 Cronograma Detallado

#### **Semana 1: Fundación (Días 1-4)**

**Día 1 - Setup y BigQuery (Lunes)**
```bash
# Tareas:
1. Crear estructura de carpetas
2. Configurar Google Cloud (service account)
3. Implementar extractor BigQuery
4. Probar y validar
```

**Día 2 - Magento API (Martes)**
```bash
# Tareas:
1. Implementar extractor Magento
2. Manejar paginación y rate limits
3. Validar datos
```

**Día 3 - Refactor Scripts (Miércoles)**
```bash
# Tareas:
1. Modificar scripts para leer desde warehouse
2. Mantener fallback a CSVs
3. Probar outputs
```

**Día 4 - Testing (Jueves)**
```bash
# Tareas:
1. Testing end-to-end
2. Documentación
3. Preparar para Fase 2
```

#### **Semana 2: CEG + Marketing (Días 5-8)**

**Día 5 - Precios CEG (Viernes)**
**Día 6 - Ventas/Clientes CEG (Lunes)**
**Día 7 - Connectif (Martes)**
**Día 8 - GA4 (Miércoles)**

#### **Semana 3: Automatización + Polish (Días 9-11)**

**Día 9 - CLI y Orquestación (Jueves)**
**Día 10 - Scheduler (Viernes)**
**Día 11 - Documentación Final (Lunes)**

---

### 🚀 Comandos que Queremos Tener

```bash
# Actualizar todos los datos
python etl.py update --all

# Actualizar solo una fuente
python etl.py update --bigquery
python etl.py update --magento
python etl.py update --ceg

# Generar reportes
python etl.py analyze --all
python etl.py analyze --sales
python etl.py analyze --inventory

# Ver estado
python etl.py status

# Ver logs
python etl.py logs --tail
```

---

### ✅ Checklist de Setup Inicial (Hacer HOY)

**Accesos:**
- [ ] Verificar acceso a BigQuery Trade Unity
- [ ] Verificar acceso a API Magento (ya tienes token en `export_ventas_tradeunity.py`)
- [ ] Verificar acceso a datos CEG (BigQuery, Sheets, o API)
- [ ] Verificar acceso a Connectif API
- [ ] Verificar acceso a GA4 (property ID)

**Configuración:**
- [ ] Crear service account para Google Cloud
- [ ] Obtener tokens/keys de APIs
- [ ] Crear `.env` con credenciales
- [ ] Crear `.env.example` (template)

**Estructura:**
- [ ] Crear `data/warehouse/` con subcarpetas
- [ ] Crear `scripts/extractors/`
- [ ] Crear `scripts/config/`
- [ ] Actualizar `requirements.txt` con nuevas dependencias

---

## 📚 Estructura de Archivos Propuesta

```
ETL Trade Unity/
├── data/
│   └── warehouse/              # Data Warehouse (nuevo)
│       ├── bigquery_tu/
│       │   └── 2026/02/18/sales.parquet
│       ├── magento/
│       │   └── products.parquet
│       ├── ceg/
│       │   ├── prices.parquet
│       │   ├── sales.parquet
│       │   └── clients.parquet
│       ├── connectif/
│       │   └── campaigns.parquet
│       └── ga4/
│           └── events.parquet
│
├── scripts/
│   ├── extractors/             # Extractores (nuevo)
│   │   ├── __init__.py
│   │   ├── base_extractor.py   # Clase base
│   │   ├── bigquery_extractor.py
│   │   ├── magento_extractor.py
│   │   ├── ceg_extractor.py
│   │   ├── connectif_extractor.py
│   │   └── ga4_extractor.py
│   │
│   ├── transformers/            # Transformadores (nuevo)
│   │   ├── __init__.py
│   │   ├── data_cleaner.py
│   │   ├── data_enricher.py
│   │   └── data_merger.py
│   │
│   ├── config/                  # Configuración (nuevo)
│   │   ├── __init__.py
│   │   ├── connections.yaml
│   │   └── schemas.yaml         # Esquemas de datos
│   │
│   ├── utils/                   # Utilidades (nuevo)
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── storage.py           # Manejo de Parquet
│   │   └── validators.py
│   │
│   ├── etl.py                   # CLI principal (nuevo)
│   │
│   └── (scripts actuales)       # Scripts de análisis (mantener)
│       ├── analisis_inventario.py
│       ├── analisis_clientes_completo.py
│       └── ...
│
├── .env                        # Credenciales (no commitear)
├── .env.example                # Template de credenciales
├── requirements.txt             # Actualizar con nuevas dependencias
├── etl.py                      # CLI principal (symlink o wrapper)
└── ROADMAP_ARQUITECTURA_DATOS.md
```

### 🎯 Principios de Diseño

**1. Modularidad:**
- Cada extractor es independiente
- Fácil agregar nuevas fuentes
- Fácil testear individualmente

**2. Resiliencia:**
- Fallback a datos anteriores si falla extracción
- Retry logic automático
- Logging detallado

**3. Performance:**
- Incremental loads (solo datos nuevos)
- Particionado por fecha
- Compresión Parquet

**4. Compartibilidad:**
- Código limpio y documentado
- Type hints en Python
- README completo
- Ejemplos de uso

---

## 🎯 Métricas de Éxito

**Fase 1:**
- ✅ Extracción diaria de ventas TU funcionando
- ✅ Extracción diaria de productos Magento funcionando
- ✅ Data Warehouse con datos actualizados

**Fase 2:**
- ✅ Cruce CEG-TU funcionando
- ✅ Identificación de oportunidades de cross-sell

**Fase 3:**
- ✅ Atribución de campañas funcionando
- ✅ Scoring de clientes actualizado

**Fase 4:**
- ✅ Pipeline completamente automatizado
- ✅ 0 intervención manual requerida

---

## 📞 Contactos y Recursos

**Documentación:**
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [Magento 2 REST API](https://devdocs.magento.com/guides/v2.4/rest/bk-rest.html)
- [GA4 Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Connectif API](https://docs.connectif.io/) (verificar documentación)

**Equipos:**
- **Trade Unity Tech**: Para acceso a BigQuery y Magento
- **CEG Tech**: Para acceso a datos CEG
- **Marketing**: Para acceso a Connectif y GA4

---

**Última actualización:** Febrero 2026  
**Próxima revisión:** Después de completar Fase 1
