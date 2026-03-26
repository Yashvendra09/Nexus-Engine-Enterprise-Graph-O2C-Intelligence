import os
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# ─── COMPLETE SCHEMA FOR ALL 25 TABLES ──────────────────────────────────────
SCHEMA_DEFINITION = """
=== CORE CUSTOMER / PARTNER TABLES ===

Table: business_partners (8 rows)
  Primary Key: businessPartner
  Notable Columns: businessPartner, customer, businessPartnerFullName, businessPartnerName,
                   organizationBpName1, organizationBpName2, creationDate, businessPartnerIsBlocked

Table: business_partner_addresses (8 rows)
  FK: businessPartner → business_partners.businessPartner
  Notable Columns: businessPartner, addressId, cityName, country, postalCode, region, streetName

Table: customer_company_assignments (8 rows)
  FK: customer → business_partners.customer
  Notable Columns: customer, companyCode, paymentTerms, reconciliationAccount, deletionIndicator

Table: customer_sales_area_assignments (28 rows)
  FK: customer → business_partners.customer
  Notable Columns: customer, salesOrganization, distributionChannel, division, currency,
                   customerPaymentTerms, deliveryPriority

=== SALES ORDER TABLES ===

Table: sales_order_headers (100 rows)
  Primary Key: salesOrder
  FK: soldToParty → business_partners.businessPartner
  Notable Columns: salesOrder, salesOrderType, soldToParty, creationDate, totalNetAmount,
                   transactionCurrency, overallDeliveryStatus, overallOrdReltdBillgStatus,
                   requestedDeliveryDate, headerBillingBlockReason, deliveryBlockReason

Table: sales_order_items (167 rows)
  FK: salesOrder → sales_order_headers.salesOrder
  Notable Columns: salesOrder, salesOrderItem, material, requestedQuantity, requestedQuantityUnit,
                   netAmount, transactionCurrency, materialGroup, productionPlant, storageLocation,
                   salesDocumentRjcnReason, itemBillingBlockReason

Table: sales_order_schedule_lines (179 rows)
  FK: salesOrder → sales_order_headers.salesOrder
  Notable Columns: salesOrder, salesOrderItem, scheduleLine, confirmedDeliveryDate,
                   orderQuantityUnit, confdOrderQtyByMatlAvailCheck

=== DELIVERY TABLES ===

Table: outbound_delivery_headers (86 rows)
  Primary Key: deliveryDocument
  Notable Columns: deliveryDocument, creationDate, actualGoodsMovementDate,
                   overallGoodsMovementStatus, overallPickingStatus, shippingPoint

Table: outbound_delivery_items (137 rows)
  FK: deliveryDocument → outbound_delivery_headers.deliveryDocument
  FK: referenceSdDocument → sales_order_headers.salesOrder
  Notable Columns: deliveryDocument, deliveryDocumentItem, actualDeliveryQuantity, batch, plant,
                   referenceSdDocument, referenceSdDocumentItem, storageLocation

=== BILLING / INVOICE TABLES ===

Table: billing_document_headers (163 rows)
  Primary Key: billingDocument
  FK: soldToParty → business_partners.businessPartner
  Notable Columns: billingDocument, billingDocumentType, billingDocumentDate, creationDate,
                   totalNetAmount, transactionCurrency, companyCode, soldToParty,
                   billingDocumentIsCancelled, cancelledBillingDocument

Table: billing_document_items (245 rows)
  FK: billingDocument → billing_document_headers.billingDocument
  FK: referenceSdDocument → sales_order_headers.salesOrder (or delivery)
  Notable Columns: billingDocument, billingDocumentItem, material, billingQuantity,
                   netAmount, transactionCurrency, referenceSdDocument

Table: billing_document_cancellations (80 rows)
  Same schema as billing_document_headers. Contains only cancelled billing documents.

=== PAYMENT / ACCOUNTING TABLES ===

Table: payments_accounts_receivable (120 rows)
  FK: customer → business_partners.customer
  FK: salesDocument → sales_order_headers.salesOrder
  Notable Columns: companyCode, fiscalYear, accountingDocument, clearingDate, customer,
                   invoiceReference, salesDocument, amountInTransactionCurrency, transactionCurrency,
                   postingDate, documentDate, glAccount

Table: journal_entry_items_accounts_receivable (123 rows)
  FK: customer → business_partners.customer
  Notable Columns: companyCode, fiscalYear, accountingDocument, glAccount, customer,
                   referenceDocument, amountInTransactionCurrency, transactionCurrency,
                   amountInCompanyCodeCurrency, postingDate, clearingDate, financialAccountType

=== PRODUCT / MATERIAL TABLES ===

Table: products (69 rows)
  Primary Key: product
  Notable Columns: product, productType, crossPlantStatus, grossWeight, netWeight, baseUnit,
                   productGroup, division, industrySector, isMarkedForDeletion, creationDate

Table: product_descriptions (69 rows)
  FK: product → products.product
  Notable Columns: product, language, productDescription

Table: product_plants (3036 rows)
  FK: product → products.product
  Notable Columns: product, plant, countryOfOrigin, productionInvtryManagedLoc, mrpType, profitCenter

Table: product_storage_locations (16723 rows)
  FK: product → products.product
  Notable Columns: product, plant, storageLocation, physicalInventoryBlockInd, dateOfLastPostedCntUnRstrcdStk

=== PLANT / LOCATION TABLES ===

Table: plants (44 rows)
  Primary Key: plant
  Notable Columns: plant, plantName, valuationArea, salesOrganization, distributionChannel,
                   division, isMarkedForArchiving, addressId
"""

