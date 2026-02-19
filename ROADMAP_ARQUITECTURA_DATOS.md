# 🏗️ Roadmap de Arquitectura de Datos - ETL Trade Unity

> **Arquitecto de Datos:** Sistema ETL completo para integración de todas las fuentes de Trade Unity y CEG  
> **Fecha:** Febrero 2026  
> **Objetivo:** Conectar todas las bases de datos para análisis unificado y en tiempo real

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

**Fuentes de Datos Locales (CSV/Excel):**
- ✅ Catálogo Trade Unity (`fuentes/Catalogo TU.csv`)
- ✅ Stock ERP (`fuentes/stock erp.csv`)
- ✅ Precios CEG Plataforma/FOB (`fuentes/Productos plataforma CEG_base price unit & fob_Tabla (2).csv`)
- ✅ Publicaciones históricas (`fuentes/Publicaciones de productos.csv`)
- ✅ Ventas históricas Trade Unity (`inputs/ventas_historicas_items_FINAL.csv`)

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

### Stack Tecnológico Propuesto

**Conexiones:**
- `google-cloud-bigquery` - BigQuery TU y CEG
- `google-cloud-analytics-data` - GA4
- `requests` / `httpx` - APIs REST (Magento, Connectif)
- `pymysql` / `sqlalchemy` - Bases de datos MySQL (si es necesario)

**Procesamiento:**
- `pandas` - Manipulación de datos
- `pyarrow` / `parquet` - Formato de almacenamiento eficiente
- `dask` - Procesamiento paralelo (si los datos son muy grandes)

**Orquestación:**
- `schedule` / `APScheduler` - Tareas programadas
- `airflow` (opcional) - Orquestación avanzada si crece

**Configuración:**
- `python-dotenv` - Variables de entorno
- `pyyaml` - Configuración de conexiones

---

## 🚀 Fases de Implementación

### **FASE 1: Fundación (Semanas 1-2)** 🎯 PRIORIDAD CRÍTICA

**Objetivo:** Establecer infraestructura base y conectar fuentes críticas

**Tareas:**
1. ✅ Crear estructura de Data Warehouse (`data/warehouse/`)
2. ✅ Configurar autenticación (Google Cloud, APIs)
3. ✅ Implementar extractor de BigQuery Trade Unity (ventas)
4. ✅ Implementar extractor de Magento (productos)
5. ✅ Crear sistema de logging y monitoreo básico
6. ✅ Documentar credenciales y configuración

**Entregables:**
- Scripts de extracción funcionando
- Data Warehouse con datos de ventas TU y productos Magento
- Documentación de configuración

---

### **FASE 2: Integración CEG (Semanas 3-4)** 🎯 PRIORIDAD ALTA

**Objetivo:** Conectar todas las fuentes CEG y crear cruces

**Tareas:**
1. ✅ Implementar extractor de precios CEG (actualizados)
2. ✅ Implementar extractor de ventas CEG
3. ✅ Implementar extractor de clientes CEG
4. ✅ Crear módulo de cruce CEG-TU (clientes, productos)
5. ✅ Análisis de clientes que compran en ambos canales
6. ✅ Análisis de clientes TU que nunca compraron pero sí en CEG

**Entregables:**
- Datos CEG integrados en Data Warehouse
- Scripts de cruce CEG-TU funcionando
- Análisis de oportunidades de cross-sell

---

### **FASE 3: Marketing y Comportamiento (Semanas 5-6)** 🎯 PRIORIDAD MEDIA-ALTA

**Objetivo:** Integrar datos de marketing y comportamiento web

**Tareas:**
1. ✅ Implementar extractor de Connectif
2. ✅ Implementar extractor de GA4
3. ✅ Crear módulo de atribución (qué campaña generó qué venta)
4. ✅ Análisis de engagement vs conversión
5. ✅ Scoring de clientes basado en comportamiento

