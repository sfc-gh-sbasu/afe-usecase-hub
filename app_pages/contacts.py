import streamlit as st
import pandas as pd

run_query = st.session_state.run_query
filter_sql = st.session_state.get("filter_sql", "1=1")

st.title(":material/group: Contacts")
st.caption("AE, SE, and team members per use case — sourced from SFDC team assignments")

@st.cache_data(ttl=300)
def load_contacts(_filter):
    return run_query(f"""
        SELECT
            USE_CASE_ID, ACCOUNT_NAME,
            USE_CASE_LEAD_SE_NAME, OWNER_NAME,
            USE_CASE_TEAM_NAME_LIST, USE_CASE_TEAM_ROLE_LIST,
            USE_CASE_NAME, USE_CASE_STAGE
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY ACCOUNT_NAME
    """)

df = load_contacts(filter_sql)

@st.cache_data(ttl=300)
def load_flattened_team(_filter):
    return run_query(f"""
        SELECT
            d.USE_CASE_ID,
            d.ACCOUNT_NAME,
            n.VALUE::STRING AS CONTACT_NAME,
            CASE
                WHEN n.VALUE::STRING = d.OWNER_NAME THEN 'Use Case Owner'
                WHEN n.VALUE::STRING = d.USE_CASE_LEAD_SE_NAME THEN 'Solution Engineer'
                WHEN ARRAY_CONTAINS(n.VALUE, d.USE_CASE_TEAM_ACCOUNT_SE_WORKLOAD_FCTO_LIST) THEN 'SE - Workload FCTO'
                WHEN ARRAY_CONTAINS(n.VALUE, d.USE_CASE_TEAM_PLATFORM_SPECIALIST_LIST) THEN 'Platform Specialist'
                WHEN n.INDEX < ARRAY_SIZE(d.USE_CASE_TEAM_ROLE_LIST)
                     THEN COALESCE(d.USE_CASE_TEAM_ROLE_LIST[n.INDEX]::STRING, 'Team Member')
                ELSE 'Team Member'
            END AS CONTACT_ROLE
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE d,
             LATERAL FLATTEN(INPUT => d.USE_CASE_TEAM_NAME_LIST) n
        WHERE ({_filter})
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY d.ACCOUNT_NAME, CONTACT_ROLE
    """)

try:
    team_df = load_flattened_team(filter_sql)
except Exception:
    team_df = pd.DataFrame()

total_contacts = len(team_df) if not team_df.empty else 0
unique_people = team_df["CONTACT_NAME"].nunique() if not team_df.empty else 0
accounts = df["ACCOUNT_NAME"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Accounts", accounts)
col2.metric("Total team assignments", total_contacts)
col3.metric("Unique people", unique_people)

st.divider()

fc1, fc2 = st.columns([3, 2])
search = fc1.text_input(":material/search: Search", placeholder="Name, role, customer...", key="ct_search")
sort_col = fc2.selectbox("Sort by", ["Customer", "Lead SE", "AE"], key="ct_sort")

customers = sorted(df["ACCOUNT_NAME"].dropna().unique())

for customer in customers:
    if search and search.lower() not in customer.lower():
        cust_team = team_df[team_df["ACCOUNT_NAME"] == customer] if not team_df.empty else pd.DataFrame()
        if cust_team.empty or not cust_team.apply(
            lambda r: search.lower() in " ".join(str(v) for v in r.values if v is not None).lower(), axis=1
        ).any():
            cust_df = df[df["ACCOUNT_NAME"] == customer]
            if not cust_df.apply(
                lambda r: search.lower() in " ".join(str(v) for v in [r.get("USE_CASE_LEAD_SE_NAME"), r.get("OWNER_NAME")] if v is not None).lower(), axis=1
            ).any():
                continue

    cust_df = df[df["ACCOUNT_NAME"] == customer]
    cust_team = team_df[team_df["ACCOUNT_NAME"] == customer] if not team_df.empty else pd.DataFrame()

    with st.container(border=True):
        st.subheader(customer)

        c1, c2 = st.columns(2)
        with c1:
            st.caption(":material/badge: **Key Assignments (SFDC)**")
            lead_ses = cust_df["USE_CASE_LEAD_SE_NAME"].dropna().unique()
            owners = cust_df["OWNER_NAME"].dropna().unique()
            for se in lead_ses:
                st.write(f":material/engineering: **{se}** — Lead SE")
            for ae in owners:
                st.write(f":material/sell: **{ae}** — Account Executive")
            if len(lead_ses) == 0 and len(owners) == 0:
                st.write("No key assignments recorded")

        with c2:
            st.caption(":material/groups: **Use Case Team Members**")
            if not cust_team.empty:
                seen = set()
                for _, r in cust_team.iterrows():
                    key = (r["CONTACT_NAME"], r["CONTACT_ROLE"])
                    if key not in seen:
                        seen.add(key)
                        role = r["CONTACT_ROLE"] or "Team Member"
                        role_icon = ":material/engineering:" if "engineer" in role.lower() or "specialist" in role.lower() else ":material/sell:" if "executive" in role.lower() or "sales" in role.lower() else ":material/person:"
                        st.write(f"{role_icon} **{r['CONTACT_NAME']}** — {role}")
            else:
                st.write("No team members listed")
