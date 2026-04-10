import streamlit as st
import pandas as pd

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/lightbulb: Product Opportunities")
st.caption("AI-identified product opportunities derived from use case metadata")


@st.cache_data(ttl=300)
def load_use_case_data(_filter):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_INDUSTRY,
            TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
            COMPETITORS, INCUMBENT_VENDOR, IMPLEMENTER, PARTNER_NAME,
            USE_CASE_STAGE, USE_CASE_STATUS, USE_CASE_NAME,
            IS_WON, IS_LOST, IN_POC, REGION_NAME
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)


def detect_opportunities(df):
    opps = []
    for _, row in df.iterrows():
        tech = str(row.get("TECHNICAL_USE_CASE") or "").lower()
        workloads = str(row.get("WORKLOADS") or "").lower()
        incumbent = str(row.get("INCUMBENT_VENDOR") or "").lower()
        stage = str(row.get("USE_CASE_STAGE") or "")

        if any(kw in tech for kw in ["ingestion", "openflow", "cdc", "replication", "nifi", "fivetran", "airbyte", "informatica", "matillion"]):
            confidence = "HIGH" if "openflow" in tech else "MEDIUM"
            rationale = f"Use case involves data ingestion/replication. Incumbent: {row['INCUMBENT_VENDOR'] or 'None'}. Good fit for Openflow."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Openflow", CONFIDENCE=confidence, RATIONALE=rationale, STATUS="Active"))

        if any(kw in tech for kw in ["iceberg", "interoperable storage", "data lake", "lakehouse", "parquet", "delta"]):
            confidence = "HIGH" if "iceberg" in tech else "MEDIUM"
            rationale = f"Iceberg/lakehouse mentioned in use case. Cloud: {row['CLOUD_PROVIDER'] or 'Unknown'}."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Iceberg/Lakehouse", CONFIDENCE=confidence, RATIONALE=rationale, STATUS="Active"))

        if any(kw in tech for kw in ["streaming", "kafka", "kinesis", "snowpipe streaming", "real-time", "ssv2"]):
            confidence = "HIGH" if "snowpipe" in tech or "ssv2" in tech else "MEDIUM"
            rationale = "Real-time/streaming use case. Candidate for Snowpipe Streaming V2."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Snowpipe Streaming", CONFIDENCE=confidence, RATIONALE=rationale, STATUS="Active"))

        if any(kw in tech for kw in ["cortex", "machine learning", "ai", "llm", "chatbot", "summarization", "classification"]):
            confidence = "HIGH" if "cortex" in tech else "MEDIUM"
            rationale = "AI/ML referenced in use case. Opportunity for Cortex AI or Cortex Agent."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Cortex AI/ML", CONFIDENCE=confidence, RATIONALE=rationale, STATUS="Active"))

        if any(kw in tech for kw in ["conversational", "agent", "natural language", "text-to-sql"]):
            confidence = "HIGH" if "agent" in tech else "MEDIUM"
            rationale = "Conversational/agent use case. Strong candidate for Cortex Agent."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Cortex Agent", CONFIDENCE=confidence, RATIONALE=rationale, STATUS="Active"))

        if "snowpark" in tech and any(kw in tech for kw in ["spark", "pyspark", "databricks"]):
            rationale = "Spark/PySpark workload. Candidate for Snowpark Connect migration."
            opps.append(dict(USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
                             PRODUCT="Snowpark Connect", CONFIDENCE="MEDIUM", RATIONALE=rationale, STATUS="Active"))

    return pd.DataFrame(opps) if opps else pd.DataFrame(
        columns=["USE_CASE_ID", "ACCOUNT_NAME", "PRODUCT", "CONFIDENCE", "RATIONALE", "STATUS"]
    )


df = load_use_case_data(filter_sql)
opps_df = detect_opportunities(df)

col1, col2, col3 = st.columns(3)
col1.metric("Total opportunities", len(opps_df))
col2.metric("High confidence", len(opps_df[opps_df["CONFIDENCE"] == "HIGH"]) if not opps_df.empty else 0)
col3.metric("Accounts with opps", opps_df["ACCOUNT_NAME"].nunique() if not opps_df.empty else 0)

st.divider()

if opps_df.empty:
    st.info("No product opportunities detected from current use case metadata. This may mean the SFDC data lacks product-specific keywords.", icon=":material/info:")
    st.stop()

fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
search = fc1.text_input(":material/search: Search", placeholder="Customer, product, rationale...", key="opp_search")
product_filter = fc2.selectbox("Product", ["All"] + sorted(opps_df["PRODUCT"].unique().tolist()), key="opp_prod")
sort_col = fc3.selectbox("Sort by", ["Confidence", "Customer", "Product"], key="opp_sort")
sort_dir = fc4.selectbox("Order", ["Asc", "Desc"], key="opp_dir")

filtered = opps_df.copy()
if search:
    mask = filtered.apply(lambda r: search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1)
    filtered = filtered[mask]
if product_filter and product_filter != "All":
    filtered = filtered[filtered["PRODUCT"] == product_filter]
sort_map = {"Confidence": "CONFIDENCE", "Customer": "ACCOUNT_NAME", "Product": "PRODUCT"}
filtered = filtered.sort_values(sort_map[sort_col], ascending=(sort_dir == "Asc"), na_position="last")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("By product")
    prod_counts = filtered["PRODUCT"].value_counts()
    st.bar_chart(prod_counts, horizontal=True, color="#29B5E8")
with col_b:
    st.subheader("By confidence")
    conf_counts = filtered["CONFIDENCE"].value_counts()
    st.bar_chart(conf_counts, horizontal=True, color="#FF6F61")

st.divider()

for _, row in filtered.iterrows():
    conf_color = "green" if row["CONFIDENCE"] == "HIGH" else "orange" if row["CONFIDENCE"] == "MEDIUM" else "gray"
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(f"**{row['ACCOUNT_NAME']}**")
        c2.write(f":material/rocket_launch: {row['PRODUCT']}")
        c3.badge(row["CONFIDENCE"], color=conf_color)
        st.caption(row["RATIONALE"])
