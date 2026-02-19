# 🚀 Setup Google Colab - ETL Trade Unity

> **Guía completa** para migrar el sistema ETL a Google Colab y mantener spreadsheets automáticos actualizados

---

## 📋 Tabla de Contenidos

- [Por qué Colab](#-por-qué-colab)
- [Estructura del Notebook](#-estructura-del-notebook)
- [Setup Inicial](#-setup-inicial)
- [Autenticación](#-autenticación)
- [Escribir a Google Sheets](#-escribir-a-google-sheets)
- [Automatización](#-automatización)
- [Migración desde Local](#-migración-desde-local)

---

## 🎯 Por qué Colab

### Ventajas Clave

✅ **100% en línea** - Accesible desde cualquier lugar  
✅ **Spreadsheets automáticos** - Escribe directo a Google Sheets  
✅ **Gratis** - No requiere infraestructura propia  
✅ **Integración nativa** - BigQuery, GA4, Sheets funcionan perfecto  
✅ **Compartible** - Fácil compartir notebooks con el equipo  
✅ **Automatizable** - Google Apps Script puede triggerear ejecuciones  
✅ **Diferente a Looker** - Este es ETL + análisis profundo, Looker es dashboards

### Cuándo Usar Colab vs Looker

| Necesidad | Usar |
|-----------|------|
| ETL completo (extraer, transformar, cargar) | **Colab** |
| Análisis profundo con Python | **Colab** |
| Generar Excel/CSV automáticos | **Colab** |
| Dashboards visuales interactivos | **Looker** |
| Visualización en tiempo real | **Looker** |
| Reportes ejecutivos visuales | **Looker** |

**Son complementarios:** Colab hace el ETL y análisis, Looker visualiza los resultados.

---

## 📓 Estructura del Notebook

### Organización Propuesta

```python
# ============================================================================
# ETL TRADE UNITY - Google Colab Notebook
# ============================================================================
# 
# Este notebook ejecuta el pipeline completo:
# 1. Extrae datos de todas las fuentes
# 2. Transforma y enriquece los datos
# 3. Genera análisis completos
# 4. Escribe a Google Sheets y Drive
#
# Ejecutar: Runtime > Run All (o sección por sección)
# ============================================================================

# ----------------------------------------------------------------------------
# SECCIÓN 1: SETUP Y CONFIGURACIÓN
# ----------------------------------------------------------------------------
# - Instalar dependencias
# - Configurar autenticación
# - Cargar credenciales

# ----------------------------------------------------------------------------
# SECCIÓN 2: EXTRACTORS
# ----------------------------------------------------------------------------
# - BigQuery Trade Unity (ventas)
# - Magento API (productos)
# - CEG (precios, ventas, clientes)
# - Connectif (marketing)
# - GA4 (comportamiento web)

# ----------------------------------------------------------------------------
# SECCIÓN 3: TRANSFORMERS
# ----------------------------------------------------------------------------
# - Limpieza de datos
# - Enriquecimiento
# - Cruces CEG-TU

# ----------------------------------------------------------------------------
# SECCIÓN 4: ANALYSIS
# ----------------------------------------------------------------------------
# - Análisis de inventario
# - Análisis de clientes
# - Análisis de ventas
# - Análisis de pricing

# ----------------------------------------------------------------------------
# SECCIÓN 5: OUTPUTS
# ----------------------------------------------------------------------------
# - Escribir a Google Sheets
# - Generar Excel y subir a Drive
# - Generar Markdown y subir a Drive
```

---

## 🔧 Setup Inicial

### Paso 1: Crear Notebook en Colab

1. Ir a [Google Colab](https://colab.research.google.com/)
2. Crear nuevo notebook: `File > New notebook`
3. Renombrar: `ETL Trade Unity - Pipeline Completo`
4. Guardar en Google Drive

### Paso 2: Instalar Dependencias

```python
# Primera celda del notebook
!pip install -q google-cloud-bigquery
!pip install -q google-cloud-analytics-data
!pip install -q gspread
!pip install -q google-auth
!pip install -q pandas
!pip install -q openpyxl
!pip install -q requests
```

### Paso 3: Importar Librerías

```python
# Segunda celda
import pandas as pd
import numpy as np
from datetime import datetime, date
from google.cloud import bigquery
from google.analytics.data_v1beta import BetaAnalyticsDataClient
import gspread
from google.oauth2 import service_account
import requests
from google.colab import drive, files, auth
```

---

## 🔐 Autenticación

### Opción 1: Service Account (Recomendado para Automatización)

```python
# Cargar service account desde Colab Secrets
from google.colab import userdata

# Configurar credenciales
import json
import os

# Obtener credenciales desde Secrets
service_account_info = json.loads(userdata.get('GOOGLE_SERVICE_ACCOUNT'))
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=['https://www.googleapis.com/auth/bigquery',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive']
)

# Configurar clientes
bq_client = bigquery.Client(credentials=credentials, project='trade-unity-project')
sheets_client = gspread.authorize(credentials)
```

### Opción 2: Autenticación Interactiva (Para Desarrollo)

```python
# Autenticación interactiva (más fácil para desarrollo)
from google.colab import auth
auth.authenticate_user()

# Configurar clientes
bq_client = bigquery.Client(project='trade-unity-project')
```

### Configurar Secrets en Colab

1. Ir a: `Colab > 🔑 (icono de llave) > Add a secret`
2. Agregar:
   - `GOOGLE_SERVICE_ACCOUNT` - JSON completo del service account
   - `MAGENTO_API_TOKEN` - Token de API Magento
   - `CONNECTIF_API_KEY` - Key de Connectif (si aplica)

---

## 📊 Escribir a Google Sheets

### Ejemplo: Escribir Análisis de Ventas

```python
def write_to_sheets(df, spreadsheet_name, worksheet_name):
    """
    Escribe un DataFrame a Google Sheets.
    
    Args:
        df: DataFrame de pandas
        spreadsheet_name: Nombre del spreadsheet
        worksheet_name: Nombre de la hoja
    """
    try:
        # Abrir o crear spreadsheet
        try:
            spreadsheet = sheets_client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = sheets_client.create(spreadsheet_name)
            # Compartir con tu email (opcional)
            spreadsheet.share('tu-email@ejemplo.com', perm_type='user', role='writer')
        
        # Abrir o crear worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        
        # Limpiar hoja existente
        worksheet.clear()
        
        # Escribir headers
        worksheet.append_row(df.columns.tolist())
        
        # Escribir datos (en batches para performance)
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = batch.values.tolist()
            worksheet.append_rows(values)
        
        print(f"✅ Datos escritos a {spreadsheet_name} > {worksheet_name}")
        print(f"   Filas escritas: {len(df)}")
        
    except Exception as e:
        print(f"❌ Error escribiendo a Sheets: {e}")
        raise

# Ejemplo de uso
ventas_df = pd.DataFrame(...)  # Tu análisis de ventas
write_to_sheets(ventas_df, "TradeUnity Sales Analysis", "Ventas por Trimestre")
```

### Estructura de Spreadsheets Propuesta

```
📊 TradeUnity Sales Analysis
   ├── Ventas por Trimestre
   ├── Top Productos
   └── Top Clientes

📊 TradeUnity Customer Intelligence
   ├── TOP 100 Clientes
   ├── Oportunistas
   ├── Fans de Marca
   └── Fieles a Vertical

📊 TradeUnity Inventory Deep Dive
   ├── Inventario Completo
   ├── Stock Crítico
   └── Mejores Productos

📊 TradeUnity Pricing Intelligence
   ├── Márgenes FOB
   └── Márgenes Plataforma

📊 TradeUnity Commercial Calendar 2026
   └── Sugerencias por Evento
```

---

## 📁 Subir Archivos a Google Drive

### Ejemplo: Generar Excel y Subir a Drive

```python
def upload_to_drive(file_path, drive_folder_id=None):
    """
    Sube un archivo a Google Drive.
    
    Args:
        file_path: Ruta local del archivo
        drive_folder_id: ID de carpeta en Drive (opcional)
    """
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.discovery import build
    
    drive_service = build('drive', 'v3', credentials=credentials)
    
    file_metadata = {
        'name': os.path.basename(file_path),
    }
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    print(f"✅ Archivo subido: {file.get('webViewLink')}")
    return file.get('id')

# Ejemplo: Generar Excel y subir
with pd.ExcelWriter('/tmp/customer_intelligence.xlsx', engine='openpyxl') as writer:
    df_top100.to_excel(writer, sheet_name='TOP 100', index=False)
    df_oportunistas.to_excel(writer, sheet_name='Oportunistas', index=False)
    # ... más hojas

upload_to_drive('/tmp/customer_intelligence.xlsx', drive_folder_id='TU_FOLDER_ID')
```

---

## ⏰ Automatización

### Opción 1: Google Apps Script (Recomendado)

Crear un script en Google Apps Script que ejecute el notebook:

```javascript
// Google Apps Script
function runColabNotebook() {
  // URL del notebook (debe estar compartido públicamente o con service account)
  const notebookUrl = 'https://colab.research.google.com/drive/TU_NOTEBOOK_ID';
  
  // Ejecutar notebook (requiere configuración adicional)
  // O usar Colab API si está disponible
  
  // Alternativa: Usar Colab Scheduler (ver Opción 2)
}

// Trigger diario a las 8:00 AM
function createDailyTrigger() {
  ScriptApp.newTrigger('runColabNotebook')
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();
}
```

### Opción 2: Colab Scheduler (Más Simple)

Usar extensiones de Colab para scheduling:

```python
# Instalar colab-scheduler
!pip install -q colab-scheduler

from colab_scheduler import scheduler

# Programar ejecución diaria
scheduler.schedule(
    notebook_url='https://colab.research.google.com/drive/TU_NOTEBOOK_ID',
    schedule='daily',
    time='08:00'
)
```

### Opción 3: Manual (Para Desarrollo)

Simplemente ejecutar: `Runtime > Run All` cuando quieras actualizar.

---

## 🔄 Migración desde Local

### Paso 1: Adaptar Scripts

Los scripts actuales funcionan en Colab con mínimos cambios:

```python
# ANTES (local):
# df = pd.read_csv('fuentes/catalogo_trade_unity.csv')

# DESPUÉS (Colab):
# Opción 1: Subir archivo a Colab
from google.colab import files
uploaded = files.upload()
df = pd.read_csv('catalogo_trade_unity.csv')

# Opción 2: Leer desde Drive
drive.mount('/content/drive')
df = pd.read_csv('/content/drive/MyDrive/ETL Trade Unity/fuentes/catalogo_trade_unity.csv')

# Opción 3: Leer desde BigQuery (mejor)
query = "SELECT * FROM `project.dataset.catalog`"
df = pd.read_gbq(query, credentials=credentials)
```

### Paso 2: Reemplazar Outputs

```python
# ANTES (local):
# df.to_excel('outputs/analisis.xlsx', index=False)

# DESPUÉS (Colab):
# Opción 1: Escribir a Sheets (automático)
write_to_sheets(df, "TradeUnity Analysis", "Sheet1")

# Opción 2: Generar Excel y subir a Drive
df.to_excel('/tmp/analisis.xlsx', index=False)
upload_to_drive('/tmp/analisis.xlsx')
```

### Paso 3: Organizar Notebook

Dividir en secciones claras con markdown cells:

```markdown
# ETL Trade Unity - Pipeline Completo

## 1. Setup
## 2. Extract
## 3. Transform
## 4. Analyze
## 5. Output
```

---

## 📝 Checklist de Migración

### Setup Inicial
- [ ] Crear notebook en Colab
- [ ] Instalar dependencias
- [ ] Configurar autenticación (service account o interactiva)
- [ ] Configurar Secrets (tokens, credenciales)

### Adaptar Scripts
- [ ] Adaptar extractores (BigQuery, Magento, etc.)
- [ ] Adaptar transformers
- [ ] Adaptar análisis (leer desde DataFrames en memoria)
- [ ] Adaptar outputs (escribir a Sheets/Drive)

### Testing
- [ ] Probar extracción de cada fuente
- [ ] Probar escritura a Sheets
- [ ] Probar generación de Excel
- [ ] Probar subida a Drive
- [ ] Validar que outputs sean correctos

### Automatización
- [ ] Configurar trigger (Apps Script o Scheduler)
- [ ] Probar ejecución automática
- [ ] Configurar notificaciones (opcional)

---

## 🎯 Próximos Pasos

1. **Crear notebook base** en Colab
2. **Migrar primer extractor** (BigQuery) como prueba
3. **Probar escritura a Sheets**
4. **Migrar resto de extractores**
5. **Adaptar análisis**
6. **Configurar automatización**

---

**Última actualización:** Febrero 2026
