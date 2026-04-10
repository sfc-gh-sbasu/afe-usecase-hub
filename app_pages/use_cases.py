import streamlit as st
import pandas as pd

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
    se_comments = row.get("SE_COMMENTS") or ""
    meddpicc_pain = row.get("MEDDPICC_IDENTIFY_PAIN") or ""
    meddpicc_champion = row.get("MEDDPICC_CHAMPION") or ""
    incumbent = row.get("INCUMBENT_VENDOR") or ""
    competitors = row.get("COMPETITORS") or ""
    poc_stage = row.get("POC_STAGE") or ""
    decision_date = row.get("DECISION_DATE")
    go_live = row.get("GO_LIVE_DATE")
    is_lost = bool(row.get("IS_LOST"))
    is_won = bool(row.get("IS_WON"))

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


@st.cache_data(ttl=300)
def load_use_cases(_filter):
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
            REGION_NAME, ACCOUNT_ID
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)


df = load_use_cases(filter_sql)

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
                st.badge("Lost", icon=":material/block:", color="red")
            elif row["IS_WON"]:
                st.badge("Won", icon=":material/celebration:", color="green")
            elif row["IN_POC"]:
                st.badge("POC", icon=":material/science:", color="blue")
            else:
                st.badge("In Pursuit", icon=":material/trending_up:", color="orange")

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
                days = row["DAYS_IN_STAGE"]
                if days is not None:
                    st.markdown(f":material/timer: **Days in Stage:** {int(days)}")
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
            sfdc_url = f"https://snowforce.lightning.force.com/lightning/r/vh__Deliverable__c/{row['USE_CASE_ID']}/view"
            detail_header = st.columns([2, 1, 1])
            with detail_header[0]:
                if row["USE_CASE_DESCRIPTION"]:
                    with st.expander(":material/description: **Use Case Description**", expanded=True):
                        st.write(str(row["USE_CASE_DESCRIPTION"])[:3000])
            with detail_header[1]:
                cloud = row["CLOUD_PROVIDER"] or "Unknown"
                st.caption(f":material/cloud: **Cloud:** {cloud}")
            with detail_header[2]:
                st.link_button("Open in SFDC", sfdc_url, icon=":material/open_in_new:")

            if row["RISK_DESCRIPTION"]:
                st.error(f"**Risk:** {str(row['RISK_DESCRIPTION'])[:500]}", icon=":material/error:")

            sec1, sec2 = st.columns(2)
            with sec1:
                st.markdown("##### :material/edit_note: Comments")
                if row["SE_COMMENTS"]:
                    with st.expander(":material/person: **SE Comments**", expanded=True):
                        st.write(str(row["SE_COMMENTS"])[:3000])
                if row["SPECIALIST_COMMENTS"]:
                    with st.expander(":material/engineering: **Specialist Comments**"):
                        st.write(str(row["SPECIALIST_COMMENTS"])[:3000])
                if row["PARTNER_COMMENTS"]:
                    with st.expander(":material/handshake: **Partner Comments**"):
                        st.write(str(row["PARTNER_COMMENTS"])[:3000])
            with sec2:
                st.markdown("##### :material/psychology: MEDDPICC")
                if row["MEDDPICC_IDENTIFY_PAIN"]:
                    st.markdown(f"**Pain:** {str(row['MEDDPICC_IDENTIFY_PAIN'])[:500]}")
                if row["MEDDPICC_CHAMPION"]:
                    st.markdown(f"**Champion:** {str(row['MEDDPICC_CHAMPION'])[:500]}")
                if row["MEDDPICC_METRICS"]:
                    st.markdown(f"**Metrics:** {str(row['MEDDPICC_METRICS'])[:500]}")
                if not any([row["MEDDPICC_IDENTIFY_PAIN"], row["MEDDPICC_CHAMPION"], row["MEDDPICC_METRICS"]]):
                    st.info("No MEDDPICC data recorded", icon=":material/info:")

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
