import streamlit as st
import pandas as pd
import json

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/lightbulb: Product Opportunities")
st.caption("Cortex AI-powered product expansion opportunities — analyzes SFDC use case metadata with Snowflake Cortex LLM")

if st.session_state.get("is_default_view", False):
    if st.session_state.get("is_region_mode", False):
        st.info("Viewing **all accounts** in your selected region(s). Pick specific accounts from the sidebar to narrow down.", icon=":material/map:")
    else:
        st.info("Viewing **top 10 accounts** by EACV + ACV. Select specific accounts from the sidebar or switch to **Region / Territory** view.", icon=":material/filter_alt:")

FIVE_SERVICES = ["Openflow", "SSV2 (Snowpipe Streaming)", "Iceberg / Open Data Lake", "Dynamic Tables", "Snowpark"]

CORTEX_MODEL = "llama3.1-70b"

SYSTEM_PROMPT = """You are a Snowflake Applied Field Engineering (AFE) specialist. Your job is to analyze SFDC use case data and identify product expansion opportunities across these 5 Snowflake services:

1. **Openflow** — Data ingestion, CDC, database replication, SaaS connectors. Competitors: Fivetran, Airbyte, Informatica, Matillion, NiFi, Talend, Stitch, HVR, Qlik Replicate, Oracle GoldenGate, Oracle XStream.
2. **SSV2 (Snowpipe Streaming)** — Real-time streaming ingestion via Kafka connector, Kinesis, or custom SDK. Low-latency, event-driven pipelines. Competitors: Confluent, Amazon Kinesis, Azure Event Hubs, Google Pub/Sub.
3. **Iceberg / Open Data Lake** — Apache Iceberg tables, open table formats, interoperable storage, lakehouse architecture. Competitors: Databricks Delta Lake, Apache Hudi, AWS Lake Formation.
4. **Dynamic Tables** — Declarative data pipelines, continuous/incremental transformation, materialized views replacement. No direct competitor — replaces custom ETL/ELT orchestration (Airflow, dbt scheduling, stored procedures).
5. **Snowpark** — Python/Java/Scala compute on Snowflake, UDFs, Snowpark Connect for Spark migration. Competitors: Databricks, EMR, Spark on Kubernetes, Google Dataproc.

For each use case, analyze ALL text fields and return ONLY relevant product opportunities as a JSON array. Each opportunity must have:
- "product": One of the 5 service names EXACTLY as listed above
- "confidence": "HIGH" (strong explicit signals), "MEDIUM" (related technology patterns), or "LOW" (indirect/inferred fit)
- "rationale": 1-2 sentence explanation of WHY this is an opportunity
- "signals": Array of specific evidence found in the text

Rules:
- A use case can match 0 to 5 products. Only include genuine opportunities.
- HIGH = explicit product mention OR very strong direct signal (e.g., "CDC replication from Oracle" → HIGH for Openflow)
- MEDIUM = related technology pattern (e.g., "real-time data pipeline" → MEDIUM for SSV2)
- LOW = indirect/inferred fit (e.g., "data warehouse modernization" → LOW for Dynamic Tables)
- If a competing product is mentioned (e.g., Fivetran, Databricks, Kafka), flag it as a displacement opportunity
- Consider the incumbent vendor as competitive context
- Return ONLY a valid JSON array. No markdown, no explanation outside the JSON."""


