import pandas as pd
import os
from datetime import datetime
from sklearn.ensemble import IsolationForest

raw_file = r"E:\projects\Patient Vitals Data Pipeline\data\raw\live_vitals.csv"

silver_file = r"E:\projects\Patient Vitals Data Pipeline\data\processed\cleaned_vitals.csv"
gold_status_file = r"E:\projects\Patient Vitals Data Pipeline\data\processed\patient_status.csv"
critical_file = r"E:\projects\Patient Vitals Data Pipeline\data\processed\critical_alerts.csv"

os.makedirs(os.path.dirname(silver_file), exist_ok=True)

print("Processing engine started...")

last_processed_size = 0
model = IsolationForest(contamination=0.02, random_state=42)


# status logic
def get_status(row):
    if row["heart_rate"] > 140 or row["heart_rate"] < 40:
        return "Critical"
    if row["spo2"] < 88:
        return "Critical"
    if row["temp"] > 39.5:
        return "Critical"

    if row["heart_rate"] > 110 or row["spo2"] < 94:
        return "Warning"

    return "Normal"


# live processing loop
while True:
    if not os.path.exists(raw_file):
        continue

    df = pd.read_csv(raw_file, on_bad_lines="skip")

    if len(df) == last_processed_size:
        continue

    new_data = df.iloc[last_processed_size:]
    last_processed_size = len(df)

    clean_df = new_data.copy().drop_duplicates()

    # anomaly detection
    try:
        features = clean_df[["heart_rate", "spo2", "temp", "resp_rate"]]
        preds = model.fit_predict(features)

        clean_df["anomaly_flag"] = [
            "Anomaly" if p == -1 else "Normal" for p in preds
        ]
    except:
        clean_df["anomaly_flag"] = "Normal"

    # status logic
    clean_df["status"] = clean_df.apply(get_status, axis=1)

    # fix columns order
    columns_order = [
        "timestamp",
        "patient_id",
        "heart_rate",
        "bp_sys",
        "bp_dia",
        "spo2",
        "resp_rate",
        "temp",
        "status",
        "anomaly_flag"
    ]

    for col in columns_order:
        if col not in clean_df.columns:
            clean_df[col] = None

    clean_df = clean_df[columns_order]

    # silver cleaned data
    if not os.path.exists(silver_file):
        clean_df.to_csv(silver_file, index=False)
    else:
        clean_df.to_csv(silver_file, mode="a", header=False, index=False)

    # gold status file
    if not os.path.exists(gold_status_file):
        clean_df.to_csv(gold_status_file, index=False)
    else:
        clean_df.to_csv(gold_status_file, mode="a", header=False, index=False)

    # alert generation
    alerts = clean_df[
        (clean_df["status"] == "Critical") |
        (clean_df["anomaly_flag"] == "Anomaly")
    ]

    if not alerts.empty:
        alerts["alert_type"] = alerts.apply(
            lambda r: "Anomaly" if r["anomaly_flag"] == "Anomaly" else "Critical",
            axis=1
        )

        if not os.path.exists(critical_file):
            alerts.to_csv(critical_file, index=False)
        else:
            alerts.to_csv(critical_file, mode="a", header=False, index=False)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Alerts: {len(alerts)}")