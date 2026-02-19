# Trade Unity (TU) — Documento base

> Documento vivo para uso interno: definición, alcance, propuesta de valor, operación y stack.

## 0) Relación con Comprando en Grupo (CEG)

Trade Unity es una **empresa hermana** de **Comprando en Grupo (CEG)**.

- **CEG** es la compañía “madre” del ecosistema: diseña y opera modelos de **importación** (estándar / express / directa-personalizada), desarrolla producto en origen y sostiene parte del know‑how de sourcing, calidad y logística.
- **TU** es el **canal ecommerce B2B** para **comercializar** (y operar) ese mix de productos y condiciones comerciales de forma digital, escalable y con integración a ERP.

### Marcas propias del grupo (CEG)

> Marcas propias del grupo (según catálogo TU cargado en plataforma) y su presencia relativa.

- **Kuest** — movilidad, deportes y fitness.
- **Barovo** — máquinas y herramientas (incluye plataforma inalámbrica “ION MAX”).
- **Kushiro** — outdoor/camping y línea térmica.
- **Miyawa** — maquinaria y herramientas.
- **Etheos** — electricidad e iluminación.
- **Gloa** — sanitarios, griferías, vanitory y accesorios.
- **Vonne** — hogar / cocina (electro y equipamiento).

**Peso en catálogo TU (base actual):** en el archivo de catálogo cargado, TU tiene **3.615 productos** y **80 marcas**; las **7 marcas propias** representan **~84%** del total de productos publicados.

**Ejemplos de marcas no propias presentes en catálogo (muestra):** Tramontina, MEISO, Mor, Porto Brasil, Tubofusión, OU, Floridis, Brickell (entre otras).

### Rubros que comercializamos (alto nivel)

Rubros principales (según “Categoría (2° Nivel)” del catálogo TU actual; ordenado por cantidad de productos):

- **Máquinas y Herramientas**
- **Hogar y Bazar**
- **Electricidad e Iluminación**
- **Sanitarios y Griferías**
- **Outdoor y Camping**

Rubros secundarios (menor participación por cantidad de productos, pero presentes):

- **Movilidad y Rodados**
- **Deportes y Entretenimiento**
- **Electrónica y Accesorios**

> Nota: la taxonomía final (nombres de categorías y jerarquía) conviene validarla contra Magento/Odoo para evitar diferencias entre “catálogo analítico” y “categorías visibles” en el sitio.

## 1) Definición

**Trade Unity (TU)** es un **ecommerce B2B** orientado a **venta mayorista** y **operaciones corporativas**, diseñado para habilitar compras de volumen con **reglas comerciales** (precios por escala, descuentos por rangos, condiciones por medio de pago), e integrado con un **ERP** para ejecutar la operación end‑to‑end (stock, pedidos, facturación, logística y postventa).

En la práctica, TU permite que clientes B2B (empresas) puedan:

- Registrarse y operar con reglas de alta/validación (incluyendo datos fiscales).
- Comprar un catálogo amplio con precios y escalas (incluyendo lógica de stock limitado).
- Acceder a condiciones comerciales por monto y medio de pago (transferencia, eCheqs, etc.).
- Coordinar envíos mediante transportistas y reglas de shipping (incluye excepciones fiscales/regionales).
- Integrar el ciclo de compra con procesos internos (ERP, facturación, logística, soporte).

## 2) Problema que resuelve

TU reduce fricciones típicas del B2B:

- **Compra mayorista** (carritos grandes, repetición de SKUs, packs/caja madre).
- **Condiciones comerciales complejas** (por monto, por método de pago, por cliente/segmento).
- **Stock y disponibilidad** (verificación/sincronización; stock asignado por cotizaciones/carritos).
- **Operación end‑to‑end** (alta → pricing → orden → pago → factura → despacho → postventa).
- **Crecimiento vía segmentación** (automatización y campañas por comportamiento).

## 3) Propuesta de valor