def safe_int(v, default=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


@st.cache_data(ttl=300)
def load_use_case_data(filter_str):
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
        WHERE ({filter_str})
          AND USE_CASE_STATUS NOT IN ('Not In Pursuit', 'Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)


@st.cache_data(ttl=600)
def detect_opportunities_cortex(filter_str):
    result_df = run_query(f"""
        WITH use_cases AS (
            SELECT
                USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_ID, ACCOUNT_INDUSTRY,
                USE_CASE_NAME, USE_CASE_DESCRIPTION,
                TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
                COMPETITORS, INCUMBENT_VENDOR,
                USE_CASE_STAGE, REGION_NAME,
                OWNER_NAME, USE_CASE_LEAD_SE_NAME,
                IS_WON, IN_POC
            FROM MDM.MDM_INTERFACES.DIM_USE_CASE
            WHERE ({filter_str})
              AND USE_CASE_STATUS NOT IN ('Not In Pursuit', 'Closed - Lost', 'Closed - Archived')
        )
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_ID, ACCOUNT_INDUSTRY,
            USE_CASE_NAME, USE_CASE_STAGE, CLOUD_PROVIDER, REGION_NAME,
            INCUMBENT_VENDOR, COMPETITORS, OWNER_NAME, USE_CASE_LEAD_SE_NAME,
            IS_WON, IN_POC,
            SNOWFLAKE.CORTEX.COMPLETE(
                '{CORTEX_MODEL}',
                CONCAT(
                    '{SYSTEM_PROMPT.replace(chr(39), chr(39)+chr(39))}',
                    '\\n\\nUse Case Data:\\n',
                    '- Account: ', COALESCE(ACCOUNT_NAME, 'N/A'), '\\n',
                    '- Industry: ', COALESCE(ACCOUNT_INDUSTRY, 'N/A'), '\\n',
                    '- Use Case Name: ', COALESCE(USE_CASE_NAME, 'N/A'), '\\n',
                    '- Description: ', COALESCE(USE_CASE_DESCRIPTION, 'N/A'), '\\n',
                    '- Technical Use Case: ', COALESCE(TECHNICAL_USE_CASE, 'N/A'), '\\n',
                    '- Workloads: ', COALESCE(WORKLOADS, 'N/A'), '\\n',
                    '- Cloud Provider: ', COALESCE(CLOUD_PROVIDER, 'N/A'), '\\n',
                    '- Incumbent Vendor: ', COALESCE(INCUMBENT_VENDOR, 'N/A'), '\\n',
                    '- Competitors: ', COALESCE(COMPETITORS, 'N/A'), '\\n',
                    '\\nReturn ONLY a JSON array of opportunities. If none, return [].'
                )
            ) AS LLM_RESPONSE
        FROM use_cases
    """)
    return result_df


def parse_llm_opportunities(result_df):
    opps = []
    for _, row in result_df.iterrows():
        raw = str(row.get("LLM_RESPONSE") or "[]")
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
            else:
                parsed = []
        except (json.JSONDecodeError, ValueError):
            parsed = []

        base = dict(
            USE_CASE_ID=row["USE_CASE_ID"], ACCOUNT_NAME=row["ACCOUNT_NAME"],
            ACCOUNT_ID=row.get("ACCOUNT_ID"), ACCOUNT_INDUSTRY=row.get("ACCOUNT_INDUSTRY"),
            USE_CASE_NAME=row.get("USE_CASE_NAME"), USE_CASE_STAGE=str(row.get("USE_CASE_STAGE") or ""),
            CLOUD_PROVIDER=row.get("CLOUD_PROVIDER"), REGION_NAME=row.get("REGION_NAME"),
            INCUMBENT_VENDOR=str(row.get("INCUMBENT_VENDOR") or ""),
            COMPETITORS=row.get("COMPETITORS"),
            OWNER_NAME=row.get("OWNER_NAME"), LEAD_SE=row.get("USE_CASE_LEAD_SE_NAME"),
            IS_WON=row.get("IS_WON"), IN_POC=row.get("IN_POC"),
        )

        for item in parsed:
            product = item.get("product", "")
            if product not in FIVE_SERVICES:
                for svc in FIVE_SERVICES:
                    if product.lower() in svc.lower() or svc.lower().startswith(product.lower()):
                        product = svc
                        break
                else:
                    continue

            confidence = str(item.get("confidence", "LOW")).upper()
            if confidence not in ("HIGH", "MEDIUM", "LOW"):
                confidence = "MEDIUM"

            signals = item.get("signals", [])
            if isinstance(signals, str):
                signals = [signals]

            opps.append({
                **base,
                "PRODUCT": product,
                "CONFIDENCE": confidence,
                "RATIONALE": item.get("rationale", "Cortex AI-identified opportunity"),
                "SIGNALS": signals,
            })

    return pd.DataFrame(opps) if opps else pd.DataFrame(
        columns=["USE_CASE_ID", "ACCOUNT_NAME", "PRODUCT", "CONFIDENCE", "RATIONALE", "SIGNALS"]
    )


selected_names = st.session_state.get("selected_account_names", [])

with st.container(border=True):
    st.markdown("##### :material/psychology: How opportunities are detected")
    st.caption(
        "Opportunities are **identified by Snowflake Cortex AI** (llama3.1-70b) which analyzes each use case's SFDC fields: "
        "**Technical Use Case**, **Workloads**, **Use Case Description**, **Incumbent Vendor**, and **Competitors**. "
        "The LLM understands context, competitive dynamics, and technology patterns to map use cases to the 5 core AFE/PSS services. "
        "**HIGH** confidence = strong explicit signals. "
        "**MEDIUM** = related technology patterns. "
        "**LOW** = indirect/inferred fit. "
        "Results are cached for 10 minutes."
    )

if not selected_names:
    st.info("Select accounts from the sidebar to analyze opportunities.", icon=":material/filter_list:")
    st.stop()

selected_filter = filter_sql
acct_list = ",".join([f"'{n.replace(chr(39), chr(39)+chr(39))}'" for n in selected_names])
selected_filter = f"({filter_sql}) AND ACCOUNT_NAME IN ({acct_list})"

df = load_use_case_data(selected_filter)

st.info(
    f"Cortex AI will analyze **{len(df)}** use cases across **{len(selected_names)}** selected account(s). "
    f"To minimize LLM costs, select only the accounts you need from the sidebar.",
    icon=":material/toll:"
)

run_analysis = st.button(":material/psychology: Run Cortex AI Analysis", type="primary", key="run_opp_analysis")

if not run_analysis and "opp_results" not in st.session_state:
    st.caption("Click the button above to start the analysis.")
    st.stop()

if run_analysis:
    with st.spinner("Analyzing use cases with Cortex AI... This may take a minute."):
        raw_df = detect_opportunities_cortex(selected_filter)
        opps_df = parse_llm_opportunities(raw_df)
        st.session_state.opp_results = opps_df
        st.session_state.opp_filter_key = selected_filter
elif st.session_state.get("opp_filter_key") == selected_filter:
    opps_df = st.session_state.opp_results
else:
    del st.session_state["opp_results"]
    del st.session_state["opp_filter_key"]
    st.info("Account selection changed. Click **Run Cortex AI Analysis** to refresh results.", icon=":material/refresh:")
    st.stop()

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
    st.info("No product opportunities detected for the current filter. This may mean SFDC data lacks sufficient context for Cortex AI to identify opportunities.", icon=":material/info:")
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
                st.markdown(f":green[{high_count} HIGH confidence]")
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
                    color_map = {"green": "green", "orange": "orange", "gray": "gray"}
                    color_name = color_map.get(conf_color, "gray")
                    st.markdown(f":{color_name}[{opp['CONFIDENCE']}]")
