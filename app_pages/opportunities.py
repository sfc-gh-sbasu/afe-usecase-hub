import streamlit as st
import pandas as pd

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/lightbulb: Product Opportunities")
st.caption("AI-identified product expansion opportunities based on SFDC use case metadata, technical keywords, and competitive context")

FIVE_SERVICES = ["Openflow", "SSV2 (Snowpipe Streaming)", "Iceberg / Open Data Lake", "Dynamic Tables", "Snowpark"]


def safe_int(v, default=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


@st.cache_data(ttl=300)
def load_use_case_data(_filter):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_ID, ACCOUNT_INDUSTRY,
            USE_CASE_NAME, USE_CASE_DESCRIPTION,
            TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
            COMPETITORS, INCUMBENT_VENDOR, IMPLEMENTER, PARTNER_NAME,
            USE_CASE_STAGE, USE_CASE_STATUS,
            IS_WON, IS_LOST, IN_POC, REGION_NAME,
            OWNER_NAME, USE_CASE_LEAD_SE_NAME,
            DAYS_IN_STAGE, MEDDPICC_IDENTIFY_PAIN
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
        desc = str(row.get("USE_CASE_DESCRIPTION") or "").lower()
        combined = f"{tech} {workloads} {desc}"
        incumbent = str(row.get("INCUMBENT_VENDOR") or "")
        stage = str(row.get("USE_CASE_STAGE") or "")
        base = dict(
            USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
            ACCOUNT_ID=row.get("ACCOUNT_ID"), ACCOUNT_INDUSTRY=row.get("ACCOUNT_INDUSTRY"),
            USE_CASE_NAME=row.get("USE_CASE_NAME"), USE_CASE_STAGE=stage,
            CLOUD_PROVIDER=row.get("CLOUD_PROVIDER"), REGION_NAME=row.get("REGION_NAME"),
            INCUMBENT_VENDOR=incumbent, COMPETITORS=row.get("COMPETITORS"),
            OWNER_NAME=row.get("OWNER_NAME"), LEAD_SE=row.get("USE_CASE_LEAD_SE_NAME"),
            IS_WON=row.get("IS_WON"), IN_POC=row.get("IN_POC"),
        )

        if any(kw in combined for kw in ["ingestion", "openflow", "cdc", "replication", "nifi", "fivetran", "airbyte", "informatica", "matillion", "xstream", "goldengate"]):
            confidence = "HIGH" if "openflow" in combined else "MEDIUM"
            signals = []
            if "openflow" in combined:
                signals.append("Openflow explicitly mentioned in SFDC")
            if any(kw in combined for kw in ["cdc", "replication", "xstream", "goldengate"]):
                signals.append("CDC/replication keywords detected")
            if any(kw in combined for kw in ["fivetran", "airbyte", "informatica", "matillion", "nifi"]):
                signals.append(f"Competing tool mentioned — displacement opportunity")
            if incumbent and incumbent.lower() not in ["none", "nan", ""]:
                signals.append(f"Incumbent: {incumbent}")
            opps.append({**base, "PRODUCT": "Openflow", "CONFIDENCE": confidence,
                         "RATIONALE": f"Data ingestion/replication use case. {'; '.join(signals)}",
                         "SIGNALS": signals})

        if any(kw in combined for kw in ["iceberg", "interoperable storage", "data lake", "lakehouse", "parquet", "delta", "open format", "open table"]):
            confidence = "HIGH" if "iceberg" in combined else "MEDIUM"
            signals = []
            if "iceberg" in combined:
                signals.append("Iceberg explicitly mentioned")
            if any(kw in combined for kw in ["lakehouse", "delta", "databricks"]):
                signals.append("Lakehouse/Delta keywords — open format interest")
            if "parquet" in combined:
                signals.append("Parquet mentioned — open format storage need")
            opps.append({**base, "PRODUCT": "Iceberg / Open Data Lake", "CONFIDENCE": confidence,
                         "RATIONALE": f"Open data lake / Iceberg opportunity. {'; '.join(signals)}",
                         "SIGNALS": signals})

        if any(kw in combined for kw in ["streaming", "kafka", "kinesis", "snowpipe streaming", "real-time", "ssv2", "real time", "low latency"]):
            confidence = "HIGH" if any(kw in combined for kw in ["snowpipe", "ssv2"]) else "MEDIUM"
            signals = []
            if any(kw in combined for kw in ["snowpipe", "ssv2"]):
                signals.append("Snowpipe Streaming explicitly mentioned")
            if "kafka" in combined:
                signals.append("Kafka mentioned — SSV2 Kafka connector opportunity")
            if any(kw in combined for kw in ["real-time", "real time", "low latency"]):
                signals.append("Real-time / low-latency requirement")
            opps.append({**base, "PRODUCT": "SSV2 (Snowpipe Streaming)", "CONFIDENCE": confidence,
                         "RATIONALE": f"Streaming/real-time data use case. {'; '.join(signals)}",
                         "SIGNALS": signals})

        if any(kw in combined for kw in ["dynamic table", "continuous pipeline", "declarative pipeline", "materialized view", "incremental"]):
            confidence = "HIGH" if "dynamic table" in combined else "MEDIUM"
            signals = []
            if "dynamic table" in combined:
                signals.append("Dynamic Tables explicitly mentioned")
            if any(kw in combined for kw in ["pipeline", "transformation", "etl"]):
                signals.append("Data pipeline/transformation use case")
            if "incremental" in combined:
                signals.append("Incremental processing mentioned")
            opps.append({**base, "PRODUCT": "Dynamic Tables", "CONFIDENCE": confidence,
                         "RATIONALE": f"Data pipeline / transformation candidate. {'; '.join(signals)}",
                         "SIGNALS": signals})
        elif any(kw in combined for kw in ["pipeline", "transformation", "etl"]) and "dynamic table" not in combined:
            opps.append({**base, "PRODUCT": "Dynamic Tables", "CONFIDENCE": "LOW",
                         "RATIONALE": "Transformation/pipeline use case — could benefit from Dynamic Tables for declarative pipelines.",
                         "SIGNALS": ["Data transformation/ETL keywords detected"]})

        if any(kw in combined for kw in ["snowpark", "spark", "pyspark", "databricks", "python udf", "java udf"]):
            confidence = "HIGH" if "snowpark" in combined else "MEDIUM"
            signals = []
            if "snowpark" in combined:
                signals.append("Snowpark explicitly mentioned")
            if any(kw in combined for kw in ["spark", "pyspark", "databricks"]):
                signals.append("Spark/PySpark workload — Snowpark Connect migration opportunity")
            if any(kw in combined for kw in ["python udf", "java udf"]):
                signals.append("UDF development — Snowpark for custom compute")
            opps.append({**base, "PRODUCT": "Snowpark", "CONFIDENCE": confidence,
                         "RATIONALE": f"Compute/processing candidate. {'; '.join(signals)}",
                         "SIGNALS": signals})

    return pd.DataFrame(opps) if opps else pd.DataFrame(
        columns=["USE_CASE_ID", "ACCOUNT_NAME", "PRODUCT", "CONFIDENCE", "RATIONALE", "SIGNALS"]
    )


df = load_use_case_data(filter_sql)
opps_df = detect_opportunities(df)

with st.container(border=True):
    st.markdown("##### :material/info: How opportunities are detected")
    st.caption(
        "Opportunities are **automatically identified** by scanning each use case's SFDC fields: "
        "**Technical Use Case**, **Workloads**, **Use Case Description**, **Incumbent Vendor**, and **Competitors**. "
        "Keyword matching maps use cases to the 5 core AFE/PSS services. "
        "**HIGH** confidence = explicit product mention (e.g., 'Openflow', 'Iceberg'). "
        "**MEDIUM** = related keywords (e.g., 'CDC', 'lakehouse'). "
        "**LOW** = broad match (e.g., 'ETL' → Dynamic Tables). "
        "A single use case can generate multiple opportunities across different products."
    )

svc_metrics = st.columns(5)
for col, svc in zip(svc_metrics, FIVE_SERVICES):
    svc_opps = opps_df[opps_df["PRODUCT"] == svc] if not opps_df.empty else pd.DataFrame()
    high_ct = len(svc_opps[svc_opps["CONFIDENCE"] == "HIGH"]) if not svc_opps.empty else 0
    label = svc.split("(")[0].strip().split("/")[0].strip()
    col.metric(label, len(svc_opps), delta=f"{high_ct} HIGH" if high_ct else "0 HIGH",
               delta_color="normal" if high_ct else "off")

st.divider()

fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
search = fc1.text_input(":material/search: Search", placeholder="Customer, product, rationale...", key="opp_search")
product_filter = fc2.selectbox("Service", ["All"] + FIVE_SERVICES, key="opp_prod")
conf_filter = fc3.selectbox("Confidence", ["All", "HIGH", "MEDIUM", "LOW"], key="opp_conf")
sort_dir = fc4.selectbox("Order", ["Asc", "Desc"], key="opp_dir")

filtered = opps_df.copy()
if search:
    mask = filtered.apply(lambda r: search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1)
    filtered = filtered[mask]
if product_filter and product_filter != "All":
    filtered = filtered[filtered["PRODUCT"] == product_filter]
if conf_filter and conf_filter != "All":
    filtered = filtered[filtered["CONFIDENCE"] == conf_filter]
filtered = filtered.sort_values("ACCOUNT_NAME", ascending=(sort_dir == "Asc"), na_position="last")

if filtered.empty:
    st.info("No product opportunities detected for the current filter. This may mean SFDC data lacks product-specific keywords for your use cases.", icon=":material/info:")
    st.stop()

ovc1, ovc2 = st.columns(2)
with ovc1:
    st.subheader("By service")
    prod_counts = filtered["PRODUCT"].value_counts()
    st.bar_chart(prod_counts, horizontal=True, color="#29B5E8")
with ovc2:
    st.subheader("By confidence")
    conf_counts = filtered["CONFIDENCE"].value_counts()
    st.bar_chart(conf_counts, horizontal=True, color="#FF6F61")

st.divider()

accounts = filtered["ACCOUNT_NAME"].unique()
for acct in accounts:
    acct_opps = filtered[filtered["ACCOUNT_NAME"] == acct]
    first_row = acct_opps.iloc[0]
    products_str = ", ".join(acct_opps["PRODUCT"].unique())
    high_count = len(acct_opps[acct_opps["CONFIDENCE"] == "HIGH"])

    status_badge = ""
    if first_row.get("IS_WON"):
        status_badge = ":material/celebration: Won"
    elif first_row.get("IN_POC"):
        status_badge = ":material/science: POC"
    else:
        status_badge = f":material/trending_up: {(first_row.get('USE_CASE_STAGE') or 'N/A').split(' - ')[-1]}"

    with st.container(border=True):
        hdr1, hdr2, hdr3 = st.columns([2, 2, 1])
        with hdr1:
            st.subheader(first_row["ACCOUNT_NAME"])
            st.caption(f":material/domain: {first_row.get('ACCOUNT_INDUSTRY') or 'N/A'} | "
                       f":material/map: {first_row.get('REGION_NAME') or 'N/A'} | "
                       f":material/cloud: {first_row.get('CLOUD_PROVIDER') or 'Unknown'}")
        with hdr2:
            st.markdown(f"**{len(acct_opps)} opportunities** across: {products_str}")
            if high_count:
                st.badge(f"{high_count} HIGH confidence", color="green")
            st.caption(f"{status_badge} | **AE:** {first_row.get('OWNER_NAME') or 'N/A'} | **SE:** {first_row.get('LEAD_SE') or 'N/A'}")
        with hdr3:
            sfdc_url = f"https://snowforce.lightning.force.com/lightning/r/Use_Case__c/{first_row['USE_CASE_ID']}/view"
            st.link_button("Open SFDC", sfdc_url, icon=":material/open_in_new:")

        if first_row.get("INCUMBENT_VENDOR") and str(first_row["INCUMBENT_VENDOR"]).lower() not in ["none", "nan", ""]:
            st.caption(f":material/swap_horiz: **Incumbent:** {first_row['INCUMBENT_VENDOR']}"
                       + (f" | :material/swords: **Competing:** {first_row['COMPETITORS']}" if first_row.get("COMPETITORS") else ""))

        for _, opp in acct_opps.iterrows():
            conf_color = "green" if opp["CONFIDENCE"] == "HIGH" else "orange" if opp["CONFIDENCE"] == "MEDIUM" else "gray"
            product_icons = {
                "Openflow": ":material/sync_alt:",
                "Iceberg / Open Data Lake": ":material/ac_unit:",
                "SSV2 (Snowpipe Streaming)": ":material/stream:",
                "Dynamic Tables": ":material/autorenew:",
                "Snowpark": ":material/code:",
            }
            icon = product_icons.get(opp["PRODUCT"], ":material/lightbulb:")

            with st.container(border=True):
                oc1, oc2, oc3 = st.columns([1, 3, 1])
                with oc1:
                    st.markdown(f"{icon} **{opp['PRODUCT']}**")
                with oc2:
                    st.caption(opp["RATIONALE"])
                    signals = opp.get("SIGNALS")
                    if signals and isinstance(signals, list):
                        for sig in signals:
                            st.caption(f"  :material/check: {sig}")
                with oc3:
                    st.badge(opp["CONFIDENCE"], color=conf_color)
