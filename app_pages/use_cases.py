import streamlit as st
import pandas as pd
import re

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/work: Customer Use Cases")
st.caption("Use case lifecycle, activity, and next-step guidance")

ALL_STAGES = [
    "1 - Discovery",
    "2 - Scoping",
    "3 - Technical / Business Validation",
    "4 - Use Case Won / Migration Plan",
    "5 - Implementation In Progress",
    "6 - Implementation Complete",
    "7 - Deployed",
    "8 - Use Case Lost",
]


def render_lifecycle_bar(current_stage):
    current_stage = str(current_stage or "")
    current_idx = -1
    for i, s in enumerate(ALL_STAGES):
        if s == current_stage or current_stage.startswith(s.split(" - ")[0]):
            current_idx = i
            break

    is_lost = current_idx == 7

    chevrons = []
    for i, stage in enumerate(ALL_STAGES):
        label = stage.split(" - ", 1)[1]
        if i == 7:
            if is_lost:
                bg = "#e74c3c"
                fg = "#fff"
            else:
                bg = "#f0f0f0"
                fg = "#999"
        elif is_lost:
            bg = "#f0f0f0"
            fg = "#999"
        elif i < current_idx:
            bg = "#29B5E8"
            fg = "#fff"
        elif i == current_idx:
            bg = "#1a8cb4"
            fg = "#fff"
        else:
            bg = "#f0f0f0"
            fg = "#666"

        check = "&#10003; " if (i < current_idx and not is_lost) else ""
        chevrons.append(
            f'<div style="display:inline-flex;align-items:center;justify-content:center;'
            f'padding:4px 14px 4px 20px;background:{bg};color:{fg};'
            f'font-size:11px;font-weight:{"700" if i == current_idx else "500"};'
            f'clip-path:polygon(0 0,calc(100% - 10px) 0,100% 50%,calc(100% - 10px) 100%,0 100%,10px 50%);'
            f'margin-left:-6px;white-space:nowrap;">{check}{label}</div>'
        )
    html = (
        '<div style="display:flex;align-items:center;overflow-x:auto;padding:2px 0 2px 6px;">'
        + "".join(chevrons)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def build_win_unblock_summary(row):
    parts = []
    stage = str(row.get("USE_CASE_STAGE") or "")
    days = row.get("DAYS_IN_STAGE")
    risk = row.get("RISK_DESCRIPTION")
    next_steps = row.get("NEXT_STEPS") or ""
    meddpicc_pain = row.get("MEDDPICC_IDENTIFY_PAIN") or ""
    meddpicc_champion = row.get("MEDDPICC_CHAMPION") or ""
    incumbent = row.get("INCUMBENT_VENDOR") or ""
    competitors = row.get("COMPETITORS") or ""
    poc_stage = row.get("POC_STAGE") or ""
    decision_date = row.get("DECISION_DATE")
    go_live = row.get("GO_LIVE_DATE")
    is_lost = bool(row.get("IS_LOST"))

    if is_lost or "8 -" in stage:
        return None, "lost"
    if "7 - Deployed" in stage:
        return None, "deployed"

    if days is not None and days and int(days) > 60:
        parts.append(f":material/schedule: **Stale — {int(days)} days in stage.** Needs re-engagement or stage update.")

    if risk:
        parts.append(f":material/error: **Risk:** {str(risk)[:300]}")

    if "1 - Discovery" in stage:
        parts.append(":material/search: **Discovery** — Qualify the use case: confirm pain, identify champion, define success criteria.")
        if not meddpicc_pain:
            parts.append(":material/psychology: **MEDDPICC gap:** Pain not documented. Schedule discovery call.")
        if not meddpicc_champion:
            parts.append(":material/person: **MEDDPICC gap:** No champion identified. Find technical sponsor.")
    elif "2 - Scoping" in stage:
        parts.append(":material/rule: **Scoping** — Define technical requirements, architecture, and POC scope.")
        if incumbent:
            parts.append(f":material/swap_horiz: Displacing **{incumbent}**. Build competitive differentiation deck.")
    elif "3 - Technical" in stage:
        parts.append(":material/science: **Validation** — Execute POC or technical proof. Drive to a decision.")
        if poc_stage:
            parts.append(f":material/labs: POC Stage: **{poc_stage}**")
        if decision_date:
            parts.append(f":material/event: Decision date: **{str(decision_date)[:10]}**")
        if competitors:
            parts.append(f":material/swords: Competing with: **{competitors}**")
    elif "4 - Use Case Won" in stage:
        parts.append(":material/celebration: **Won** — Transition to implementation. Define migration plan, timeline, and Go-Live target.")
    elif "5 - Implementation" in stage:
        parts.append(":material/build: **In Progress** — Monitor implementation health. Unblock technical issues.")
        if go_live:
            parts.append(f":material/rocket_launch: Go-Live target: **{str(go_live)[:10]}**")
    elif "6 - Implementation Complete" in stage:
        parts.append(":material/verified: **Implementation Complete** — Confirm production workload is running. Update stage to Deployed.")

    if next_steps:
        steps_preview = str(next_steps)[:300].replace("\n", " ")
        parts.append(f":material/checklist: **Next Steps:** {steps_preview}")

    if not parts:
        parts.append(":material/trending_up: No specific blockers identified. Review SFDC for latest activity.")

    return parts, "active"


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


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', str(text))
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&#39;', "'").replace('&amp;', '&').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    return text.strip()


def generate_expansion_recs(row, product_usage_df, meetings_df):
    recs = []
    name = (row.get("USE_CASE_NAME") or "").lower()
    desc = (row.get("USE_CASE_DESCRIPTION") or "").lower()
    tech = (row.get("TECHNICAL_USE_CASE") or "").lower()
    combined = f"{name} {desc} {tech}"

    has_openflow = not product_usage_df.empty and "Openflow" in product_usage_df["PRODUCT"].values
    has_iceberg = not product_usage_df.empty and "Iceberg" in product_usage_df["PRODUCT"].values
    has_ssv2 = not product_usage_df.empty and "SSV2" in product_usage_df["PRODUCT"].values

    call_text = ""
    if not meetings_df.empty:
        call_text = " ".join(meetings_df["CALL_BRIEF"].dropna().head(5).tolist()).lower()

    if not has_openflow and ("ingestion" in combined or "etl" in combined or "replication" in combined or "cdc" in combined):
        recs.append("Openflow: Customer has ingestion/ETL needs but no Openflow adoption yet. Propose Openflow to replace legacy CDC/replication tools.")
    elif has_openflow and not has_iceberg:
        recs.append("Iceberg Tables: Customer uses Openflow for ingestion. Propose Iceberg tables for open lakehouse storage to complement their data pipeline.")

    if not has_iceberg and ("lakehouse" in combined or "databricks" in combined or "delta" in combined or "parquet" in combined):
        recs.append("Iceberg/Lakehouse: Customer discusses lakehouse patterns. Propose Snowflake-managed Iceberg tables for interoperable open-format storage.")

    if not has_ssv2 and ("streaming" in combined or "real-time" in combined or "kafka" in combined or "kinesis" in combined):
        recs.append("Snowpipe Streaming V2: Customer has real-time/streaming requirements. Propose SSV2 for sub-second streaming ingestion.")

    if "cortex" not in combined and "ml" not in combined and "machine learning" not in tech:
        if "analytics" in combined or "reporting" in combined or "dashboard" in combined:
            recs.append("Cortex AI: Customer focuses on analytics — propose Cortex AI functions (AI_CLASSIFY, AI_SUMMARIZE, AI_EXTRACT) to add intelligence to their data pipelines.")
        if "search" in call_text or "natural language" in call_text:
            recs.append("Cortex Search / Intelligence: Conversations mention search or NL queries — propose Snowflake Intelligence for text-to-SQL analytics.")

    if "agent" not in combined and "conversational" not in tech:
        if "chatbot" in call_text or "agent" in call_text or "rag" in call_text:
            recs.append("Cortex Agents: Meeting discussions reference agents/chatbots/RAG — propose Cortex Agents for conversational AI over their data.")

    if "dynamic table" not in combined and ("pipeline" in combined or "transformation" in combined):
        recs.append("Dynamic Tables: Customer has data transformation needs — propose Dynamic Tables for declarative, auto-refreshing data pipelines.")

    if "snowpark" not in combined and ("spark" in combined or "python" in combined or "pyspark" in combined):
        recs.append("Snowpark / Snowpark Connect: Customer uses Spark/Python workloads — propose Snowpark Connect for seamless Spark-to-Snowflake migration.")

    if "streamlit" not in combined and ("dashboard" in combined or "app" in combined or "visualization" in combined):
        recs.append("Streamlit in Snowflake: Customer needs dashboards/apps — propose Streamlit in Snowflake for governed data applications.")

    if not recs:
        recs.append("Platform Growth: Explore Cortex AI, Dynamic Tables, or Snowflake Intelligence as next steps to deepen Snowflake adoption.")

    return recs[:5]


@st.cache_data(ttl=300)
def load_use_cases(filter_str):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME, ACCOUNT_INDUSTRY,
            USE_CASE_NAME, USE_CASE_STAGE, USE_CASE_STATUS,
            TECHNICAL_USE_CASE, WORKLOADS, CLOUD_PROVIDER,
            COMPETITORS, INCUMBENT_VENDOR, IMPLEMENTER, PARTNER_NAME,
            USE_CASE_LEAD_SE_NAME, OWNER_NAME,
            NEXT_STEPS, USE_CASE_DESCRIPTION,
            DAYS_IN_STAGE, IS_WON, IS_LOST, IS_TECH_WON, IN_POC,
            MEDDPICC_IDENTIFY_PAIN, MEDDPICC_CHAMPION, MEDDPICC_METRICS,
            SE_COMMENTS, SPECIALIST_COMMENTS, PARTNER_COMMENTS,
            POC_STAGE, POC_START_DATE, POC_END_DATE,
            RISK_DESCRIPTION, USE_CASE_RISK_LEVEL,
            GO_LIVE_DATE, DECISION_DATE,
            REGION_NAME, ACCOUNT_ID,
            USE_CASE_EACV, ACCOUNT_BASE_RENEWAL_ACV
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({filter_str})
          AND USE_CASE_STATUS NOT IN ('Not In Pursuit', 'Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)


@st.cache_data(ttl=600)
def load_product_usage(sfdc_account_ids_csv):
    if not sfdc_account_ids_csv:
        return pd.DataFrame()

    sfdc_ids_list = [s.strip().strip("'") for s in sfdc_account_ids_csv.split(",") if s.strip()]
    sfdc_values = ",\n".join([f"('{sid}')" for sid in sfdc_ids_list])

    df = run_query(f"""
        WITH sfdc_filter AS (SELECT $1 as SFDC_ID FROM VALUES {sfdc_values})
        SELECT t.SALESFORCE_ACCOUNT_ID, t.PRODUCT,
               t.DETAIL as USAGE_DETAIL,
               CASE WHEN t.PRODUCT = 'Openflow' THEN t.METRIC_COUNT ELSE 0 END as CONNECTOR_COUNT,
               CASE WHEN t.PRODUCT = 'Iceberg' THEN t.METRIC_COUNT ELSE 0 END as TABLE_COUNT,
               CASE WHEN t.PRODUCT = 'SSV2' THEN t.METRIC_COUNT ELSE 0 END as CHANNEL_COUNT,
               t.TOTAL_GB, t.TOTAL_CREDITS,
               t.FIRST_SEEN, t.LAST_SEEN,
               TRUE as IS_ACTIVE
        FROM TEMP.SBASU.HUB_PRODUCT_TELEMETRY t
        JOIN sfdc_filter sf ON t.SALESFORCE_ACCOUNT_ID = sf.SFDC_ID
    """)
    return df


@st.cache_data(ttl=600)
def load_gong_meetings(sfdc_account_ids_csv):
    if not sfdc_account_ids_csv:
        return pd.DataFrame()

    sfdc_ids_list = [s.strip().strip("'") for s in sfdc_account_ids_csv.split(",") if s.strip()]
    sfdc_values = ",\n".join([f"('{sid}')" for sid in sfdc_ids_list])

    return run_query(f"""
        WITH sfdc_filter AS (SELECT $1 as SFDC_ID FROM VALUES {sfdc_values})
        SELECT t.SALESFORCE_ACCOUNT_ID, t.MEETING_TITLE, t.MEETING_DATE,
               t.DURATION_DISPLAY, t.PARTICIPANTS_EMAILS, t.CALL_BRIEF,
               t.KEY_POINTS, t.NEXT_STEPS_GONG, t.VIEW_CALL_HTML, t.CALL_ID
        FROM TEMP.SBASU.HUB_GONG_MEETINGS t
        JOIN sfdc_filter sf ON t.SALESFORCE_ACCOUNT_ID = sf.SFDC_ID
        ORDER BY t.SALESFORCE_ACCOUNT_ID, t.MEETING_DATE DESC
    """)


all_df = load_use_cases(filter_sql)
total_accounts = all_df["ACCOUNT_NAME"].nunique()

selected_ids = st.session_state.get("selected_sfdc_ids", [])
selected_names = st.session_state.get("selected_account_names", [])

df = all_df[all_df["ACCOUNT_NAME"].isin(selected_names)] if selected_names else all_df

if selected_ids:
    sel_csv = ",".join([f"'{aid}'" for aid in selected_ids])
    usage_df = load_product_usage(sel_csv)
    meetings_all_df = load_gong_meetings(sel_csv)
else:
    usage_df = pd.DataFrame()
    meetings_all_df = pd.DataFrame()

loaded_accounts = len(selected_names) if selected_names else total_accounts
if loaded_accounts < total_accounts:
    st.info(
        f"Showing **{loaded_accounts}** of **{total_accounts}** accounts (top 10 by EACV + ACV). "
        f"Select more accounts from the sidebar dropdown.",
        icon=":material/filter_list:"
    )

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Use Cases", len(df))
col2.metric("Active", len(df[~df["IS_LOST"].astype(bool)]))
col3.metric("Won", len(df[df["IS_WON"].astype(bool)]))
col4.metric("In POC", len(df[df["IN_POC"].astype(bool)]))

st.divider()

fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
search = fc1.text_input(":material/search: Search", placeholder="Customer, product, status...", key="uc_search")
stage_filter = fc2.selectbox("Stage", ["All"] + ALL_STAGES, key="uc_stage")
sort_col = fc3.selectbox("Sort by", ["Customer", "Stage", "Days in Stage", "Industry", "Region"], key="uc_sort")
sort_dir = fc4.selectbox("Order", ["Asc", "Desc"], key="uc_dir")

sort_map = {
    "Customer": "ACCOUNT_NAME", "Stage": "USE_CASE_STAGE",
    "Days in Stage": "DAYS_IN_STAGE", "Industry": "ACCOUNT_INDUSTRY",
    "Region": "REGION_NAME"
}

filtered = df.copy()
if search:
    mask = filtered.apply(lambda r: search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1)
    filtered = filtered[mask]
if stage_filter and stage_filter != "All":
    filtered = filtered[filtered["USE_CASE_STAGE"] == stage_filter]
filtered = filtered.sort_values(sort_map[sort_col], ascending=(sort_dir == "Asc"), na_position="last")

for _, row in filtered.iterrows():
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(row["ACCOUNT_NAME"])
            focus = row["TECHNICAL_USE_CASE"] or row["WORKLOADS"] or ""
            if focus:
                st.caption(focus)
        with c2:
            if row["IS_LOST"]:
                st.markdown(":red[:material/block: Lost]")
            elif row["IS_WON"]:
                st.markdown(":green[:material/celebration: Won]")
            elif row["IN_POC"]:
                st.markdown(":blue[:material/science: POC]")
            else:
                st.markdown(":orange[:material/trending_up: In Pursuit]")

        render_lifecycle_bar(row["USE_CASE_STAGE"])

        win_items, win_status = build_win_unblock_summary(row)
        if win_status == "active" and win_items:
            with st.expander(":material/lightbulb: **What to do to win / unblock**", expanded=False):
                for item in win_items:
                    st.markdown(item)
        elif win_status == "deployed":
            st.success("Deployed and in production", icon=":material/check_circle:")

        tab_snapshot, tab_detail = st.tabs([":material/update: Snapshot", ":material/info: Details"])

        with tab_snapshot:
            snap_cols = st.columns(3)
            with snap_cols[0]:
                eacv = safe_float(row.get("USE_CASE_EACV"))
                acv = safe_float(row.get("ACCOUNT_BASE_RENEWAL_ACV"))
                if eacv:
                    st.markdown(f":material/attach_money: **EACV:** ${eacv:,.0f}")
                if acv:
                    st.caption(f":material/account_balance: ACV: ${acv:,.0f}")
                days = row["DAYS_IN_STAGE"]
                if days is not None and pd.notna(days):
                    st.markdown(f":material/timer: **Days in Stage:** {safe_int(days)}")
                if row["OWNER_NAME"]:
                    st.caption(f":material/sell: AE: {row['OWNER_NAME']}")
                if row["USE_CASE_LEAD_SE_NAME"]:
                    st.caption(f":material/engineering: Lead SE: {row['USE_CASE_LEAD_SE_NAME']}")
            with snap_cols[1]:
                if row["REGION_NAME"]:
                    st.markdown(f":material/map: **Region:** {row['REGION_NAME']}")
                if row["ACCOUNT_INDUSTRY"]:
                    st.caption(f":material/domain: {row['ACCOUNT_INDUSTRY']}")
            with snap_cols[2]:
                if row["DECISION_DATE"]:
                    st.markdown(f":material/event: **Decision:** {str(row['DECISION_DATE'])[:10]}")
                if row["GO_LIVE_DATE"]:
                    st.caption(f":material/rocket_launch: Go-Live: {str(row['GO_LIVE_DATE'])[:10]}")
                if row["POC_STAGE"]:
                    st.caption(f":material/science: POC: {row['POC_STAGE']}")

            next_steps = row["NEXT_STEPS"]
            if next_steps:
                with st.expander(":material/checklist: **SFDC Next Steps**"):
                    st.write(str(next_steps)[:1500])
            se_cmt = row["SE_COMMENTS"]
            if se_cmt:
                with st.expander(":material/edit_note: **SE Comments**"):
                    st.write(str(se_cmt)[:1500])

        with tab_detail:
            sfdc_url = f"https://snowforce.lightning.force.com/lightning/r/Use_Case__c/{row['USE_CASE_ID']}/view"
            sfdc_account_id = row["ACCOUNT_ID"]

            detail_header = st.columns([2, 1, 1])
            with detail_header[0]:
                if row["ACCOUNT_INDUSTRY"]:
                    st.caption(f":material/domain: **Industry:** {row['ACCOUNT_INDUSTRY']} | **Stage:** {row['USE_CASE_STAGE'] or 'N/A'}")
                if row["OWNER_NAME"] or row["USE_CASE_LEAD_SE_NAME"]:
                    st.caption(f":material/person: **AE:** {row['OWNER_NAME'] or 'N/A'} | **Lead SE:** {row['USE_CASE_LEAD_SE_NAME'] or 'N/A'}")
                eacv = safe_float(row.get("USE_CASE_EACV"))
                acv = safe_float(row.get("ACCOUNT_BASE_RENEWAL_ACV"))
                acv_parts = []
                if eacv:
                    acv_parts.append(f"**EACV:** ${eacv:,.0f}")
                if acv:
                    acv_parts.append(f"**ACV:** ${acv:,.0f}")
                if acv_parts:
                    st.caption(f":material/attach_money: {' | '.join(acv_parts)}")
            with detail_header[1]:
                cloud = row["CLOUD_PROVIDER"] or "Unknown"
                st.caption(f":material/cloud: **Deploy:** {cloud}")
            with detail_header[2]:
                st.link_button("Open in SFDC", sfdc_url, icon=":material/open_in_new:")

            if row["RISK_DESCRIPTION"]:
                st.error(f"**Risk:** {str(row['RISK_DESCRIPTION'])[:500]}", icon=":material/error:")

            sec1, sec2 = st.columns(2)

            with sec1:
                st.markdown("##### :material/analytics: Product Usage State")
                cust_usage = pd.DataFrame()
                if not usage_df.empty and sfdc_account_id:
                    cust_usage = usage_df[usage_df["SALESFORCE_ACCOUNT_ID"] == sfdc_account_id]

                if not cust_usage.empty:
                    for _, u in cust_usage.iterrows():
                        product = u["PRODUCT"]
                        if product == "Openflow":
                            active_label = "Active" if u["IS_ACTIVE"] else "Inactive"
                            st.markdown(f":material/sync_alt: **Openflow** ({active_label})")
                            st.caption(f"{u['USAGE_DETAIL']}")
                            mc = st.columns(3)
                            mc[0].metric("Connectors", safe_int(u["CONNECTOR_COUNT"]))
                            mc[1].metric("Data Out (GB)", f"{safe_float(u['TOTAL_GB']):.1f}")
                            mc[2].metric("Last Seen", str(u["LAST_SEEN"])[:10] if u["LAST_SEEN"] else "N/A")
                        elif product == "Iceberg":
                            st.markdown(f":material/ac_unit: **Iceberg Tables**")
                            st.caption(u["USAGE_DETAIL"])
                            mc = st.columns(3)
                            mc[0].metric("Tables", f"{safe_int(u['TABLE_COUNT']):,}")
                            gb = safe_float(u["TOTAL_GB"])
                            mc[1].metric("Storage", f"{gb/1000:.1f} TB" if gb > 1000 else f"{gb:.1f} GB")
                            mc[2].metric("Credits (90d)", f"{safe_float(u['TOTAL_CREDITS']):,.0f}")
                        elif product == "SSV2":
                            st.markdown(f":material/stream: **Snowpipe Streaming V2**")
                            st.caption(u["USAGE_DETAIL"])
                            mc = st.columns(2)
                            mc[0].metric("Channels", safe_int(u["CHANNEL_COUNT"]))
                            mc[1].metric("Ingested (GB)", f"{safe_float(u['TOTAL_GB']):.2f}")
                else:
                    st.info("No Openflow, Iceberg, or SSV2 telemetry detected for this account", icon=":material/info:")

            with sec2:
                st.markdown("##### :material/edit_note: Comments")
                has_comments = bool(row["SE_COMMENTS"]) or bool(row["SPECIALIST_COMMENTS"]) or bool(row["PARTNER_COMMENTS"])
                if has_comments:
                    if row["SE_COMMENTS"]:
                        with st.expander(":material/person: **SE Comments**", expanded=True):
                            st.write(str(row["SE_COMMENTS"])[:3000])
                    if row["SPECIALIST_COMMENTS"]:
                        with st.expander(":material/engineering: **Specialist Comments**"):
                            st.write(str(row["SPECIALIST_COMMENTS"])[:3000])
                    if row["PARTNER_COMMENTS"]:
                        with st.expander(":material/handshake: **Partner Comments**"):
                            st.write(str(row["PARTNER_COMMENTS"])[:3000])
                else:
                    st.info("No SE, specialist, or partner comments recorded in SFDC", icon=":material/info:")

                if row["MEDDPICC_IDENTIFY_PAIN"] or row["MEDDPICC_CHAMPION"] or row["MEDDPICC_METRICS"]:
                    with st.expander(":material/psychology: **MEDDPICC**"):
                        if row["MEDDPICC_IDENTIFY_PAIN"]:
                            st.markdown(f"**Pain:** {str(row['MEDDPICC_IDENTIFY_PAIN'])[:500]}")
                        if row["MEDDPICC_CHAMPION"]:
                            st.markdown(f"**Champion:** {str(row['MEDDPICC_CHAMPION'])[:500]}")
                        if row["MEDDPICC_METRICS"]:
                            st.markdown(f"**Metrics:** {str(row['MEDDPICC_METRICS'])[:500]}")
                else:
                    st.info("No MEDDPICC data recorded", icon=":material/info:")

            st.divider()

            st.markdown("##### :material/record_voice_over: Recent Meetings (Gong)")
            cust_meetings = pd.DataFrame()
            if not meetings_all_df.empty and sfdc_account_id:
                cust_meetings = meetings_all_df[meetings_all_df["SALESFORCE_ACCOUNT_ID"] == sfdc_account_id]

            if not cust_meetings.empty:
                for idx, (_, mtg) in enumerate(cust_meetings.head(3).iterrows()):
                    meeting_date = str(mtg["MEETING_DATE"])[:16] if mtg["MEETING_DATE"] else "N/A"
                    duration = mtg["DURATION_DISPLAY"] or "N/A"
                    with st.expander(
                        f":material/videocam: **{mtg['MEETING_TITLE']}** — {meeting_date} ({duration})",
                        expanded=(idx == 0)
                    ):
                        if mtg["PARTICIPANTS_EMAILS"]:
                            st.caption(f":material/group: {str(mtg['PARTICIPANTS_EMAILS'])[:200]}")
                        brief = strip_html(mtg.get("CALL_BRIEF"))
                        if brief:
                            st.markdown("**Summary:**")
                            st.write(brief[:2000])
                        key_pts = strip_html(mtg.get("KEY_POINTS"))
                        if key_pts:
                            st.markdown("**Key Points:**")
                            st.write(key_pts[:2000])
                        ns = strip_html(mtg.get("NEXT_STEPS_GONG"))
                        if ns:
                            st.markdown("**Next Steps:**")
                            st.write(ns[:2000])
                        gong_url = None
                        view_html = str(mtg.get("VIEW_CALL_HTML") or "")
                        url_match = re.search(r'href="([^"]+)"', view_html)
                        if url_match:
                            gong_url = url_match.group(1)
                        elif mtg.get("CALL_ID"):
                            gong_url = f"https://app.gong.io/call?id={mtg['CALL_ID']}"
                        if gong_url:
                            st.link_button("Open in Gong", gong_url, icon=":material/play_circle:")
            else:
                st.info("No Gong recordings found for this account in the last 3 months", icon=":material/info:")

            st.divider()

            mtg_col, rec_col = st.columns(2)
            with mtg_col:
                if row["USE_CASE_DESCRIPTION"]:
                    with st.expander(":material/description: **Use Case Description**", expanded=True):
                        st.write(str(row["USE_CASE_DESCRIPTION"])[:3000])

                tech_parts = []
                if row["INCUMBENT_VENDOR"]:
                    tech_parts.append(f"Incumbent: {row['INCUMBENT_VENDOR']}")
                if row["COMPETITORS"]:
                    tech_parts.append(f"Competing: {row['COMPETITORS']}")
                if row["IMPLEMENTER"]:
                    tech_parts.append(f"Implementer: {row['IMPLEMENTER']}")
                if row["PARTNER_NAME"]:
                    tech_parts.append(f"Partner: {row['PARTNER_NAME']}")
                if tech_parts:
                    st.caption(f":material/build: {' | '.join(tech_parts)}")

            with rec_col:
                st.markdown("##### :material/lightbulb: Expansion Recommendations")
                recs = generate_expansion_recs(row, cust_usage, cust_meetings)
                for rec_line in recs:
                    rec_line = rec_line.strip()
                    if rec_line:
                        if rec_line.startswith("Openflow:"):
                            st.markdown(f":material/sync_alt: {rec_line}")
                        elif rec_line.startswith("Iceberg"):
                            st.markdown(f":material/ac_unit: {rec_line}")
                        elif rec_line.startswith("Snowpipe") or rec_line.startswith("SSV2"):
                            st.markdown(f":material/stream: {rec_line}")
                        elif rec_line.startswith("Cortex"):
                            st.markdown(f":material/psychology: {rec_line}")
                        elif rec_line.startswith("Dynamic"):
                            st.markdown(f":material/autorenew: {rec_line}")
                        elif rec_line.startswith("Snowpark"):
                            st.markdown(f":material/code: {rec_line}")
                        elif rec_line.startswith("Streamlit"):
                            st.markdown(f":material/dashboard: {rec_line}")
                        else:
                            st.markdown(f":material/trending_up: {rec_line}")
