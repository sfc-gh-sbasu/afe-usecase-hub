import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="DE Field Use Case Intelligence Hub", layout="wide", page_icon=":material/hub:")

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
def resolve_current_user():
    df = run_query("""
        SELECT e.PREFERRED_FULL_NAME
        FROM MDM.MDM_INTERFACES.DIM_EMPLOYEE e
        WHERE UPPER(e.SNOWHOUSE_LOGIN_NAME) = CURRENT_USER()
          AND e.IS_ACTIVE = TRUE
        LIMIT 1
    """)
    if df.empty:
        return None
    return df.iloc[0, 0]


@st.cache_data(ttl=600)
def resolve_user_role(full_name):
    safe = full_name.replace("'", "''")
    df = run_query(f"""
        SELECT
            COUNT(CASE WHEN ARRAY_CONTAINS('{safe}'::VARIANT, USE_CASE_TEAM_NAME_LIST) THEN 1 END) as IC_COUNT,
            COUNT(CASE WHEN ACCOUNT_SE_MANAGER = '{safe}' THEN 1 END) as MGR_COUNT,
            COUNT(CASE WHEN ACCOUNT_SE_DIRECTOR = '{safe}' THEN 1 END) as DIR_COUNT,
            COUNT(CASE WHEN ACCOUNT_SE_VP = '{safe}' OR ACCOUNT_GVP = '{safe}' OR ACCOUNT_RVP = '{safe}' THEN 1 END) as VP_COUNT
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
    """)
    if df.empty:
        return "ic"
    row = df.iloc[0]
    if row["VP_COUNT"] > 0:
        return "vp"
    if row["DIR_COUNT"] > 0:
        return "director"
    if row["MGR_COUNT"] > 0:
        return "manager"
    return "ic"


def build_name_filter(full_name):
    safe = full_name.replace("'", "''")
    role = resolve_user_role(full_name)
    if role == "vp":
        return f"(ACCOUNT_SE_VP = '{safe}' OR ACCOUNT_GVP = '{safe}' OR ACCOUNT_RVP = '{safe}' OR ACCOUNT_SE_DIRECTOR = '{safe}' OR ACCOUNT_SE_MANAGER = '{safe}' OR ARRAY_CONTAINS('{safe}'::VARIANT, USE_CASE_TEAM_NAME_LIST))"
    if role == "director":
        return f"(ACCOUNT_SE_DIRECTOR = '{safe}' OR ACCOUNT_SE_MANAGER = '{safe}' OR ARRAY_CONTAINS('{safe}'::VARIANT, USE_CASE_TEAM_NAME_LIST))"
    if role == "manager":
        return f"(ACCOUNT_SE_MANAGER = '{safe}' OR ARRAY_CONTAINS('{safe}'::VARIANT, USE_CASE_TEAM_NAME_LIST))"
    return f"ARRAY_CONTAINS('{safe}'::VARIANT, USE_CASE_TEAM_NAME_LIST)"


@st.cache_data(ttl=600)
def load_my_regions(full_name):
    name_filter = build_name_filter(full_name)
    return run_query(f"""
        SELECT DISTINCT REGION_NAME
        FROM MDM.MDM_INTERFACES.DIM_USE_CASE
        WHERE {name_filter}
          AND USE_CASE_STATUS NOT IN ('Closed - Lost', 'Closed - Archived')
          AND REGION_NAME IS NOT NULL
        ORDER BY 1
    """)


with st.sidebar:
    st.title(":material/hub: DE Field Use Case Intelligence Hub")
    st.caption("Real-time visibility into AFE/PSS use cases, contacts, tech stack, product usage metrics, and opportunities")
    st.divider()

    my_name = resolve_current_user()
    if not my_name:
        st.error("Could not resolve your identity. Ensure your Snowhouse login is mapped in DIM_EMPLOYEE.", icon=":material/error:")
        st.stop()

    user_role = resolve_user_role(my_name)
    role_labels = {"ic": "SE", "manager": "Manager", "director": "Director", "vp": "VP"}
    st.markdown(f":material/person: Logged in as **{my_name}** ({role_labels.get(user_role, 'SE')})")

    filter_mode = st.radio("Filter by", ["My Use Cases", "My Region / Territory"], key="filter_mode", horizontal=True)

    my_name_filter = build_name_filter(my_name)

    if filter_mode == "My Use Cases":
        st.session_state.filter_sql = my_name_filter
        st.success(f"Showing your use cases", icon=":material/person:")
    else:
        try:
            regions_df = load_my_regions(my_name)
            my_regions = regions_df["REGION_NAME"].dropna().tolist()
        except Exception:
            my_regions = []

        if not my_regions:
            st.warning("No regions found for your use cases.", icon=":material/warning:")
            st.session_state.filter_sql = my_name_filter
        else:
            selected_regions = st.multiselect(
                ":material/map: Your Region(s)",
                options=my_regions,
                default=my_regions,
                key="selected_regions",
                placeholder="Select regions..."
            )
            if selected_regions:
                region_list = ",".join([f"'{r}'" for r in selected_regions])
                st.session_state.filter_sql = f"REGION_NAME IN ({region_list})"
                st.success(f"Showing: **{', '.join(selected_regions)}**", icon=":material/map:")
            else:
                st.session_state.filter_sql = None

    st.divider()
    try:
        info_df = run_query("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE()")
        st.caption(f":material/account_circle: {info_df.iloc[0, 0]} | {info_df.iloc[0, 1]}")
    except Exception:
        pass

if not st.session_state.get("filter_sql"):
    st.info("Select a filter from the sidebar to get started.", icon=":material/filter_alt:")
    st.stop()

page.run()
