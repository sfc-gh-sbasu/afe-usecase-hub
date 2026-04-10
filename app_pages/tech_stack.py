import streamlit as st
import pandas as pd

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/layers: Tech Stack Analysis")
st.caption("Customer technology landscape and product focus areas")

@st.cache_data(ttl=300)
def load_tech_data(_filter):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_INDUSTRY,
            TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
            COMPETITORS, INCUMBENT_VENDOR, IMPLEMENTER, PARTNER_NAME,
            USE_CASE_STAGE, REGION_NAME
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)

df = load_tech_data(filter_sql)

def derive_products(row):
    parts = []
    tech = str(row.get("TECHNICAL_USE_CASE") or "").lower()
    workloads = str(row.get("WORKLOADS") or "").lower()
    if "openflow" in tech or "openflow" in workloads:
        parts.append("Openflow")
    if "iceberg" in tech or "interoperable storage" in tech or "lakehouse" in tech:
        parts.append("Iceberg/Lakehouse")
    if "ingestion" in tech:
        parts.append("Data Ingestion")
    if "transformation" in tech:
        parts.append("Data Transformation")
    if "machine learning" in tech or "cortex" in tech:
        parts.append("Cortex AI/ML")
    if "conversational" in tech:
        parts.append("Cortex Agent")
    if "analytics" in workloads or "business intelligence" in tech:
        parts.append("Analytics")
    if "apps" in tech or "native app" in tech:
        parts.append("Native Apps")
    return ", ".join(parts) if parts else workloads.title() or "TBD"

df["PRODUCT_FOCUS"] = df.apply(derive_products, axis=1)

def derive_deploy(row):
    cloud = row.get("CLOUD_PROVIDER") or ""
    if not cloud or cloud == "None":
        return "Unknown"
    if ";" in cloud:
        return "Multi-Cloud"
    return cloud

df["DEPLOYMENT_MODEL"] = df.apply(derive_deploy, axis=1)

def build_tech_summary(row):
    parts = []
    if row["INCUMBENT_VENDOR"]:
        parts.append(f"Incumbent: {row['INCUMBENT_VENDOR']}")
    if row["COMPETITORS"]:
        parts.append(f"Competing: {row['COMPETITORS']}")
    if row["IMPLEMENTER"]:
        parts.append(f"Implementer: {row['IMPLEMENTER']}")
    if row["PARTNER_NAME"]:
        parts.append(f"Partner: {row['PARTNER_NAME']}")
    return "; ".join(parts) if parts else None

df["TECH_STACK_SUMMARY"] = df.apply(build_tech_summary, axis=1)

ovc1, ovc2 = st.columns(2)
with ovc1:
    st.subheader("Deployment models")
    deployment_counts = df["DEPLOYMENT_MODEL"].value_counts()
    st.bar_chart(deployment_counts, horizontal=True, color="#29B5E8")
with ovc2:
    st.subheader("Products in play")
    product_list = []
    for p in df["PRODUCT_FOCUS"].dropna():
        for item in p.split(","):
            clean = item.strip()
            if clean and clean != "TBD":
                product_list.append(clean)
    if product_list:
        prod_series = pd.Series(product_list).value_counts().head(10)
        st.bar_chart(prod_series, horizontal=True, color="#FF6F61")

st.divider()
st.subheader("Per-customer tech stack detail")

tsc1, tsc2, tsc3 = st.columns([3, 2, 1])
ts_search = tsc1.text_input(":material/search: Search", placeholder="Customer, product, tech stack...", key="ts_search")
ts_sort = tsc2.selectbox("Sort by", ["Customer", "Deployment Model", "Product Focus", "Industry"], key="ts_sort")
ts_dir = tsc3.selectbox("Order", ["Asc", "Desc"], key="ts_dir")

ts_filtered = df.copy()
if ts_search:
    ts_filtered = ts_filtered[ts_filtered.apply(
        lambda r: ts_search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1
    )]
ts_sort_map = {
    "Customer": "ACCOUNT_NAME", "Deployment Model": "DEPLOYMENT_MODEL",
    "Product Focus": "PRODUCT_FOCUS", "Industry": "ACCOUNT_INDUSTRY"
}
ts_filtered = ts_filtered.sort_values(ts_sort_map[ts_sort], ascending=(ts_dir == "Asc"), na_position="last")

for _, row in ts_filtered.iterrows():
    with st.expander(
        f":material/business: **{row['ACCOUNT_NAME']}** — {row['DEPLOYMENT_MODEL']} | {row['PRODUCT_FOCUS']}"
    ):
        if row["ACCOUNT_INDUSTRY"]:
            st.caption(f":material/domain: {row['ACCOUNT_INDUSTRY']} | :material/map: {row['REGION_NAME'] or 'N/A'}")
        st.write(f"**Products (SFDC):** {row['PRODUCT_FOCUS']}")
        st.write(f"**Tech stack:** {row['TECH_STACK_SUMMARY'] or 'Unknown — needs discovery'}")
        st.caption(f":material/layers: Stage: {row['USE_CASE_STAGE'] or 'N/A'}")
