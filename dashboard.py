import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh


st.set_page_config(page_title="System Health Dashboard", layout="wide")

st.title("🖥️ System Health Dashboard")
st.caption("Live status monitoring of critical applications")

# Refresh interval in seconds
REFRESH_INTERVAL = 60

@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_status_data():
    try:
        response = requests.get("https://kreeztoph.pythonanywhere.com/get_statuses")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return {}

# Fetch the data
data = fetch_status_data()
# ---- Auto Refresh every 60 seconds ----
st_autorefresh(interval=60 * 1000 , limit=None, key="data_refresh")
if not data:
    st.warning("No data available.")
else:
    records = []
    now = datetime.now()

    for app_name, details in data.items():
        timestamp_str = details.get("timestamp", "")
        try:
            timestamp = datetime.strptime(timestamp_str, "%d-%m-%Y %H:%M:%S")
        except ValueError:
            timestamp = None

        # Determine if data is stale
        is_stale = timestamp and (now - timestamp > timedelta(minutes=15))
        status = "inactive" if is_stale else details.get("status", "unknown")

        records.append({
            "Application": app_name,
            "Status": status,
            "System Name": details.get("system_name", "N/A"),
            "Timestamp": timestamp_str,
            "User Login": details.get("user_login", "N/A")
        })

    df = pd.DataFrame(records)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d-%m-%Y %H:%M:%S", errors="coerce")
    df = df.sort_values("Timestamp", ascending=False)

    st.markdown(f"**Last updated:** {now.strftime('%d-%m-%Y %H:%M:%S')} (refresh every {REFRESH_INTERVAL}s)")

    # Apply conditional formatting
    def color_status(val):
        if val == "active":
            return "background-color: #d4edda; color: green"
        elif val == "inactive":
            return "background-color: #f8d7da; color: red"
        else:
            return "background-color: #fff3cd; color: #856404"

    styled_df = df.style.map(color_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