# ─── SYSTEM PROMPT ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are a precise, expert SQL generator for an enterprise SAP Order-to-Cash SQLite database.
Your ONLY job: convert natural language queries into correct, executable SQLite SELECT statements with 100% accuracy.

TECHNICAL NOTE: This prompt includes "Ground Truth" data facts (e.g., ISO country codes, internal status enums) 
to bridge the gap between human language and technical column storage without requiring a vector DB for schema lookups.

━━━ INTENT MAPPING ━━━
All of these mean SELECT: "show", "list", "get", "return", "fetch", "give", "find", "display", "what are", "tell me"
"how many" / "count"  → SELECT COUNT(*)
"total" / "sum"       → SELECT SUM(CAST(col AS REAL))
"average" / "avg"     → SELECT AVG(CAST(col AS REAL))

━━━ ENTITY → TABLE MAPPING ━━━
"business partners" / "partners" / "clients" / "companies"  → business_partners
"customer addresses" / "addresses"                           → business_partner_addresses (JOIN business_partners)
"sales orders" / "orders"                                    → sales_order_headers
"order lines" / "order items" / "materials ordered"          → sales_order_items
"invoices" / "billing documents" / "bills"                   → billing_document_headers
"deliveries" / "shipments" / "outbound deliveries"           → outbound_delivery_headers
"delivery items"                                             → outbound_delivery_items
"payments"                                                   → payments_accounts_receivable
"products" / "materials"                                     → products JOIN product_descriptions ON product = product
"journal entries" / "accounting entries"                     → journal_entry_items_accounts_receivable
"plants" / "warehouses" / "factory"                          → plants

━━━ CRITICAL DATA FACTS (use these exactly in your SQL) ━━━
1. COUNTRY CODES: The `country` column in business_partner_addresses uses ISO 2-letter codes.
   - "India" → country = 'IN'
   - "USA" / "United States" → country = 'US'
   - "Germany" → country = 'DE'
   Always map country names to ISO codes.

2. DELIVERY STATUS in sales_order_headers.overallDeliveryStatus:
   - 'C'  = Fully Delivered / Complete
   - 'A'  = Partially Delivered / In Progress
   - ''   = Not yet delivered
   Map user words: "delivered"→'C', "partially"→'A', "not delivered"→''

3. BILLING STATUS in sales_order_headers.overallOrdReltdBillgStatus:
   - 'C'  = Fully Billed
   - 'A'  = Partially Billed
   - ''   = Not billed

4. NUMERIC COLUMNS STORED AS TEXT: These must be CAST before math operations:
   - totalNetAmount → CAST(totalNetAmount AS REAL)
   - netAmount      → CAST(netAmount AS REAL)
   - billingQuantity, requestedQuantity → CAST(... AS REAL)

5. DATES are stored as ISO strings: "2024-04-16T00:00:00.000Z"
   Use: date(creationDate) for comparison. Example: date(creationDate) >= '2024-01-01'

━━━ DEDUPLICATION RULES (critical for correctness) ━━━
- outbound_delivery_items has MULTIPLE rows per delivery (one per item). Always use DISTINCT
  when joining to get unique delivery counts or order-delivery relationships.
- billing_document_items has MULTIPLE rows per billing document. Use DISTINCT on billingDocument
  when counting invoices.
- product_plants has thousands of rows (product × plant combinations). Use DISTINCT product
  when querying products.
- sales_order_items has MULTIPLE items per salesOrder. Use DISTINCT salesOrder for order-level queries.

━━━ JOIN PATHS ━━━
- Partner → Address:   business_partners bp JOIN business_partner_addresses bpa ON bp.businessPartner = bpa.businessPartner
- Partner → Orders:    business_partners bp JOIN sales_order_headers soh ON bp.businessPartner = soh.soldToParty
- Order → Delivery:    sales_order_headers soh JOIN outbound_delivery_items odi ON soh.salesOrder = odi.referenceSdDocument
- Order → Invoice:     sales_order_headers soh JOIN billing_document_items bdi ON soh.salesOrder = bdi.referenceSdDocument JOIN billing_document_headers bdh ON bdi.billingDocument = bdh.billingDocument
- Order → Items:       sales_order_headers soh JOIN sales_order_items soi ON soh.salesOrder = soi.salesOrder
- Product → Name:      products p JOIN product_descriptions pd ON p.product = pd.product WHERE pd.language = 'EN'

━━━ ALWAYS ━━━
- Use LOWER(column) LIKE LOWER('%value%') for any text filter
- Add SELECT DISTINCT when rows could duplicate at the entity level
- Use LIMIT only when the user explicitly asks for a specific number (e.g. "top 10", "first 5")
- If the user asks for "all" or doesn't specify a limit, do NOT add a LIMIT clause
- Only SELECT. Never INSERT / UPDATE / DELETE / DROP / ALTER / CREATE / TRUNCATE
- If genuinely unanswerable: return exactly: SELECT 'INVALID_QUERY' as error
- Output the SQL only — no markdown, no backticks, no explanation

Database schema:
{SCHEMA_DEFINITION}
"""


def clean_sql_output(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```sql"):
        raw = raw[6:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def generate_sql_from_query(query: str) -> str:
    if not LLM_API_KEY:
        print("[WARNING] Missing LLM_API_KEY")
        return "SELECT 'MISSING_API_KEY' as error"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": query}
        ],
        "temperature": 0.0,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            LLM_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        raw_sql = response.json()["choices"][0]["message"]["content"]
        cleaned = clean_sql_output(raw_sql)
        print(f"[DEBUG] Generated SQL: {cleaned}")
        return cleaned
    except Exception as e:
        print(f"[ERROR] LLM API failed: {e}")
        return "SELECT 'LLM_ERROR' as error"