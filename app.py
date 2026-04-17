import streamlit as st
import pandas as pd
import os
import time

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Patient Monitor", layout="wide")

status_file = r"E:\projects\Patient Vitals Data Pipeline\data\processed\patient_status.csv"
alert_file = r"E:\projects\Patient Vitals Data Pipeline\data\processed\critical_alerts.csv"

# -------------------------------
# HOSPITAL UI STYLING
# -------------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.metric-card {
    background-color: #1c1f26;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
.critical {
    color: #ff4b4b;
    font-weight: bold;
}
.warning {
    color: #ffa500;
    font-weight: bold;
}
.normal {
    color: #00c853;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("Patient Vitals Monitoring System")

# -------------------------------
# LOAD DATA
# -------------------------------
if not os.path.exists(status_file):
    st.error("Run processing script first")
    st.stop()

df = pd.read_csv(status_file, on_bad_lines="skip")

if df.empty:
    st.warning("No data available")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])

latest_df = df.sort_values("timestamp").groupby("patient_id", as_index=False).last()

# -------------------------------
# METRICS PANEL
# -------------------------------
total = len(latest_df)
warning = (latest_df["status"] == "Warning").sum()
critical = (latest_df["status"] == "Critical").sum()

col1, col2, col3 = st.columns(3)

col1.markdown(f"<div class='metric-card'>Total Patients<br><h2>{total}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-card warning'>Warning Cases<br><h2>{warning}</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-card critical'>Critical Cases<br><h2>{critical}</h2></div>", unsafe_allow_html=True)


# -------------------------------
# ALERT HISTORY
# -------------------------------
st.subheader("Alert History")

if os.path.exists(alert_file):
    alert_df = pd.read_csv(alert_file, on_bad_lines="skip").tail(20)
    st.dataframe(alert_df, use_container_width=True)
else:
    st.write("No alerts yet")


# -------------------------------
# PATIENT SELECTOR
# -------------------------------
st.subheader("Patient Selection")

patient_ids = sorted(df["patient_id"].unique())
selected_patient = st.selectbox("Select Patient", patient_ids)

patient_data = df[df["patient_id"] == selected_patient].copy()
patient_data = patient_data.sort_values("timestamp").tail(100)

# -------------------------------
# CURRENT STATUS
# -------------------------------
current = latest_df[latest_df["patient_id"] == selected_patient].iloc[0]

status = current["status"]

if status == "Critical":
    st.markdown(f"<h2 class='critical'>Patient {selected_patient} - CRITICAL</h2>", unsafe_allow_html=True)
elif status == "Warning":
    st.markdown(f"<h2 class='warning'>Patient {selected_patient} - WARNING</h2>", unsafe_allow_html=True)
else:
    st.markdown(f"<h2 class='normal'>Patient {selected_patient} - NORMAL</h2>", unsafe_allow_html=True)

st.write("Anomaly:", current.get("anomaly_flag", "Normal"))

# -------------------------------
# BASELINE vs CURRENT
# -------------------------------
st.subheader("Clinical Insight")

current_hr = patient_data["heart_rate"].iloc[-1]
baseline_hr = patient_data["heart_rate"].mean()

current_spo2 = patient_data["spo2"].iloc[-1]
baseline_spo2 = patient_data["spo2"].mean()

col1, col2 = st.columns(2)

with col1:
    st.write("Heart Rate Baseline:", round(baseline_hr, 2))
    st.write("Heart Rate Current:", round(current_hr, 2))
    st.write("Deviation:", round(current_hr - baseline_hr, 2))

with col2:
    st.write("SpO2 Baseline:", round(baseline_spo2, 2))
    st.write("SpO2 Current:", round(current_spo2, 2))
    st.write("Deviation:", round(current_spo2 - baseline_spo2, 2))

# -------------------------------
# STABILITY INDICATOR
# -------------------------------
st.subheader("Patient Stability")

hr_std = patient_data["heart_rate"].std()

if hr_std < 5:
    st.write("Stability: Stable")
elif hr_std < 10:
    st.write("Stability: Moderate Variation")
else:
    st.write("Stability: Unstable")


# -------------------------------
# VITALS MONITOR PANEL
# -------------------------------
st.subheader("Live Vitals Monitor")

col1, col2 = st.columns(2)

with col1:
    st.markdown("Heart Rate")
    patient_data["hr_ma"] = patient_data["heart_rate"].rolling(5).mean()

    st.line_chart(
        patient_data.set_index("timestamp")[["heart_rate", "hr_ma"]]
    )

    st.markdown("Oxygen Saturation")
    st.line_chart(patient_data.set_index("timestamp")["spo2"])

with col2:
    st.markdown("Temperature")
    st.line_chart(patient_data.set_index("timestamp")["temp"])

    st.markdown("Respiratory Rate")
    st.line_chart(patient_data.set_index("timestamp")["resp_rate"])

st.markdown("Blood Pressure")
st.line_chart(patient_data.set_index("timestamp")[["bp_sys", "bp_dia"]])

# -------------------------------
# EXPORT DATA
# -------------------------------
st.subheader("Export Patient Data")

csv = patient_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Patient Data",
    data=csv,
    file_name=f"{selected_patient}_data.csv",
    mime="text/csv"
)

# -------------------------------
# AUTO REFRESH
# -------------------------------
time.sleep(3)
st.rerun()