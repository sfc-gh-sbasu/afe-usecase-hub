import streamlit as st
import pandas as pd

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/layers: Tech Stack Analysis")
st.caption("Customer technology landscape, product usage telemetry, and competitive positioning")


def safe_int(v, default=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def safe_float(v, default=0.0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


@st.cache_data(ttl=300)
def load_tech_data(_filter):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_ID, ACCOUNT_INDUSTRY,
            USE_CASE_NAME, USE_CASE_DESCRIPTION,
            TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
            COMPETITORS, INCUMBENT_VENDOR, IMPLEMENTER, PARTNER_NAME,
            USE_CASE_STAGE, USE_CASE_STATUS, REGION_NAME,
            DAYS_IN_STAGE, IS_WON, IS_LOST, IN_POC,
            OWNER_NAME, USE_CASE_LEAD_SE_NAME,
            MEDDPICC_IDENTIFY_PAIN
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)


@st.cache_data(ttl=600)
def load_product_usage_for_tech(sfdc_account_ids_csv):
    if not sfdc_account_ids_csv:
        return pd.DataFrame()

    openflow_df = run_query(f"""
        SELECT SALESFORCE_ACCOUNT_ID, 'Openflow' as PRODUCT,
               COUNT(DISTINCT CONNECTOR_NAME) as METRIC_COUNT,
               SUM(BYTES_SENT)/1e9 as TOTAL_GB,
               LISTAGG(DISTINCT CONNECTOR_NAME, ', ') WITHIN GROUP (ORDER BY CONNECTOR_NAME) as DETAIL,
               MAX(DS) as LAST_SEEN
        FROM SNOWSCIENCE.OPENFLOW.OPENFLOW_CONNECTORS
        WHERE SALESFORCE_ACCOUNT_ID IN ({sfdc_account_ids_csv})
        GROUP BY 1
    """)

    account_map_df = run_query(f"""
        SELECT DISTINCT SNOWFLAKE_DEPLOYMENT, CAST(SNOWFLAKE_ACCOUNT_ID AS INTEGER) as SNOWFLAKE_ACCOUNT_ID,
               SALESFORCE_ACCOUNT_ID
        FROM SNOWSCIENCE.DIMENSIONS.DIM_ACCOUNTS_HISTORY
        WHERE SALESFORCE_ACCOUNT_ID IN ({sfdc_account_ids_csv})
          AND GENERAL_DATE = (SELECT MAX(GENERAL_DATE) FROM SNOWSCIENCE.DIMENSIONS.DIM_ACCOUNTS_HISTORY)
          AND ACCOUNT_STATUS = 'Active' AND SNOWFLAKE_ACCOUNT_TYPE = 'Customer'
    """)

    iceberg_df = pd.DataFrame()
    ssv2_df = pd.DataFrame()

    if not account_map_df.empty:
        account_map_df = account_map_df.dropna(subset=["SNOWFLAKE_DEPLOYMENT", "SNOWFLAKE_ACCOUNT_ID"])
        account_map_df = account_map_df[account_map_df["SNOWFLAKE_DEPLOYMENT"].astype(str).str.strip() != ""]

    if not account_map_df.empty:
        conditions = " OR ".join([
            f"(DEPLOYMENT = '{r['SNOWFLAKE_DEPLOYMENT']}' AND ACCOUNT_ID = {safe_int(r['SNOWFLAKE_ACCOUNT_ID'])})"
            for _, r in account_map_df.iterrows()
        ])

        iceberg_df = run_query(f"""
            WITH latest_day AS (
                SELECT DEPLOYMENT, ACCOUNT_ID, MAX(DS) as MAX_DS
                FROM SNOWSCIENCE.PRODUCT.ICEBERG_DAILY_ACCOUNT_AGG
                WHERE DS >= DATEADD(day, -90, CURRENT_DATE()) AND ({conditions})
                GROUP BY 1, 2
            )
            SELECT a.DEPLOYMENT, a.ACCOUNT_ID, 'Iceberg' as PRODUCT,
                   SUM(a.QUALIFIED_TABLE_COUNT) as METRIC_COUNT,
                   SUM(a.ACTIVE_BYTES)/1e9 as TOTAL_GB,
                   MAX(a.DS) as LAST_SEEN
            FROM SNOWSCIENCE.PRODUCT.ICEBERG_DAILY_ACCOUNT_AGG a
            JOIN latest_day ld ON a.DEPLOYMENT = ld.DEPLOYMENT AND a.ACCOUNT_ID = ld.ACCOUNT_ID AND a.DS = ld.MAX_DS
            GROUP BY 1, 2
        """)

        if not iceberg_df.empty:
            sfdc_map = {(r['SNOWFLAKE_DEPLOYMENT'], r['SNOWFLAKE_ACCOUNT_ID']): r['SALESFORCE_ACCOUNT_ID']
                        for _, r in account_map_df.iterrows()}
            iceberg_df["SALESFORCE_ACCOUNT_ID"] = iceberg_df.apply(
                lambda r: sfdc_map.get((r["DEPLOYMENT"], r["ACCOUNT_ID"])), axis=1)

        ssv2_df = run_query(f"""
            SELECT DEPLOYMENT, ACCOUNT_ID, 'SSV2' as PRODUCT,
                   COUNT(DISTINCT CHANNEL_NAME) as METRIC_COUNT,
                   SUM(APPEND_BYTES_COUNT)/1e9 as TOTAL_GB,
                   MAX(DS) as LAST_SEEN
            FROM SNOWSCIENCE.SNOWPIPE.SSV2_CHANNEL_METRICS
            WHERE DS >= DATEADD(day, -90, CURRENT_DATE()) AND ({conditions})
            GROUP BY 1, 2
        """)

        if not ssv2_df.empty:
            sfdc_map = {(r['SNOWFLAKE_DEPLOYMENT'], r['SNOWFLAKE_ACCOUNT_ID']): r['SALESFORCE_ACCOUNT_ID']
                        for _, r in account_map_df.iterrows()}
            ssv2_df["SALESFORCE_ACCOUNT_ID"] = ssv2_df.apply(
                lambda r: sfdc_map.get((r["DEPLOYMENT"], r["ACCOUNT_ID"])), axis=1)

    rows = []
    if not openflow_df.empty:
        for _, r in openflow_df.iterrows():
            rows.append({"SALESFORCE_ACCOUNT_ID": r["SALESFORCE_ACCOUNT_ID"], "PRODUCT": "Openflow",
                         "METRIC_COUNT": safe_int(r["METRIC_COUNT"]), "METRIC_LABEL": "Connectors",
                         "TOTAL_GB": safe_float(r["TOTAL_GB"]), "DETAIL": str(r["DETAIL"] or ""),
                         "LAST_SEEN": r["LAST_SEEN"]})
    if not iceberg_df.empty:
        for _, r in iceberg_df.iterrows():
            rows.append({"SALESFORCE_ACCOUNT_ID": r.get("SALESFORCE_ACCOUNT_ID"), "PRODUCT": "Iceberg",
                         "METRIC_COUNT": safe_int(r["METRIC_COUNT"]), "METRIC_LABEL": "Active Tables",
                         "TOTAL_GB": safe_float(r["TOTAL_GB"]), "DETAIL": f"{safe_int(r['METRIC_COUNT']):,} active tables",
                         "LAST_SEEN": r["LAST_SEEN"]})
    if not ssv2_df.empty:
        for _, r in ssv2_df.iterrows():
            rows.append({"SALESFORCE_ACCOUNT_ID": r.get("SALESFORCE_ACCOUNT_ID"), "PRODUCT": "SSV2",
                         "METRIC_COUNT": safe_int(r["METRIC_COUNT"]), "METRIC_LABEL": "Channels",
                         "TOTAL_GB": safe_float(r["TOTAL_GB"]), "DETAIL": f"{safe_int(r['METRIC_COUNT'])} streaming channels",
                         "LAST_SEEN": r["LAST_SEEN"]})
    return pd.DataFrame(rows) if rows else pd.DataFrame()


df = load_tech_data(filter_sql)

sfdc_ids = df["ACCOUNT_ID"].dropna().unique().tolist()
sfdc_ids_csv = ",".join([f"'{aid}'" for aid in sfdc_ids]) if sfdc_ids else ""
usage_df = load_product_usage_for_tech(sfdc_ids_csv)


def derive_products(row):
    parts = []
    tech = str(row.get("TECHNICAL_USE_CASE") or "").lower()
    workloads = str(row.get("WORKLOADS") or "").lower()
    if "openflow" in tech or "openflow" in workloads:
        parts.append("Openflow")
    if "iceberg" in tech or "interoperable storage" in tech or "lakehouse" in tech:
        parts.append("Iceberg/Open Data Lake")
    if any(kw in tech for kw in ["streaming", "kafka", "kinesis", "snowpipe", "ssv2"]):
        parts.append("SSV2 (Snowpipe Streaming)")
    if "dynamic table" in tech or "dynamic table" in workloads:
        parts.append("Dynamic Tables")
    if "snowpark" in tech or "pyspark" in tech or "spark" in tech:
        parts.append("Snowpark")
    if "ingestion" in tech and "openflow" not in tech:
        parts.append("Data Ingestion")
    if "machine learning" in tech or "cortex" in tech:
        parts.append("Cortex AI/ML")
    if "conversational" in tech or "agent" in tech:
        parts.append("Cortex Agent")
    if "analytics" in workloads or "business intelligence" in tech:
        parts.append("Analytics")
    if "native app" in tech:
        parts.append("Native Apps")
    return ", ".join(parts) if parts else workloads.title() or "TBD"


df["PRODUCT_FOCUS"] = df.apply(derive_products, axis=1)


def derive_deploy(row):
    cloud = row.get("CLOUD_PROVIDER") or ""
    if not cloud or cloud == "None":
        return "Unknown"
    return "Multi-Cloud" if ";" in cloud else cloud


df["DEPLOYMENT_MODEL"] = df.apply(derive_deploy, axis=1)


FIVE_SERVICES = ["Openflow", "Iceberg/Open Data Lake", "SSV2 (Snowpipe Streaming)", "Dynamic Tables", "Snowpark"]

product_list = []
for p in df["PRODUCT_FOCUS"].dropna():
    for item in p.split(","):
        clean = item.strip()
        if clean and clean != "TBD":
            product_list.append(clean)

svc_counts = {s: 0 for s in FIVE_SERVICES}
for p in product_list:
    for s in FIVE_SERVICES:
        if s.lower().split("(")[0].strip() in p.lower() or p.lower() in s.lower():
            svc_counts[s] += 1

col1, col2, col3, col4, col5 = st.columns(5)
for col, svc in zip([col1, col2, col3, col4, col5], FIVE_SERVICES):
    label = svc.split("(")[0].strip() if "(" in svc else svc.split("/")[0].strip()
    count = svc_counts[svc]
    accts_with_telemetry = 0
    if not usage_df.empty:
        product_key = svc.split("(")[0].strip().split("/")[0].strip()
        accts_with_telemetry = usage_df[usage_df["PRODUCT"].str.contains(product_key, case=False, na=False)]["SALESFORCE_ACCOUNT_ID"].nunique()
    col.metric(label, count, delta=f"{accts_with_telemetry} telemetry", delta_color="normal")

st.divider()

ovc1, ovc2 = st.columns(2)
with ovc1:
    st.subheader("Deployment models")
    deployment_counts = df["DEPLOYMENT_MODEL"].value_counts()
    st.bar_chart(deployment_counts, horizontal=True, color="#29B5E8")
with ovc2:
    st.subheader("Products in play")
    if product_list:
        prod_series = pd.Series(product_list).value_counts().head(10)
        st.bar_chart(prod_series, horizontal=True, color="#FF6F61")

st.divider()
st.subheader("Per-customer tech stack detail")

tsc1, tsc2, tsc3, tsc4 = st.columns([3, 2, 2, 1])
ts_search = tsc1.text_input(":material/search: Search", placeholder="Customer, product, tech stack...", key="ts_search")
ts_product = tsc2.selectbox("Service filter", ["All"] + FIVE_SERVICES, key="ts_svc_filter")
ts_sort = tsc3.selectbox("Sort by", ["Customer", "Deployment Model", "Product Focus", "Industry", "Stage"], key="ts_sort")
ts_dir = tsc4.selectbox("Order", ["Asc", "Desc"], key="ts_dir")

ts_filtered = df.copy()
if ts_search:
    ts_filtered = ts_filtered[ts_filtered.apply(
        lambda r: ts_search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1
    )]
if ts_product and ts_product != "All":
    svc_key = ts_product.split("(")[0].strip().lower()
    ts_filtered = ts_filtered[ts_filtered["PRODUCT_FOCUS"].str.lower().str.contains(svc_key, na=False)]

ts_sort_map = {
    "Customer": "ACCOUNT_NAME", "Deployment Model": "DEPLOYMENT_MODEL",
    "Product Focus": "PRODUCT_FOCUS", "Industry": "ACCOUNT_INDUSTRY",
    "Stage": "USE_CASE_STAGE"
}
ts_filtered = ts_filtered.sort_values(ts_sort_map[ts_sort], ascending=(ts_dir == "Asc"), na_position="last")

for _, row in ts_filtered.iterrows():
    stage_short = (row["USE_CASE_STAGE"] or "N/A").split(" - ")[-1]
    won_icon = ":material/celebration:" if row.get("IS_WON") else ":material/business:"
    with st.expander(
        f"{won_icon} **{row['ACCOUNT_NAME']}** — {row['DEPLOYMENT_MODEL']} | {stage_short} | {row['PRODUCT_FOCUS']}"
    ):
        sfdc_url = f"https://snowforce.lightning.force.com/lightning/r/Use_Case__c/{row['USE_CASE_ID']}/view"

        hdr1, hdr2, hdr3 = st.columns([2, 2, 1])
        with hdr1:
            st.caption(f":material/domain: **Industry:** {row['ACCOUNT_INDUSTRY'] or 'N/A'} | **Region:** {row['REGION_NAME'] or 'N/A'}")
            if row["OWNER_NAME"] or row["USE_CASE_LEAD_SE_NAME"]:
                st.caption(f":material/person: **AE:** {row['OWNER_NAME'] or 'N/A'} | **Lead SE:** {row['USE_CASE_LEAD_SE_NAME'] or 'N/A'}")
        with hdr2:
            st.caption(f":material/layers: **Stage:** {row['USE_CASE_STAGE'] or 'N/A'}")
            if row["DAYS_IN_STAGE"] and pd.notna(row["DAYS_IN_STAGE"]):
                st.caption(f":material/timer: {safe_int(row['DAYS_IN_STAGE'])} days in current stage")
        with hdr3:
            st.link_button("Open in SFDC", sfdc_url, icon=":material/open_in_new:")

        if row["USE_CASE_DESCRIPTION"]:
            desc = str(row["USE_CASE_DESCRIPTION"])[:500]
            st.markdown(f"> {desc}{'...' if len(str(row['USE_CASE_DESCRIPTION'])) > 500 else ''}")

        comp_parts = []
        if row["INCUMBENT_VENDOR"]:
            comp_parts.append(f":material/swap_horiz: **Incumbent:** {row['INCUMBENT_VENDOR']}")
        if row["COMPETITORS"]:
            comp_parts.append(f":material/swords: **Competing:** {row['COMPETITORS']}")
        if row["IMPLEMENTER"]:
            comp_parts.append(f":material/build: **Implementer:** {row['IMPLEMENTER']}")
        if row["PARTNER_NAME"]:
            comp_parts.append(f":material/handshake: **Partner:** {row['PARTNER_NAME']}")
        if comp_parts:
            st.markdown(" | ".join(comp_parts))

        if row["MEDDPICC_IDENTIFY_PAIN"]:
            st.markdown(f":material/psychology: **Pain:** {str(row['MEDDPICC_IDENTIFY_PAIN'])[:300]}")

        st.markdown("##### :material/analytics: Live Product Telemetry (90 days)")
        sfdc_account_id = row.get("ACCOUNT_ID")
        cust_usage = pd.DataFrame()
        if not usage_df.empty and sfdc_account_id:
            cust_usage = usage_df[usage_df["SALESFORCE_ACCOUNT_ID"] == sfdc_account_id]

        if not cust_usage.empty:
            svc_cols = st.columns(len(cust_usage))
            for col_idx, (_, u) in enumerate(cust_usage.iterrows()):
                with svc_cols[col_idx]:
                    icons = {"Openflow": ":material/sync_alt:", "Iceberg": ":material/ac_unit:", "SSV2": ":material/stream:"}
                    icon = icons.get(u["PRODUCT"], ":material/analytics:")
                    st.markdown(f"{icon} **{u['PRODUCT']}**")
                    st.metric(u["METRIC_LABEL"], f"{u['METRIC_COUNT']:,}")
                    st.caption(f"{safe_float(u['TOTAL_GB']):.1f} GB | Last: {str(u['LAST_SEEN'])[:10] if u['LAST_SEEN'] else 'N/A'}")
                    if u["DETAIL"]:
                        st.caption(str(u["DETAIL"])[:200])
        else:
            st.info("No Openflow, Iceberg, or SSV2 telemetry detected (Dynamic Tables & Snowpark telemetry not yet available in Snowhouse)", icon=":material/info:")
