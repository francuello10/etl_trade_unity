import csv
import math
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Set

import requests
from tqdm import tqdm

# =========================================================
# HARDCODE (como pediste)
# =========================================================
API_URL = "https://www.tradeunity.com.ar/rest/V1/orders"
API_TOKEN = "ih8enp7eks5g2ddp170zlj4bdckyjjpl"

PAGE_SIZE = 100              # 50/100/200 según el server
MAX_WORKERS = 16             # si te rate-limitea, bajalo a 8
REQUEST_TIMEOUT = 120

# Enrichment (catálogo actual)
ENRICH_PRODUCTS = True
INCLUDE_CATEGORY_NAMES = True      # OJO: puede ser muy lento
BRAND_ATTRIBUTE_CODES = ["manufacturer", "brand", "marca"]  # probamos en este orden

RAW_CSV = "ventas_historicas_items_raw.csv"
OUT_CSV = "ventas_historicas_items_enriched.csv"


# =========================================================
# HTTP helpers (robustos con backoff)
# =========================================================
_thread_local = threading.local()

def _get_session() -> requests.Session:
    """Una Session por thread (requests.Session no es thread-safe)."""
    if getattr(_thread_local, "session", None) is None:
        s = requests.Session()
        s.headers.update({
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        _thread_local.session = s
    return _thread_local.session

def http_get_json(url: str, params: Optional[Dict[str, str]] = None, max_retries: int = 8) -> Any:
    backoff = 1.0
    last_err = None
    for _ in range(max_retries):
        try:
            r = _get_session().get(url, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()

            # retry transient
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(backoff, 30))
                backoff *= 2
                continue

            # hard fail
            raise RuntimeError(f"HTTP {r.status_code} | {url} | {r.text[:800]}")
        except Exception as e:
            last_err = e
            time.sleep(min(backoff, 30))
            backoff *= 2
    raise RuntimeError(f"Max retries excedido | {url} | last_err={last_err}")


# =========================================================
# Magento endpoints
# =========================================================
REST_ROOT = API_URL[:-len("/orders")]  # ".../rest/V1"

def fetch_orders_page(page: int) -> Dict[str, Any]:
    # Sin filtros: trae todo. Le damos sort para estabilidad.
    params = {
        "searchCriteria[sortOrders][0][field]": "created_at",
        "searchCriteria[sortOrders][0][direction]": "ASC",
        "searchCriteria[pageSize]": str(PAGE_SIZE),
        "searchCriteria[currentPage]": str(page),
    }
    return http_get_json(API_URL, params=params)

def get_custom_attr(product_json: Dict[str, Any], code: str) -> Optional[Any]:
    for a in product_json.get("custom_attributes", []) or []:
        if a.get("attribute_code") == code:
            return a.get("value")
    return None

def fetch_product(sku: str) -> Dict[str, Any]:
    sku = (sku or "").strip()
    if not sku:
        return {}
    url = f"{REST_ROOT}/products/{requests.utils.quote(sku, safe='')}"
    try:
        return http_get_json(url)
    except Exception:
        return {}

def fetch_attribute_options(attribute_code: str) -> Dict[str, str]:
    url = f"{REST_ROOT}/products/attributes/{requests.utils.quote(attribute_code, safe='')}/options"
    try:
        data = http_get_json(url) or []
    except Exception:
        return {}
    m = {}
    for opt in data:
        v = str(opt.get("value", "")).strip()
        l = str(opt.get("label", "")).strip()
        if v:
            m[v] = l
    return m

def fetch_category_name(cat_id: str) -> str:
    cat_id = str(cat_id).strip()
    if not cat_id:
        return ""
    url = f"{REST_ROOT}/categories/{requests.utils.quote(cat_id, safe='')}"
    try:
        data = http_get_json(url)
        return str(data.get("name", "")).strip()
    except Exception:
        return ""


# =========================================================
# Logic: configurable/bundle -> precio efectivo
# =========================================================
def effective_item_values(item: Dict[str, Any], parent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Si el child trae 0/None y hay parent, usamos valores del parent.
    """
    def pick(field: str):
        v = item.get(field)
        if parent and (v is None or v == 0 or v == 0.0):
            pv = parent.get(field)
            return pv if pv is not None else v
        return v

    return {
        "original_price": pick("original_price"),
        "price": pick("price"),
        "price_incl_tax": pick("price_incl_tax"),
        "discount_amount": pick("discount_amount"),
        "discount_percent": pick("discount_percent"),
        "row_total": pick("row_total"),
        "row_total_incl_tax": pick("row_total_incl_tax"),
        "tax_percent": pick("tax_percent"),
        "tax_amount": pick("tax_amount"),
    }


# =========================================================
# Export Paso 1: Orders -> RAW CSV (sin enrich) + set de SKUs
# =========================================================
RAW_HEADERS = [
    # Order header
    "increment_id", "entity_id", "created_at", "updated_at", "status",
    "customer_email", "customer_firstname", "customer_lastname", "customer_taxvat",
    "order_currency_code", "base_currency_code", "currency_rate",
    "grand_total", "subtotal", "discount_amount_order", "shipping_amount", "tax_amount_order",
    # Item
    "item_id", "parent_item_id", "product_type", "sku", "name", "qty_ordered",
    "original_price", "price", "price_incl_tax",
    "discount_amount_item", "discount_percent_item",
    "row_total", "row_total_incl_tax",
    "tax_percent_item", "tax_amount_item",
]

def export_raw_and_collect_skus() -> Set[str]:
    first = fetch_orders_page(1)
    total_count = int(first.get("total_count", 0) or 0)
    total_pages = max(1, math.ceil(total_count / PAGE_SIZE)) if total_count else 1

    sku_set: Set[str] = set()

    with open(RAW_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(RAW_HEADERS)

        def process_page(data: Dict[str, Any]):
            orders = data.get("items", []) or []
            for o in orders:
                inc = o.get("increment_id", "")
                entity_id = o.get("entity_id", "")
                created = o.get("created_at", "")
                updated = o.get("updated_at", "")
                status = o.get("status", "")

                email = o.get("customer_email", "")
                fn = o.get("customer_firstname", "")
                ln = o.get("customer_lastname", "")
                taxvat = o.get("customer_taxvat", "")

                order_currency = o.get("order_currency_code", "")
                base_currency = o.get("base_currency_code", "")
                currency_rate = (o.get("extension_attributes") or {}).get("currency_rate", "")

                grand_total = o.get("grand_total", "")
                subtotal = o.get("subtotal", "")
                discount_amount_order = o.get("discount_amount", "")
                shipping_amount = o.get("shipping_amount", "")
                tax_amount_order = o.get("tax_amount", "")

                items = o.get("items", []) or []
                items_by_id = {str(i.get("item_id")): i for i in items if i.get("item_id") is not None}

                for it in items:
                    parent = items_by_id.get(str(it.get("parent_item_id"))) if it.get("parent_item_id") else None
                    eff = effective_item_values(it, parent)

                    sku = str(it.get("sku", "") or "").strip()
                    if sku:
                        sku_set.add(sku)

                    w.writerow([
                        inc, entity_id, created, updated, status,
                        email, fn, ln, taxvat,
                        order_currency, base_currency, currency_rate,
                        grand_total, subtotal, discount_amount_order, shipping_amount, tax_amount_order,
                        it.get("item_id", ""), it.get("parent_item_id", ""), it.get("product_type", ""),
                        sku, it.get("name", ""), it.get("qty_ordered", ""),
                        eff["original_price"], eff["price"], eff["price_incl_tax"],
                        eff["discount_amount"], eff["discount_percent"],
                        eff["row_total"], eff["row_total_incl_tax"],
                        eff["tax_percent"], eff["tax_amount"],
                    ])

        # page 1
        process_page(first)

        # restantes
        for page in tqdm(range(2, total_pages + 1), desc="Descargando orders", unit="page"):
            data = fetch_orders_page(page)
            process_page(data)

    print(f"OK RAW -> {RAW_CSV}")
    print(f"SKUs únicos detectados: {len(sku_set)}")
    return sku_set


# =========================================================
# Enrichment: SKU -> category_ids/names + brand (cache + paralelismo)
# =========================================================
def enrich_skus(skus: Set[str]) -> Dict[str, Tuple[str, str, str]]:
    """
    Return mapping:
      sku -> (category_ids_str, category_names_str, brand_str)
    """
    product_cache: Dict[str, Dict[str, Any]] = {}
    brand_options_cache: Dict[str, Dict[str, str]] = {}
    category_name_cache: Dict[str, str] = {}

    def get_brand_label(product_json: Dict[str, Any]) -> str:
        for code in BRAND_ATTRIBUTE_CODES:
            v = get_custom_attr(product_json, code)
            if v is None or str(v).strip() == "":
                continue

            s = str(v).strip()
            # si es option_id, mapear con options del mismo code
            if s.isdigit():
                if code not in brand_options_cache:
                    brand_options_cache[code] = fetch_attribute_options(code)
                return brand_options_cache[code].get(s, s)
            return s
        return ""

    def get_category_ids(product_json: Dict[str, Any]) -> List[str]:
        cat_ids = get_custom_attr(product_json, "category_ids")
        if cat_ids is None:
            links = (product_json.get("extension_attributes") or {}).get("category_links") or []
            cat_ids = [str(x.get("category_id")) for x in links if x.get("category_id") is not None]

        if isinstance(cat_ids, str):
            cat_ids = [c.strip().strip("'").strip('"')
                       for c in cat_ids.replace("[", "").replace("]", "").split(",")
                       if c.strip()]
        elif isinstance(cat_ids, (list, tuple)):
            cat_ids = [str(x).strip() for x in cat_ids if str(x).strip()]
        else:
            cat_ids = []
        return cat_ids

    def get_category_names(cat_ids: List[str]) -> List[str]:
        if not INCLUDE_CATEGORY_NAMES:
            return []
        names = []
        for cid in cat_ids:
            if cid in category_name_cache:
                nm = category_name_cache[cid]
            else:
                nm = fetch_category_name(cid)
                category_name_cache[cid] = nm
            if nm:
                names.append(nm)
        return names

    def enrich_one(sku: str) -> Tuple[str, str, str, str]:
        # (sku, cat_ids_str, cat_names_str, brand)
        if sku in product_cache:
            p = product_cache[sku]
        else:
            p = fetch_product(sku)
            product_cache[sku] = p

        if not p:
            return (sku, "", "", "")

        cat_ids = get_category_ids(p)
        cat_names = get_category_names(cat_ids)
        brand = get_brand_label(p)

        cat_ids_str = "|".join(cat_ids) if cat_ids else ""
        cat_names_str = "|".join([x for x in cat_names if x]) if cat_names else ""
        return (sku, cat_ids_str, cat_names_str, brand)

    out: Dict[str, Tuple[str, str, str]] = {}

    sku_list = sorted(list(skus))
    print(f"Enrich SKUs: {len(sku_list)} | workers={MAX_WORKERS} | category_names={INCLUDE_CATEGORY_NAMES}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(enrich_one, sku): sku for sku in sku_list}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Enriqueciendo productos", unit="sku"):
            sku, cat_ids_str, cat_names_str, brand = fut.result()
            out[sku] = (cat_ids_str, cat_names_str, brand)

    return out


# =========================================================
# Paso 3: RAW -> OUT CSV (agrega columnas enrich)
# =========================================================
def build_final_csv(enrich_map: Dict[str, Tuple[str, str, str]]) -> None:
    out_headers = RAW_HEADERS + ["category_ids", "category_names", "brand"]

    with open(RAW_CSV, "r", newline="", encoding="utf-8") as fin, \
         open(OUT_CSV, "w", newline="", encoding="utf-8") as fout:

        r = csv.DictReader(fin)
        w = csv.writer(fout)
        w.writerow(out_headers)

        for row in tqdm(r, desc="Construyendo CSV final", unit="row"):
            sku = (row.get("sku") or "").strip()
            cat_ids, cat_names, brand = ("", "", "")
            if sku and sku in enrich_map:
                cat_ids, cat_names, brand = enrich_map[sku]

            w.writerow([row.get(h, "") for h in RAW_HEADERS] + [cat_ids, cat_names, brand])

    print(f"OK FINAL -> {OUT_CSV}")


def main():
    # sanity quick check
    try:
        _ = fetch_orders_page(1)
    except Exception as e:
        raise SystemExit(f"Error conectando a Magento. Revisá token/URL. Detalle: {e}")

    skus = export_raw_and_collect_skus()

    if ENRICH_PRODUCTS:
        enrich_map = enrich_skus(skus)
        build_final_csv(enrich_map)
    else:
        print("ENRICH_PRODUCTS=False -> ya tenés el RAW CSV.")


if __name__ == "__main__":
    main()
