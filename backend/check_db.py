import sqlite3

conn = sqlite3.connect("supply_chain.db")
cur = conn.cursor()

print("=== business_partner_addresses country values ===")
rows = cur.execute("SELECT DISTINCT country FROM business_partner_addresses").fetchall()
print([r[0] for r in rows])

print("\n=== Sample rows ===")
rows = cur.execute("SELECT * FROM business_partner_addresses LIMIT 3").fetchall()
cols = [r[1] for r in cur.execute("PRAGMA table_info(business_partner_addresses)").fetchall()]
for r in rows:
    print(dict(zip(cols, r)))

print("\n=== plants sample country/region ===")
rows = cur.execute("SELECT DISTINCT plant, plantName FROM plants LIMIT 5").fetchall()
for r in rows:
    print(r)

print("\n=== sales_order_headers delivery status values ===")
rows = cur.execute("SELECT DISTINCT overallDeliveryStatus FROM sales_order_headers").fetchall()
print([r[0] for r in rows])

print("\n=== billing_document_headers sample ===")
rows = cur.execute("SELECT billingDocument, soldToParty, totalNetAmount, billingDocumentDate FROM billing_document_headers LIMIT 5").fetchall()
for r in rows:
    print(r)

print("\n=== outbound_delivery_items referenceSdDocument sample ===")
rows = cur.execute("SELECT deliveryDocument, referenceSdDocument FROM outbound_delivery_items LIMIT 5").fetchall()
for r in rows:
    print(r)

conn.close()