**Entregables:**
- Datos de Connectif y GA4 en Data Warehouse
- Análisis de ROI de campañas
- Scoring de clientes actualizado

---

### **FASE 4: Automatización y Orquestación (Semanas 7-8)** 🎯 PRIORIDAD MEDIA

**Objetivo:** Automatizar todo el pipeline ETL

**Tareas:**
1. ✅ Crear scheduler para ejecuciones automáticas
2. ✅ Implementar sistema de alertas (errores, datos faltantes)
3. ✅ Crear dashboard de monitoreo (opcional)
4. ✅ Optimizar performance (paralelización si es necesario)
5. ✅ Documentación completa del sistema

**Entregables:**
- Pipeline ETL completamente automatizado
- Ejecuciones diarias/semanales programadas
- Sistema de alertas funcionando

---

### **FASE 5: Análisis Avanzado (Semanas 9-10)** 🎯 PRIORIDAD BAJA

**Objetivo:** Análisis avanzados con todos los datos integrados

**Tareas:**
1. ✅ Modelos predictivos (propensión a compra, churn)
2. ✅ Recomendaciones personalizadas avanzadas
3. ✅ Análisis de cohortes
4. ✅ Análisis de lifetime value mejorado
5. ✅ Dashboard ejecutivo (opcional)

**Entregables:**
- Modelos ML básicos funcionando
- Análisis avanzados en outputs

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

## 📝 Próximos Pasos Inmediatos

### Esta Semana

1. **Revisar acceso a fuentes:**
   - [ ] Verificar acceso a BigQuery Trade Unity
   - [ ] Verificar acceso a API Magento
   - [ ] Verificar acceso a datos CEG (BigQuery, Sheets, o API)
   - [ ] Verificar acceso a Connectif API
   - [ ] Verificar acceso a GA4

2. **Configurar autenticación:**
   - [ ] Crear service account para Google Cloud
   - [ ] Obtener tokens/keys de APIs
   - [ ] Configurar `.env` con credenciales

3. **Crear estructura base:**
   - [ ] Crear carpeta `data/warehouse/`
   - [ ] Crear carpeta `scripts/extractors/`
   - [ ] Crear carpeta `scripts/config/`
   - [ ] Crear `.env.example` (template sin credenciales)

### Próxima Semana

4. **Implementar primer extractor:**
   - [ ] BigQuery Trade Unity (ventas)
   - [ ] Probar conexión y extracción
   - [ ] Guardar en Data Warehouse (Parquet)

5. **Documentar:**
   - [ ] Documentar proceso de setup
   - [ ] Documentar estructura de datos extraídos
   - [ ] Crear guía de troubleshooting

---

## 📚 Estructura de Archivos Propuesta

```
ETL Trade Unity/
├── data/
│   └── warehouse/              # Data Warehouse (nuevo)
│       ├── bigquery_tu/
│       ├── magento/
│       ├── ceg/
│       ├── connectif/
│       └── ga4/
│
├── scripts/
│   ├── extractors/             # Extractores (nuevo)
│   │   ├── bigquery_extractor.py
│   │   ├── magento_extractor.py
│   │   ├── ceg_extractor.py
│   │   ├── connectif_extractor.py
│   │   └── ga4_extractor.py
│   │
│   ├── transformers/            # Transformadores (nuevo)
│   │   ├── data_cleaner.py
│   │   ├── data_enricher.py
│   │   └── data_merger.py
│   │
│   ├── config/                  # Configuración (nuevo)
│   │   ├── connections.yaml
│   │   └── schedules.yaml
│   │
│   └── (scripts actuales)       # Scripts de análisis (mantener)
│
├── .env                        # Credenciales (no commitear)
├── .env.example                # Template de credenciales
├── requirements.txt             # Actualizar con nuevas dependencias
└── ROADMAP_ARQUITECTURA_DATOS.md  # Este archivo
```

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
