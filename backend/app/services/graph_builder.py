import networkx as nx
import sqlite3
import os

def build_graph(db_path: str = "supply_chain.db") -> nx.DiGraph:
    """
    Constructs a directed graph representing the SAP Order-to-Cash data relationships.
    Ontology: Partner -> Order -> Item -> Product / Delivery / Invoice
    """
    graph = nx.DiGraph()
    
    # Resolve absolute path for database file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Back out of services/ if needed or just use current directory
    db_abs_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), db_path)
    
    if not os.path.exists(db_abs_path):
        # Fallback for different run contexts
        db_abs_path = os.path.join(os.getcwd(), db_path)

    try:
        conn = sqlite3.connect(db_abs_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
    except Exception as e:
        print(f"Graph builder failed to connect to DB: {e}")
        return graph

    # 1. ADD ENTITY NODES
    _add_partner_nodes(graph, cur)
    _add_sales_order_nodes(graph, cur)
    _add_delivery_nodes(graph, cur)
    _add_billing_nodes(graph, cur)
    
    # 2. ADD RELATIONSHIP EDGES
    _add_order_to_partner_edges(graph, cur)
    _add_delivery_to_order_edges(graph, cur)
    _add_billing_to_order_edges(graph, cur)

    conn.close()
    return graph

def _add_partner_nodes(graph, cur):
    """Business Partners (Customers)"""
    try:
        cur.execute("SELECT * FROM business_partners")
        for row in cur.fetchall():
            attrs = dict(row)
            p_id = attrs.get('businessPartner')
            name = attrs.get('businessPartnerFullName') or attrs.get('businessPartnerName') or f"Partner {p_id}"
            graph.add_node(f"partner_{p_id}", id=str(p_id), type="partner", name=name, attributes=attrs)
    except sqlite3.OperationalError: pass

def _add_sales_order_nodes(graph, cur):
    """Sales Order Headers"""
    try:
        cur.execute("SELECT * FROM sales_order_headers")
        for row in cur.fetchall():
            attrs = dict(row)
            o_id = attrs.get('salesOrder')
            graph.add_node(f"order_{o_id}", id=str(o_id), type="order", name=f"Order {o_id}", attributes=attrs)
    except sqlite3.OperationalError: pass

def _add_delivery_nodes(graph, cur):
    """Outbound Delivery Headers"""
    try:
        cur.execute("SELECT * FROM outbound_delivery_headers")
        for row in cur.fetchall():
            attrs = dict(row)
            d_id = attrs.get('deliveryDocument')
            if d_id and d_id != 'None':
                graph.add_node(f"delivery_{d_id}", id=str(d_id), type="delivery", name=f"Delivery {d_id}", attributes=attrs)
    except sqlite3.OperationalError: pass

def _add_billing_nodes(graph, cur):
    """Billing (Invoices)"""
    try:
        cur.execute("SELECT * FROM billing_document_headers")
        for row in cur.fetchall():
            attrs = dict(row)
            b_id = attrs.get('billingDocument')
            if b_id and b_id != 'None':
                graph.add_node(f"billing_{b_id}", id=str(b_id), type="invoice", name=f"Invoice {b_id}", attributes=attrs)
    except sqlite3.OperationalError: pass

def _add_order_to_partner_edges(graph, cur):
    """Link Orders to SoldToParty"""
    try:
        cur.execute("SELECT salesOrder, soldToParty FROM sales_order_headers")
        for row in cur.fetchall():
            o, p = row['salesOrder'], row['soldToParty']
            if o and p:
                graph.add_edge(f"partner_{p}", f"order_{o}", relation="placed")
    except sqlite3.OperationalError: pass

def _add_delivery_to_order_edges(graph, cur):
    """Link Deliveries to Sales Orders via items"""
    try:
        cur.execute("SELECT DISTINCT deliveryDocument, referenceSdDocument FROM outbound_delivery_items")
        for row in cur.fetchall():
            d, o = row['deliveryDocument'], row['referenceSdDocument']
            if d and o:
                graph.add_edge(f"order_{o}", f"delivery_{d}", relation="shipped_as")
    except sqlite3.OperationalError: pass

def _add_billing_to_order_edges(graph, cur):
    """Link Invoices to Sales Orders via items"""
    try:
        cur.execute("SELECT DISTINCT billingDocument, referenceSdDocument FROM billing_document_items")
        for row in cur.fetchall():
            b, o = row['billingDocument'], row['referenceSdDocument']
            if b and o:
                graph.add_edge(f"order_{o}", f"billing_{b}", relation="invoiced_as")
    except sqlite3.OperationalError: pass

def graph_to_json(graph: nx.DiGraph) -> dict:
    """Serializes the graph for frontend consumption."""
    nodes = []
    for n, d in graph.nodes(data=True):
        nodes.append({
            "id": n,
            "type": d.get("type", "unknown"),
            "name": d.get("name", str(n)),
            "attributes": d.get("attributes", {})
        })
    
    edges = []
    for u, v, d in graph.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "relation": d.get("relation", "connected_to")
        })
        
    return {"nodes": nodes, "edges": edges}
