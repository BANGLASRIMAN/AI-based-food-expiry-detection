from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from database import add_product, delete_product, get_products, init_db, product_status
from app.services.expiry import expiry_status
from app.services.freshness import visual_freshness_estimate
from app.services.ocr import detect_expiry_date

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "app" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="FoodGuard AI",
    page_icon="🥫",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
    .main-title {font-size: 2.4rem; font-weight: 800; margin-bottom: 0.1rem;}
    .subtitle {color: #667085; font-size: 1.05rem; margin-bottom: 1.5rem;}
    .card {padding: 1rem 1.2rem; border: 1px solid #e5e7eb; border-radius: 14px; background: #ffffff;}
    .status-fresh {color: #15803d; font-weight: 700;}
    .status-near {color: #b45309; font-weight: 700;}
    .status-expired {color: #b91c1c; font-weight: 700;}
</style>
""", unsafe_allow_html=True)


def status_emoji(status):
    return {"Fresh": "🟢", "Near Expiry": "🟠", "Expired": "🔴"}.get(status, "⚪")


def products_dataframe():
    rows = get_products()
    data = []
    for row in rows:
        status, days = product_status(row["expiry_date"])
        data.append({
            "ID": row["id"],
            "Product": row["name"],
            "Category": row["category"],
            "Expiry Date": row["expiry_date"],
            "Days Remaining": days,
            "Quantity": row["quantity"],
            "Storage": row["storage"],
            "Status": f"{status_emoji(status)} {status}",
        })
    return pd.DataFrame(data)


def dashboard():
    st.markdown('<div class="main-title">🥫 FoodGuard AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Based Food Expiry Detection and Smart Reminder System</div>', unsafe_allow_html=True)

    rows = get_products()
    counts = {"Fresh": 0, "Near Expiry": 0, "Expired": 0}
    total_qty = 0
    for row in rows:
        status, _ = product_status(row["expiry_date"])
        counts[status] += 1
        total_qty += row["quantity"] or 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Products", len(rows))
    c2.metric("🟢 Fresh", counts["Fresh"])
    c3.metric("🟠 Near Expiry", counts["Near Expiry"])
    c4.metric("🔴 Expired", counts["Expired"])

    st.divider()
    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Inventory Overview")
        df = products_dataframe()
        if df.empty:
            st.info("No products added yet. Use Add Product or Scan Expiry to begin.")
        else:
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

    with right:
        st.subheader("Smart Reminders")
        reminders = []
        for row in rows:
            status, days = product_status(row["expiry_date"])
            if status == "Expired":
                reminders.append(f"🔴 **{row['name']}** expired {abs(days)} day(s) ago.")
            elif status == "Near Expiry":
                reminders.append(f"🟠 **{row['name']}** expires in {days} day(s).")
        if reminders:
            for reminder in reminders:
                st.warning(reminder)
        else:
            st.success("No urgent expiry reminders.")


def add_product_page():
    st.title("➕ Add Product")
    st.write("Enter food information manually and FoodGuard will classify its expiry status.")
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product name *", placeholder="Milk")
            category = st.selectbox("Category", ["Dairy", "Beverage", "Packaged Food", "Frozen", "Fruit", "Vegetable", "Other"])
            manufacturing_date = st.date_input("Manufacturing date", value=None)
            expiry_date = st.date_input("Expiry date *", min_value=date(2000, 1, 1))
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            storage = st.text_input("Storage", placeholder="Refrigerator")
            image = st.file_uploader("Optional product image", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Save Product", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Please enter a product name.")
            return
        if expiry_date < date.today():
            status, days = expiry_status(expiry_date)
            st.warning(f"This product is already {status.lower()} ({abs(days)} day(s) ago). You can still save it.")

        image_filename = None
        if image:
            image_filename = f"{date.today().isoformat()}_{image.name}"
            (UPLOAD_DIR / image_filename).write_bytes(image.getbuffer())

        mfg = manufacturing_date.isoformat() if manufacturing_date else None
        add_product(name.strip(), category, mfg, expiry_date.isoformat(), int(quantity), storage.strip(), image_filename)
        st.success("Product added successfully!")


def scan_page():
    st.title("📷 Scan Expiry Date")
    st.write("Upload a food-package image. EasyOCR will try to detect the printed expiry date.")
    image = st.file_uploader("Upload food package image", type=["jpg", "jpeg", "png"])

    if not image:
        st.info("Choose a clear image containing an EXP, EXPIRY, USE BY, or BEST BEFORE date.")
        return

    st.image(image, caption="Uploaded package", use_container_width=True)
    if st.button("🔍 Detect Expiry Date", type="primary"):
        temp_path = UPLOAD_DIR / f"scan_{image.name}"
        temp_path.write_bytes(image.getbuffer())
        with st.spinner("Running OCR… the first run may take longer while EasyOCR initializes."):
            detected_date, ocr_text = detect_expiry_date(str(temp_path))

        if detected_date:
            status, days = expiry_status(detected_date)
            st.success(f"Detected expiry date: **{detected_date.strftime('%d %B %Y')}**")
            st.metric("Status", f"{status_emoji(status)} {status}", f"{days} days remaining")

            st.divider()
            st.subheader("Save to Inventory")
            with st.form("save_scan"):
                name = st.text_input("Product name *", placeholder="Detected food item")
                category = st.selectbox("Category", ["Dairy", "Beverage", "Packaged Food", "Frozen", "Fruit", "Vegetable", "Other"])
                quantity = st.number_input("Quantity", min_value=1, value=1)
                storage = st.text_input("Storage", placeholder="Kitchen shelf")
                save = st.form_submit_button("Save Detected Product", type="primary")
                if save:
                    if not name.strip():
                        st.error("Please enter a product name.")
                    else:
                        filename = f"{date.today().isoformat()}_{image.name}"
                        (UPLOAD_DIR / filename).write_bytes(image.getbuffer())
                        add_product(name.strip(), category, None, detected_date.isoformat(), int(quantity), storage.strip(), filename)
                        st.success("Detected product saved to inventory!")
        else:
            st.error("No expiry date could be detected. Try a clearer/cropped image or add the product manually.")

        with st.expander("View OCR text"):
            st.code(ocr_text or "No OCR text returned.")


def freshness_page():
    st.title("🤖 AI Visual Freshness")
    st.write("This page is the integration point for a trained food-freshness model.")
    image = st.file_uploader("Upload food image", type=["jpg", "jpeg", "png"], key="freshness_upload")
    if image:
        st.image(image, caption="Food image", use_container_width=True)
        if st.button("🤖 Analyze Freshness", type="primary"):
            path = UPLOAD_DIR / f"freshness_{image.name}"
            path.write_bytes(image.getbuffer())
            result = visual_freshness_estimate(str(path))
            st.info(f"Result: {result['label']}")
            st.metric("Confidence", f"{result['confidence'] * 100:.1f}%")
            st.caption(result["message"])
            st.warning("Visual AI is only an estimate and should not replace manufacturer expiry labels or food-safety guidance.")


def inventory_page():
    st.title("📦 Food Inventory")
    df = products_dataframe()
    if df.empty:
        st.info("Your inventory is empty.")
        return

    st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)
    st.subheader("Delete Product")
    product_options = {f"{row['id']} — {row['name']} ({row['expiry_date']})": row['id'] for row in get_products()}
    selected = st.selectbox("Select product", list(product_options.keys()))
    if st.button("🗑️ Delete Selected Product"):
        delete_product(product_options[selected])
        st.success("Product deleted.")
        st.rerun()


def analytics_page():
    st.title("📊 Analytics")
    df = products_dataframe()
    if df.empty:
        st.info("Add products to view analytics.")
        return
    status_counts = df["Status"].str.replace(r"^[^ ]+ ", "", regex=True).value_counts()
    st.bar_chart(status_counts)
    st.subheader("Products by Category")
    st.bar_chart(df.groupby("Category")["Quantity"].sum())


with st.sidebar:
    st.title("🥫 FoodGuard AI")
    page = st.radio("Navigation", [
        "Dashboard",
        "Add Product",
        "Scan Expiry",
        "AI Freshness",
        "Inventory",
        "Analytics",
    ])
    st.divider()
    st.caption("Python + Streamlit + SQLite + EasyOCR")

if page == "Dashboard":
    dashboard()
elif page == "Add Product":
    add_product_page()
elif page == "Scan Expiry":
    scan_page()
elif page == "AI Freshness":
    freshness_page()
elif page == "Inventory":
    inventory_page()
elif page == "Analytics":
    analytics_page()
