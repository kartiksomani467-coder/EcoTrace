import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from decimal import Decimal
from db import get_connection

# =========================================================
# EcoTrace — Dark Operations Console
# Existing database: MySQL 8+, nine-table EcoTrace schema
# =========================================================
st.set_page_config(
    page_title="EcoTrace | Operations Console",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark interface: high contrast, emerald accent, compact navigation.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --bg: #080D0B;
  --panel: #101815;
  --panel2: #141F19;
  --border: #26362D;
  --text: #F1F7F2;
  --muted: #A1B2A6;
  --green: #39D98A;
  --green2: #1C9C61;
  --amber: #FFC857;
  --red: #FF6B6B;
}
.stApp { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; }
[data-testid="stHeader"] { background: rgba(8,13,11,.95); }
[data-testid="stToolbar"] { right: 1rem; }
.block-container { max-width: 1600px; padding-top: 1.4rem; padding-bottom: 3rem; }
h1,h2,h3,h4 { color: var(--text) !important; font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.3px; }
p, label, span, li, .stMarkdown { color: var(--text); }
small, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
[data-testid="stSidebar"] { background: #0D1410; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
[data-testid="stMetric"] {
  background: linear-gradient(145deg, #142019, #0F1713);
  border: 1px solid var(--border); border-radius: 15px; padding: 17px 18px;
  box-shadow: 0 8px 28px rgba(0,0,0,.13); min-height: 118px;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color: var(--muted) !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color: var(--green) !important; font-family: 'Space Grotesk',sans-serif !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { color: var(--muted) !important; }
.stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
  background: #0D1511 !important; color: var(--text) !important; border: 1px solid #34483B !important; border-radius: 9px !important;
}
[data-baseweb="select"] > div { background: #0D1511 !important; color: var(--text) !important; border-color: #34483B !important; }
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background: #111B15 !important; }
[data-baseweb="menu"] * { color: var(--text) !important; }
.stCheckbox label, .stRadio label, .stSelectbox label, .stMultiSelect label { color: var(--text) !important; }
div.stButton > button, div.stFormSubmitButton > button, .stDownloadButton button {
  background: var(--green2); color: #041109; border: 1px solid var(--green2); border-radius: 9px;
  min-height: 2.55rem; font-weight: 700; transition: all .15s ease;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover, .stDownloadButton button:hover {
  background: var(--green); border-color: var(--green); color: #041109;
}
div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
[data-testid="stExpander"] { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
[data-testid="stTabs"] button { color: var(--muted); }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--green); border-bottom-color: var(--green); }
[data-testid="stAlert"] { border-radius: 10px; }
hr { border-color: var(--border); }
.eco-hero {
  background: radial-gradient(circle at 88% 15%, rgba(57,217,138,.19), transparent 32%),
              linear-gradient(120deg, #122219 0%, #0E1712 70%, #10241A 100%);
  border: 1px solid #294737; border-radius: 19px; padding: 25px 28px; margin-bottom: 20px;
}
.eco-eyebrow { color: var(--green); font-size: .72rem; font-weight: 700; letter-spacing: 2px; }
.eco-hero h1 { font-size: 2.2rem; margin: 7px 0 3px; }
.eco-hero p { color: var(--muted) !important; margin: 0; }
.section-kicker { color: var(--green); font-size: .74rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)


# ----------------------------- DB utilities -----------------------------
def fetch_all(sql, params=()):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def transaction(callback):
    conn = get_connection()
    cur = conn.cursor()
    try:
        conn.start_transaction()
        result = callback(cur)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def df(rows):
    return pd.DataFrame(rows)


def inventory_data():
    return df(fetch_all("""
        SELECT i.item_id, i.sku, i.item_name, i.category_id,
               c.category_name, i.unit, i.is_perishable, i.reorder_level,
               i.is_active,
               COALESCE(SUM(b.quantity_available), 0) AS stock,
               COUNT(DISTINCT b.batch_id) AS batch_count,
               MIN(CASE WHEN b.quantity_available > 0 THEN b.expiry_date END) AS next_expiry
        FROM items i
        JOIN categories c ON c.category_id = i.category_id
        LEFT JOIN inventory_batches b ON b.item_id = i.item_id
        GROUP BY i.item_id, i.sku, i.item_name, i.category_id,
                 c.category_name, i.unit, i.is_perishable,
                 i.reorder_level, i.is_active
        ORDER BY i.item_name
    """))


def category_data():
    return df(fetch_all("""
        SELECT category_id, category_name, description,
               default_shelf_life_days, created_at
        FROM categories ORDER BY category_name
    """))


def supplier_data():
    return df(fetch_all("""
        SELECT supplier_id, supplier_name, contact_person, phone, email, address
        FROM suppliers ORDER BY supplier_name
    """))


def batch_data():
    return df(fetch_all("""
        SELECT b.batch_id, b.batch_code, b.item_id, i.sku, i.item_name,
               i.unit, b.quantity_received, b.quantity_available,
               b.received_date, b.shelf_life_days, b.expiry_date
        FROM inventory_batches b JOIN items i ON i.item_id=b.item_id
        ORDER BY b.expiry_date IS NULL, b.expiry_date, b.batch_id
    """))


def usage_data():
    return df(fetch_all("""
        SELECT DATE(u.consumed_at) AS usage_date, i.item_name, i.unit,
               SUM(u.quantity_consumed) AS quantity_consumed
        FROM usage_logs u
        JOIN inventory_batches b ON b.batch_id=u.batch_id
        JOIN items i ON i.item_id=b.item_id
        GROUP BY DATE(u.consumed_at), i.item_id, i.item_name, i.unit
        ORDER BY usage_date
    """))


def stock_label(stock, reorder):
    if stock <= 0:
        return "Out of stock"
    if stock <= reorder:
        return "Low stock"
    return "Healthy"


def expiry_label(value):
    if pd.isna(value):
        return "No expiry"
    days = (pd.Timestamp(value).normalize() - pd.Timestamp(date.today())).days
    if days < 0:
        return "Expired"
    if days <= 3:
        return "Expiring soon"
    return "Fresh"


def prepare_inventory(data):
    data = data.copy()
    if data.empty:
        return data
    data["stock"] = pd.to_numeric(data["stock"], errors="coerce").fillna(0)
    data["reorder_level"] = pd.to_numeric(data["reorder_level"], errors="coerce").fillna(0)
    data["next_expiry"] = pd.to_datetime(data["next_expiry"], errors="coerce")
    data["stock_status"] = data.apply(lambda r: stock_label(r["stock"], r["reorder_level"]), axis=1)
    data["expiry_status"] = data["next_expiry"].apply(expiry_label)
    return data


def error_message(exc):
    st.error(f"{type(exc).__name__}: {exc}")


def chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#101815",
        plot_bgcolor="#101815",
        font_color="#EAF3ED",
        margin=dict(l=10, r=10, t=35, b=10),
        colorway=["#39D98A", "#FFC857", "#7BB6FF", "#FF6B6B", "#B99AFF"],
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#26362D", zerolinecolor="#26362D")
    fig.update_yaxes(gridcolor="#26362D", zerolinecolor="#26362D")
    return fig


# ----------------------------- Navigation -----------------------------
with st.sidebar:
    st.markdown("<div style='font-size:2.3rem'>🌿</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin:0'>EcoTrace</h2>", unsafe_allow_html=True)
    st.caption("INVENTORY OPERATIONS")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Inventory",
            "Categories",
            "Batches & Stock",
            "Consumption",
            "Suppliers",
            "Purchases",
            "Reports",
        ],
        label_visibility="visible",
    )
    st.divider()
    st.caption("SYSTEM STATUS")
    st.markdown("🟢 MySQL connection configured")
    st.caption("Data is loaded from your local EcoTrace database.")
    if st.button("↻ Refresh data", use_container_width=True):
        st.rerun()

st.markdown("""
<div class="eco-hero">
  <div class="eco-eyebrow">SMART INVENTORY · SHELF-LIFE · MICRO-LOGISTICS</div>
  <h1>EcoTrace Operations Console</h1>
  <p>Know what you have, what needs attention, and what to do next.</p>
</div>
""", unsafe_allow_html=True)

try:
    categories = category_data()
    inventory = prepare_inventory(inventory_data())
    suppliers = supplier_data()
    batches = batch_data()
    usage = usage_data()
except Exception as exc:
    st.error("Could not load EcoTrace data. Check MySQL service and .env settings.")
    st.exception(exc)
    st.stop()

# ----------------------------- Overview -----------------------------
if page == "Overview":
    st.markdown('<div class="section-kicker">At a glance</div>', unsafe_allow_html=True)
    st.subheader("Inventory health")
    active = inventory[inventory["is_active"].astype(bool)].copy() if not inventory.empty else inventory
    total_stock = float(active["stock"].sum()) if not active.empty else 0
    low_count = int(active["stock_status"].isin(["Low stock", "Out of stock"]).sum()) if not active.empty else 0
    expired_count = int((active["expiry_status"] == "Expired").sum()) if not active.empty else 0
    soon_count = int((active["expiry_status"] == "Expiring soon").sum()) if not active.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active products", len(active))
    m2.metric("Available stock", f"{total_stock:,.2f}")
    m3.metric("Reorder attention", low_count)
    m4.metric("Expiry attention", expired_count + soon_count)

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Categories", len(categories))
    m6.metric("Tracked batches", len(batches))
    m7.metric("Suppliers", len(suppliers))
    m8.metric("Usage records", len(usage))

    if expired_count:
        st.error(f"⛔ {expired_count} product(s) have expired stock. Check batches before use.")
    if soon_count:
        st.warning(f"◷ {soon_count} product(s) have batches expiring within 3 days.")
    if low_count:
        st.warning(f"↓ {low_count} product(s) are at or below their reorder threshold.")
    if not any([expired_count, soon_count, low_count]):
        st.success("Inventory checks look clear based on current product-level data.")

    left, right = st.columns(2)
    with left:
        st.subheader("Stock by category")
        if not active.empty:
            grouped = active.groupby("category_name", as_index=False)["stock"].sum()
            fig = px.bar(grouped, x="category_name", y="stock", color="category_name")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        else:
            st.info("Add products to see inventory distribution.")
    with right:
        st.subheader("Consumption trend")
        if not usage.empty:
            daily = usage.groupby("usage_date", as_index=False)["quantity_consumed"].sum()
            fig = px.line(daily, x="usage_date", y="quantity_consumed", markers=True)
            fig.update_traces(line_color="#39D98A", line_width=3)
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        else:
            st.info("Consumption activity will appear here after usage is recorded.")

    st.subheader("Needs attention")
    if not active.empty:
        attention = active[
            active["stock_status"].isin(["Low stock", "Out of stock"])
            | active["expiry_status"].isin(["Expired", "Expiring soon"])
        ]
        if attention.empty:
            st.success("No low-stock or near-expiry products in this view.")
        else:
            st.dataframe(attention[[
                "sku", "item_name", "category_name", "stock", "unit",
                "stock_status", "next_expiry", "expiry_status"
            ]], use_container_width=True, hide_index=True)

# ----------------------------- Inventory -----------------------------
elif page == "Inventory":
    st.subheader("Product catalogue")
    st.caption("Create, search, edit and deactivate products.")

    with st.expander("＋ Create product", expanded=False):
        if categories.empty:
            st.warning("Create a category first in the Categories workspace.")
        else:
            cat_map = {r["category_name"]: int(r["category_id"]) for _, r in categories.iterrows()}
            with st.form("product_create"):
                a, b = st.columns(2)
                sku = a.text_input("SKU / unique product code")
                name = b.text_input("Product name")
                category_name = a.selectbox("Category", list(cat_map.keys()))
                unit = b.selectbox("Unit", ["piece", "pack", "bottle", "litre", "kg", "gram", "box", "carton"])
                reorder = a.number_input("Reorder threshold", min_value=0.0, value=5.0, step=1.0)
                perishable = b.checkbox("Perishable item", value=True)
                submit = st.form_submit_button("Create product")
                if submit:
                    if not sku.strip() or not name.strip():
                        st.error("SKU and product name are required.")
                    else:
                        try:
                            execute("""
                                INSERT INTO items (sku,item_name,category_id,unit,is_perishable,reorder_level)
                                VALUES (%s,%s,%s,%s,%s,%s)
                            """, (sku.strip(), name.strip(), cat_map[category_name], unit, perishable, reorder))
                            st.success("Product created.")
                            st.rerun()
                        except Exception as exc:
                            error_message(exc)

    q1, q2 = st.columns([2, 1])
    search = q1.text_input("Search SKU or name")
    include_inactive = q2.checkbox("Show inactive products", value=False)
    view = inventory.copy()
    if not include_inactive:
        view = view[view["is_active"].astype(bool)]
    if search:
        view = view[view["sku"].str.contains(search, case=False, na=False) |
                    view["item_name"].str.contains(search, case=False, na=False)]
    st.dataframe(view[[
        "sku", "item_name", "category_name", "unit", "stock",
        "reorder_level", "stock_status", "next_expiry", "expiry_status", "is_active"
    ]], use_container_width=True, hide_index=True)

    if not inventory.empty:
        st.divider()
        st.subheader("Edit product")
        pmap = {f"{r['sku']} · {r['item_name']}": r for _, r in inventory.iterrows()}
        label = st.selectbox("Select product", list(pmap.keys()))
        product = pmap[label]
        cat_map = {r["category_name"]: int(r["category_id"]) for _, r in categories.iterrows()}
        units = ["piece", "pack", "bottle", "litre", "kg", "gram", "box", "carton"]
        with st.form("product_edit"):
            a, b = st.columns(2)
            new_sku = a.text_input("SKU", value=str(product["sku"]))
            new_name = b.text_input("Name", value=str(product["item_name"]))
            cat_names = list(cat_map.keys())
            cat_idx = cat_names.index(product["category_name"]) if product["category_name"] in cat_names else 0
            new_cat = a.selectbox("Category", cat_names, index=cat_idx)
            old_unit = str(product["unit"])
            unit_idx = units.index(old_unit) if old_unit in units else 0
            new_unit = b.selectbox("Unit", units, index=unit_idx)
            new_reorder = a.number_input("Reorder threshold", min_value=0.0, value=float(product["reorder_level"]))
            new_perishable = b.checkbox("Perishable", value=bool(product["is_perishable"]))
            is_active = st.checkbox("Product is active", value=bool(product["is_active"]))
            save = st.form_submit_button("Save changes")
            if save:
                if not new_sku.strip() or not new_name.strip():
                    st.error("SKU and name cannot be empty.")
                else:
                    try:
                        execute("""
                            UPDATE items SET sku=%s,item_name=%s,category_id=%s,unit=%s,
                            reorder_level=%s,is_perishable=%s,is_active=%s WHERE item_id=%s
                        """, (new_sku.strip(), new_name.strip(), cat_map[new_cat], new_unit,
                              new_reorder, new_perishable, is_active, int(product["item_id"])))
                        st.success("Product updated.")
                        st.rerun()
                    except Exception as exc:
                        error_message(exc)

# ----------------------------- Categories -----------------------------
elif page == "Categories":
    st.subheader("Category management")
    st.dataframe(categories, use_container_width=True, hide_index=True)
    with st.expander("＋ Add category", expanded=False):
        with st.form("category_create"):
            name = st.text_input("Category name")
            description = st.text_area("Description")
            shelf = st.number_input("Default shelf life in days (0 = unspecified)", min_value=0, value=0)
            submit = st.form_submit_button("Save category")
            if submit:
                if not name.strip():
                    st.error("Category name is required.")
                else:
                    try:
                        execute("""
                            INSERT INTO categories (category_name,description,default_shelf_life_days)
                            VALUES (%s,%s,%s)
                        """, (name.strip(), description.strip() or None, shelf or None))
                        st.success("Category created.")
                        st.rerun()
                    except Exception as exc:
                        error_message(exc)

    if not categories.empty:
        st.divider()
        st.subheader("Edit category")
        cmap = {f"{r['category_name']} · ID {r['category_id']}": r for _, r in categories.iterrows()}
        choice = st.selectbox("Choose category", list(cmap.keys()))
        cat = cmap[choice]
        with st.form("category_edit"):
            name = st.text_input("Name", value=cat["category_name"])
            description = st.text_area("Description", value=cat["description"] or "")
            old_days = cat["default_shelf_life_days"]
            days = st.number_input("Default shelf life (days)", min_value=0,
                                   value=int(old_days) if pd.notna(old_days) else 0)
            save = st.form_submit_button("Update category")
            if save:
                try:
                    execute("""
                        UPDATE categories SET category_name=%s,description=%s,
                        default_shelf_life_days=%s WHERE category_id=%s
                    """, (name.strip(), description.strip() or None, days or None, int(cat["category_id"])))
                    st.success("Category updated.")
                    st.rerun()
                except Exception as exc:
                    error_message(exc)

        with st.expander("Delete unused category"):
            st.caption("MySQL foreign keys prevent deletion when products use this category.")
            confirm = st.checkbox("I understand this category will be deleted.", key=f"confirm_cat_{cat['category_id']}")
            if st.button("Delete selected category", key="delete_category"):
                if not confirm:
                    st.warning("Confirm deletion first.")
                else:
                    try:
                        execute("DELETE FROM categories WHERE category_id=%s", (int(cat["category_id"]),))
                        st.success("Category deleted.")
                        st.rerun()
                    except Exception:
                        st.error("Category is still referenced by products or other records. Reassign those products first.")

# ----------------------------- Batches & Stock -----------------------------
elif page == "Batches & Stock":
    st.subheader("Batch and stock operations")
    st.caption("Use unique batch codes. Receipts and adjustments are written to stock_movements.")
    st.dataframe(batches, use_container_width=True, hide_index=True)

    if inventory.empty:
        st.warning("Create a product before receiving stock.")
    else:
        pmap = {f"{r['sku']} · {r['item_name']}": int(r["item_id"]) for _, r in inventory.iterrows()}
        with st.expander("＋ Receive new batch", expanded=True):
            with st.form("batch_receive"):
                item_label = st.selectbox("Product", list(pmap.keys()))
                code = st.text_input("Batch code")
                qty = st.number_input("Quantity received", min_value=0.001, value=1.0, step=1.0)
                received = st.date_input("Received date", value=date.today())
                shelf_days = st.number_input("Shelf life in days (0 = unspecified)", min_value=0, value=7)
                has_expiry = st.checkbox("Batch has expiry date", value=True)
                expiry = st.date_input("Expiry date", value=date.today() + timedelta(days=7)) if has_expiry else None
                submit = st.form_submit_button("Receive stock")
                if submit:
                    if not code.strip():
                        st.error("Batch code is required.")
                    elif expiry and expiry < received:
                        st.error("Expiry date cannot be earlier than received date.")
                    else:
                        def receive(cur):
                            cur.execute("""
                                INSERT INTO inventory_batches
                                (item_id,batch_code,quantity_received,quantity_available,
                                 received_date,shelf_life_days,expiry_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s)
                            """, (pmap[item_label], code.strip(), qty, qty, received, shelf_days or None, expiry))
                            batch_id = cur.lastrowid
                            cur.execute("""
                                INSERT INTO stock_movements (batch_id,movement_type,quantity,reason)
                                VALUES (%s,'RECEIPT',%s,%s)
                            """, (batch_id, qty, "Stock receipt"))
                            return batch_id
                        try:
                            transaction(receive)
                            st.success("Batch received and movement recorded.")
                            st.rerun()
                        except Exception as exc:
                            error_message(exc)

    if not batches.empty:
        st.divider()
        st.subheader("Adjust existing stock")
        bmap = {f"{r['item_name']} · {r['batch_code']} · available {r['quantity_available']} {r['unit']}": r for _, r in batches.iterrows()}
        choice = st.selectbox("Batch to adjust", list(bmap.keys()))
        batch = bmap[choice]
        with st.form("stock_adjust"):
            kind = st.selectbox("Movement type", ["ADJUSTMENT_IN", "ADJUSTMENT_OUT", "WASTAGE", "EXPIRY"])
            amount = st.number_input("Quantity", min_value=0.001, value=1.0, step=1.0)
            reason = st.text_input("Reason")
            submit = st.form_submit_button("Apply adjustment")
            if submit:
                def adjust(cur):
                    cur.execute("SELECT quantity_available FROM inventory_batches WHERE batch_id=%s FOR UPDATE", (int(batch["batch_id"]),))
                    row = cur.fetchone()
                    if not row:
                        raise ValueError("Batch no longer exists.")
                    available = Decimal(str(row[0]))
                    amount_d = Decimal(str(amount))
                   
                    if kind == "ADJUSTMENT_IN":
                        cur.execute("""
                            UPDATE inventory_batches
                            SET quantity_available = quantity_available + %s
                            WHERE batch_id = %s
                        """, (amount, int(batch["batch_id"])))

                    else:
                        if amount_d > available:
                            raise ValueError(
                                f"Only {available} units are available."
                            )

                        cur.execute("""
                            UPDATE inventory_batches
                            SET quantity_available = quantity_available - %s
                            WHERE batch_id = %s
                              AND quantity_available >= %s
                        """, (
                            amount,
                            int(batch["batch_id"]),
                            amount
                        ))

                        if cur.rowcount != 1:
                            raise ValueError(
                                "Stock update failed. Refresh and retry."
                            )

                    cur.execute("""
                        INSERT INTO stock_movements
                            (batch_id, movement_type, quantity, reason)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        int(batch["batch_id"]),
                        kind,
                        amount,
                        reason.strip() or kind.replace("_", " ").title()
                    ))

                try:
                    transaction(adjust)
                    st.success("Stock adjustment recorded.")
                    st.rerun()
                except Exception as exc:
                    error_message(exc)

# ----------------------------- Consumption -----------------------------
elif page == "Consumption":
    st.subheader("Consumption")
    st.caption("Stock, usage history, and stock movement update in one transaction.")
    available = df(fetch_all("""
        SELECT b.batch_id,b.batch_code,b.quantity_available,b.expiry_date,
               i.item_name,i.unit
        FROM inventory_batches b JOIN items i ON i.item_id=b.item_id
        WHERE b.quantity_available>0
        ORDER BY b.expiry_date IS NULL,b.expiry_date
    """))
    if available.empty:
        st.info("No available batches.")
    else:
        bmap = {f"{r['item_name']} · {r['batch_code']} · {r['quantity_available']} {r['unit']}": r for _, r in available.iterrows()}
        with st.form("usage_form"):
            label = st.selectbox("Choose batch", list(bmap.keys()))
            batch = bmap[label]
            qty = st.number_input("Quantity consumed", min_value=0.001,
                                  max_value=float(batch["quantity_available"]),
                                  value=min(1.0, float(batch["quantity_available"])), step=0.5)
            notes = st.text_input("Notes (optional)")
            submit = st.form_submit_button("Record consumption")
            if submit:
                def consume(cur):
                    cur.execute("SELECT quantity_available FROM inventory_batches WHERE batch_id=%s FOR UPDATE", (int(batch["batch_id"]),))
                    row = cur.fetchone()
                    if not row:
                        raise ValueError("Batch no longer exists.")
                    available_qty = Decimal(str(row[0]))
                    amount = Decimal(str(qty))
                    if amount > available_qty:
                        raise ValueError(f"Only {available_qty} units remain.")
                    cur.execute("""
                        UPDATE inventory_batches SET quantity_available=quantity_available-%s
                        WHERE batch_id=%s AND quantity_available >= %s
                    """, (qty, int(batch["batch_id"]), qty))
                    if cur.rowcount != 1:
                        raise ValueError("Stock update failed. Refresh and retry.")
                    cur.execute("""
                        INSERT INTO usage_logs (batch_id,quantity_consumed,notes)
                        VALUES (%s,%s,%s)
                    """, (int(batch["batch_id"]), qty, notes.strip() or None))
                    cur.execute("""
                        INSERT INTO stock_movements (batch_id,movement_type,quantity,reason)
                        VALUES (%s,'CONSUMPTION',%s,%s)
                    """, (int(batch["batch_id"]), qty, notes.strip() or "Stock consumed"))
                try:
                    transaction(consume)
                    st.success("Consumption saved; stock updated.")
                    st.rerun()
                except Exception as exc:
                    error_message(exc)

    st.divider()
    st.subheader("Usage history")
    if usage.empty:
        st.info("No usage records yet.")
    else:
        st.dataframe(usage, use_container_width=True, hide_index=True)
        st.download_button("Download usage CSV", usage.to_csv(index=False).encode("utf-8"),
                           file_name="ecotrace_usage.csv", mime="text/csv")

# ----------------------------- Suppliers -----------------------------
elif page == "Suppliers":
    st.subheader("Supplier directory")
    st.dataframe(suppliers, use_container_width=True, hide_index=True)

    with st.expander("＋ Add supplier"):
        with st.form("supplier_add"):
            name = st.text_input("Supplier name")
            contact = st.text_input("Contact person")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
            submit = st.form_submit_button("Save supplier")
            if submit:
                if not name.strip():
                    st.error("Supplier name is required.")
                else:
                    try:
                        execute("""
                            INSERT INTO suppliers (supplier_name,contact_person,phone,email,address)
                            VALUES (%s,%s,%s,%s,%s)
                        """, (name.strip(), contact.strip() or None, phone.strip() or None,
                              email.strip() or None, address.strip() or None))
                        st.success("Supplier saved.")
                        st.rerun()
                    except Exception as exc:
                        error_message(exc)

    if not suppliers.empty:
        st.divider()
        st.subheader("Edit supplier")
        smap = {f"{r['supplier_name']} · ID {r['supplier_id']}": r for _, r in suppliers.iterrows()}
        choice = st.selectbox("Choose supplier", list(smap.keys()))
        supplier = smap[choice]
        with st.form("supplier_edit"):
            name = st.text_input("Name", value=supplier["supplier_name"])
            contact = st.text_input("Contact person", value=supplier["contact_person"] or "")
            phone = st.text_input("Phone", value=supplier["phone"] or "")
            email = st.text_input("Email", value=supplier["email"] or "")
            address = st.text_area("Address", value=supplier["address"] or "")
            submit = st.form_submit_button("Update supplier")
            if submit:
                try:
                    execute("""
                        UPDATE suppliers SET supplier_name=%s,contact_person=%s,phone=%s,email=%s,address=%s
                        WHERE supplier_id=%s
                    """, (name.strip(), contact.strip() or None, phone.strip() or None,
                          email.strip() or None, address.strip() or None, int(supplier["supplier_id"])))
                    st.success("Supplier updated.")
                    st.rerun()
                except Exception as exc:
                    error_message(exc)

# ----------------------------- Purchases -----------------------------
elif page == "Purchases":
    st.subheader("Purchase orders")
    purchases = df(fetch_all("""
        SELECT p.purchase_id,p.reference_number,s.supplier_name,p.purchase_date,
               p.status,p.notes
        FROM purchases p JOIN suppliers s ON s.supplier_id=p.supplier_id
        ORDER BY p.purchase_date DESC,p.purchase_id DESC
    """))
    if purchases.empty:
        st.info("No purchase orders yet.")
    else:
        st.dataframe(purchases, use_container_width=True, hide_index=True)

    lines = df(fetch_all("""
        SELECT pi.purchase_item_id, p.reference_number, i.sku, i.item_name,
               pi.quantity_ordered, pi.quantity_received, pi.unit_cost,
               (pi.quantity_ordered-pi.quantity_received) AS outstanding
        FROM purchase_items pi
        JOIN purchases p ON p.purchase_id=pi.purchase_id
        JOIN items i ON i.item_id=pi.item_id
        ORDER BY pi.purchase_item_id DESC
    """))
    st.subheader("Purchase line items")
    if not lines.empty:
        st.dataframe(lines, use_container_width=True, hide_index=True)

    if suppliers.empty or inventory.empty:
        st.warning("Create at least one supplier and one product first.")
    else:
        with st.expander("＋ Create purchase order"):
            smap = {r["supplier_name"]: int(r["supplier_id"]) for _, r in suppliers.iterrows()}
            imap = {f"{r['sku']} · {r['item_name']}": int(r["item_id"]) for _, r in inventory.iterrows()}
            with st.form("po_create"):
                supplier_name = st.selectbox("Supplier", list(smap.keys()))
                ref = st.text_input("Unique reference number")
                purchase_date = st.date_input("Purchase date", value=date.today())
                status = st.selectbox("Status", ["DRAFT", "ORDERED", "CANCELLED"])
                notes = st.text_area("Notes")
                item_label = st.selectbox("Product", list(imap.keys()))
                ordered = st.number_input("Quantity ordered", min_value=0.001, value=10.0, step=1.0)
                cost = st.number_input("Unit cost", min_value=0.0, value=0.0, step=1.0)
                submit = st.form_submit_button("Create order")
                if submit:
                    if not ref.strip():
                        st.error("Reference number is required.")
                    else:
                        def create_po(cur):
                            cur.execute("""
                                INSERT INTO purchases (supplier_id,reference_number,purchase_date,status,notes)
                                VALUES (%s,%s,%s,%s,%s)
                            """, (smap[supplier_name], ref.strip(), purchase_date, status, notes.strip() or None))
                            po_id = cur.lastrowid
                            cur.execute("""
                                INSERT INTO purchase_items
                                (purchase_id,item_id,quantity_ordered,quantity_received,unit_cost)
                                VALUES (%s,%s,%s,0,%s)
                            """, (po_id, imap[item_label], ordered, cost))
                            return po_id
                        try:
                            po_id = transaction(create_po)
                            st.success(f"Purchase order created (ID {po_id}).")
                            st.rerun()
                        except Exception as exc:
                            error_message(exc)

    if not lines.empty:
        st.divider()
        st.subheader("Record purchase quantity received")
        lmap = {f"{r['reference_number']} · {r['item_name']} · outstanding {r['outstanding']}": r for _, r in lines.iterrows()}
        choice = st.selectbox("Purchase line", list(lmap.keys()))
        line = lmap[choice]
        if float(line["outstanding"]) > 0:
            with st.form("receive_purchase_line"):
                received_qty = st.number_input("Quantity received now", min_value=0.001,
                                                max_value=float(line["outstanding"]),
                                                value=min(1.0, float(line["outstanding"])), step=1.0)
                batch_code = st.text_input("New batch code for this receipt")
                received_date = st.date_input("Receipt date", value=date.today())
                expiry_enabled = st.checkbox("Set expiry date", value=True)
                expiry_date = st.date_input("Expiry date", value=date.today()+timedelta(days=7)) if expiry_enabled else None
                shelf_days = st.number_input("Shelf life (days; 0 = unspecified)", min_value=0, value=7)
                submit = st.form_submit_button("Receive purchase quantity")
                if submit:
                    if not batch_code.strip():
                        st.error("Batch code is required.")
                    elif expiry_date and expiry_date < received_date:
                        st.error("Expiry date cannot be before receipt date.")
                    else:
                        def receive_purchase(cur):
                            cur.execute("""
                                SELECT quantity_ordered,quantity_received,purchase_id,item_id
                                FROM purchase_items WHERE purchase_item_id=%s FOR UPDATE
                            """, (int(line["purchase_item_id"]),))
                            pr = cur.fetchone()
                            if not pr:
                                raise ValueError("Purchase line not found.")
                            remaining = Decimal(str(pr[0])) - Decimal(str(pr[1]))
                            amount = Decimal(str(received_qty))
                            if amount > remaining:
                                raise ValueError(f"Only {remaining} units remain outstanding.")
                            cur.execute("""
                                INSERT INTO inventory_batches
                                (item_id,batch_code,quantity_received,quantity_available,received_date,shelf_life_days,expiry_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s)
                            """, (int(pr[3]), batch_code.strip(), received_qty, received_qty,
                                  received_date, shelf_days or None, expiry_date))
                            batch_id = cur.lastrowid
                            cur.execute("""
                                INSERT INTO stock_movements (batch_id,movement_type,quantity,reason)
                                VALUES (%s,'RECEIPT',%s,%s)
                            """, (batch_id, received_qty, f"Receipt for purchase {line['reference_number']}"))
                            cur.execute("""
                                UPDATE purchase_items SET quantity_received=quantity_received+%s
                                WHERE purchase_item_id=%s
                            """, (received_qty, int(line["purchase_item_id"])))
                            cur.execute("""
                                SELECT SUM(quantity_ordered),SUM(quantity_received)
                                FROM purchase_items WHERE purchase_id=%s
                            """, (int(pr[2]),))
                            totals = cur.fetchone()
                            new_status = "RECEIVED" if totals[1] >= totals[0] else "PARTIALLY_RECEIVED" if totals[1] > 0 else "ORDERED"
                            cur.execute("UPDATE purchases SET status=%s WHERE purchase_id=%s", (new_status, int(pr[2])))
                        try:
                            transaction(receive_purchase)
                            st.success("Purchase receipt saved and stock added.")
                            st.rerun()
                        except Exception as exc:
                            error_message(exc)
        else:
            st.success("This purchase line is fully received.")

# ----------------------------- Reports -----------------------------
elif page == "Reports":
    st.subheader("Analytics & reports")
    st.caption("Depletion is a rough estimate based on recorded consumption in the last 7 days.")

    if inventory.empty:
        st.info("Add inventory to create reports.")
    else:
        fig = px.bar(inventory, x="item_name", y="stock", color="stock_status",
                     color_discrete_map={"Healthy": "#39D98A", "Low stock": "#FFC857", "Out of stock": "#FF6B6B"})
        st.plotly_chart(chart_layout(fig), use_container_width=True)

        recent_usage = df(fetch_all("""
            SELECT i.item_id, SUM(u.quantity_consumed)/7 AS average_daily
            FROM usage_logs u
            JOIN inventory_batches b ON b.batch_id=u.batch_id
            JOIN items i ON i.item_id=b.item_id
            WHERE u.consumed_at >= NOW()-INTERVAL 7 DAY
            GROUP BY i.item_id
        """))
        rates = {int(r["item_id"]): float(r["average_daily"]) for _, r in recent_usage.iterrows()} if not recent_usage.empty else {}
        report = inventory[["sku", "item_name", "category_name", "stock", "unit", "stock_status", "next_expiry"]].copy()
        report["average_daily_consumption"] = inventory["item_id"].map(rates).fillna(0)
        report["estimated_days_remaining"] = report.apply(
            lambda r: round(r["stock"]/r["average_daily_consumption"], 1)
            if r["average_daily_consumption"] > 0 else None, axis=1
        )
        st.dataframe(report, use_container_width=True, hide_index=True)
        st.download_button("⬇ Download inventory report CSV",
                           report.to_csv(index=False).encode("utf-8"),
                           file_name="ecotrace_inventory_report.csv",
                           mime="text/csv")

    st.subheader("Stock movement ledger")
    movements = df(fetch_all("""
        SELECT m.movement_at,i.sku,i.item_name,b.batch_code,
               m.movement_type,m.quantity,m.reason
        FROM stock_movements m
        JOIN inventory_batches b ON b.batch_id=m.batch_id
        JOIN items i ON i.item_id=b.item_id
        ORDER BY m.movement_at DESC LIMIT 1000
    """))
    if movements.empty:
        st.info("No stock movements recorded.")
    else:
        st.dataframe(movements, use_container_width=True, hide_index=True)
        st.download_button("⬇ Download movement ledger CSV",
                           movements.to_csv(index=False).encode("utf-8"),
                           file_name="ecotrace_stock_movements.csv",
                           mime="text/csv")

st.divider()
st.caption("EcoTrace · Local inventory workspace · Verify data before operational use")
