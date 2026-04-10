import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="AFE/PSS Use Case Hub", layout="wide", page_icon=":material/hub:")

pages = [
    st.Page("app_pages/use_cases.py", title="Use Cases", icon=":material/work:"),
    st.Page("app_pages/tech_stack.py", title="Tech Stack", icon=":material/layers:"),
    st.Page("app_pages/contacts.py", title="Contacts", icon=":material/group:"),
    st.Page("app_pages/opportunities.py", title="Opportunities", icon=":material/lightbulb:"),
]

page = st.navigation(pages)

SNOWHOUSE_CONN = os.getenv("SNOWHOUSE_CONNECTION_NAME") or "snowhouse"

def get_connection():
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        st.session_state._conn_mode = "sis"
        return session
    except Exception:
        pass

    import snowflake.connector
    if "sh_conn" not in st.session_state:
        st.session_state.sh_conn = snowflake.connector.connect(connection_name=SNOWHOUSE_CONN)
        st.session_state._conn_mode = "local"
    return st.session_state.sh_conn

def run_query(sql):
    conn = get_connection()
    if st.session_state.get("_conn_mode") == "sis":
        return conn.sql(sql).to_pandas()
    else:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)

st.session_state.run_query = run_query

@st.cache_data(ttl=600)
def load_regions():
    return run_query("""
        SELECT DISTINCT REGION_NAME
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE REGION_NAME IS NOT NULL
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
        ORDER BY 1
    """)

@st.cache_data(ttl=600)
def load_team_members():
    return run_query("""
        SELECT DISTINCT f.VALUE::STRING as TEAM_MEMBER_NAME
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE,
             LATERAL FLATTEN(INPUT => USE_CASE_TEAM_NAME_LIST) f
        WHERE USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
          AND f.VALUE::STRING IS NOT NULL
        ORDER BY 1
    """)

with st.sidebar:
    st.title(":material/hub: Use Case Hub")
    st.caption("AFE / PSS Customer Intelligence")
    st.divider()

    filter_mode = st.radio("Filter by", ["My Name", "Region / Territory"], key="filter_mode", horizontal=True)

    if filter_mode == "My Name":
        try:
            members_df = load_team_members()
            all_names = members_df["TEAM_MEMBER_NAME"].dropna().tolist()
        except Exception:
            all_names = []

        selected_name = st.selectbox(
            ":material/person: Your name",
            options=[""] + all_names,
            index=0,
            key="selected_name",
            placeholder="Start typing your name..."
        )
        st.session_state.filter_sql = None
        if selected_name:
            safe_name = selected_name.replace("'", "''")
            st.session_state.filter_sql = f"""
                ARRAY_CONTAINS('{safe_name}'::VARIANT, USE_CASE_TEAM_NAME_LIST)
            """
            st.success(f"Showing use cases for **{selected_name}**", icon=":material/person:")
    else:
        try:
            regions_df = load_regions()
            all_regions = regions_df["REGION_NAME"].dropna().tolist()
        except Exception:
            all_regions = []

        selected_regions = st.multiselect(
            ":material/map: Region(s)",
            options=all_regions,
            key="selected_regions",
            placeholder="Select regions..."
        )
        st.session_state.filter_sql = None
        if selected_regions:
            region_list = ",".join([f"'{r}'" for r in selected_regions])
            st.session_state.filter_sql = f"REGION_NAME IN ({region_list})"
            st.success(f"Showing: **{', '.join(selected_regions)}**", icon=":material/map:")

    st.divider()
    try:
        info_df = run_query("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE()")
        st.caption(f":material/account_circle: {info_df.iloc[0, 0]} | {info_df.iloc[0, 1]}")
    except Exception:
        pass

if not st.session_state.get("filter_sql"):
    st.info("Select your name or a region from the sidebar to get started.", icon=":material/filter_alt:")
    st.stop()

page.run()