- **UX simple con reglas B2B potentes** (navegación/checkout con lógica comercial/operativa).
- **Precios y escalas dinámicas** (segmentación por customer group; escalas permanentes y promos).
- **Operación integrada** (sincronización de órdenes, clientes, stock y logística entre ecommerce y ERP).
- **Automatización comercial y marketing** (segmentos y triggers con email/WhatsApp).
- **Analítica accionable** (datasets y tableros: LTV, recencia/frecuencia, clusters, top productos).



## 4) Stack tecnológico

### 4.1 Ecommerce

- **Magento 2** (2.4.5‑p14 → upgrade/migración a 2.4.8‑p3).
- Personalizaciones típicas:
  - Reglas de shipping (free shipping por monto y por SKU “gatillo”).
  - Checkout con percepciones/IVA y customer groups especiales (ej.: Tierra del Fuego sin IVA).
  - Selección/visualización de transportista (default para asociados CEG vs opciones para no asociados).
  - Backoffice para órdenes y mejoras en eCheqs.
  - QA exploratorio de flujos: alta, navegación, compras.

### 4.2 ERP / Backoffice

- **Odoo** (17/18 con migración hacia 19 en frentes).
- Integración ecommerce↔ERP mediante conector (mencionado: **Emipro**).
- Flujos: alta clientes, sincronización órdenes, facturación, logística y stock.

### 4.3 Marketing

- **Connectif**: segmentación dinámica, campañas (email/WhatsApp), triggers (carritos abandonados, leads, etc.).

### 4.4 Datos y analítica

- **Google Sheets** (operación/analítica).
- **Google Apps Script** (automatizaciones y pipelines de datos).
- **Looker Studio** (tableros) y, cuando aplica, **BigQuery**.

## 5) Flujos operativos clave

### 5.1 Alta y gestión de clientes

- Registro/alta en Magento con datos fiscales y empresa.
- Validación y asignación a customer groups (segmento comercial, régimen fiscal, provincia, etc.).
- Alta inmediata / masiva / desde Odoo con invitación para setear contraseña.

### 5.2 Catálogo, precios y promos

- Catálogo con SKUs comerciales (packs/caja madre) y metadata.
- Lógica de precios: “precio plataforma”, escalas, descuentos por rango y promos (ej.: liquidación stock).
- Condiciones por medio de pago: transferencia vs eCheqs (plazos).

### 5.3 Checkout e impuestos

- Visualización de percepciones y particularidades fiscales.
- Excepciones por cliente/grupo (ej.: sin IVA TDF).
- Shipping condicionado por monto, por SKUs y por transportista.

### 5.4 Órdenes, facturación y postventa

- Sincronización de órdenes al ERP.
- Ajustes comerciales controlados (NCs, bonificaciones, diferencias por pricing acordado).
- Facturación condicionada a validaciones (ej.: eCheqs recibidos/validados).

### 5.5 Logística

- Matrices de envío por zona
- Transferencias internas de stock y operación de almacén.

## 6) Principios de operación (para alinear criterios)

- **No romper operación por promos**: respetar precios de ventas recientes para evitar reclamos/NCs.
- **Reglas trazables**: descuentos por rango y medio de pago siempre documentados.
- **Datos como sistema nervioso**: todo cambio relevante debe reflejarse en dataset/tablero.
- **Automatización con control**: scripts con metadata (última corrida), locks y logs.

## 7) Glosario mínimo

- **SKU**: identificador del producto.
- **Caja madre / Box Qty**: unidad de empaque comercial (packs).
- **LTV / CLTV**: valor de vida del cliente.
- **Recencia/Frecuencia**: días desde última compra / compras por período.
- **eCheq**: instrumento de pago diferido (plazos).
- **NC**: nota de crédito (ajuste).
- **Percepciones**: retenciones/percepciones fiscales.


## Anexo A — One‑liner

**Trade Unity es un ecommerce B2B mayorista que integra Magento + Odoo para operar catálogo, precios por escala, compras corporativas, pagos diferidos y logística, con automatización de marketing y analítica para segmentación y crecimiento.**

