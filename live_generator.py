import pandas as pd
import numpy as np
import time
import os
from datetime import datetime

profiles_path = r"E:\projects\Patient Vitals Data Pipeline\data\profiles\patient_profiles.csv"
df = pd.read_csv(profiles_path)

print("Loaded patients:", len(df))


# configure stream parameters
BATCH_SIZE = 200   # number of patients per cycle
SLEEP_TIME = 2   # seconds between updates

output_file = r"E:\projects\Patient Vitals Data Pipeline\data\raw\live_vitals.csv"
os.makedirs(os.path.dirname(output_file), exist_ok=True)


# initialize patient states from profiles
patient_states = {}

for _, row in df.iterrows():
    patient_states[row["patient_id"]] = {
        "heart_rate": row["hr_mean"],
        "bp_sys": row["bp_sys_mean"],
        "bp_dia": row["bp_dia_mean"],
        "spo2": row["spo2_mean"],
        "resp_rate": row["resp_rate_mean"],
        "temp": row["temp_mean"]
    }


# helper function to update vitals with some randomness
def update_value(current, mean, std, min_val, max_val):
    # small smooth variation
    drift = np.random.normal(0, std * 0.1)
    new_val = current + drift

    # pull toward mean (stability)
    new_val += (mean - new_val) * 0.05

    return float(np.clip(new_val, min_val, max_val))


# stream loop
current_index = 0

print("Starting live stream...\n")

while True:
    records = []

    # Select batch
    batch_df = df.iloc[current_index:current_index + BATCH_SIZE]

    if batch_df.empty:
        current_index = 0
        continue

    for _, row in batch_df.iterrows():
        pid = row["patient_id"]
        state = patient_states[pid]

        # vital updates
        state["heart_rate"] = update_value(
            state["heart_rate"],
            row["hr_mean"],
            row["hr_std"],
            row["hr_min"],
            row["hr_max"]
        )

        state["bp_sys"] = update_value(
            state["bp_sys"],
            row["bp_sys_mean"],
            5,
            90,
            180
        )

        state["bp_dia"] = state["bp_sys"] * 0.66

        state["spo2"] = update_value(
            state["spo2"],
            row["spo2_mean"],
            1,
            85,
            100
        )

        state["resp_rate"] = update_value(
            state["resp_rate"],
            row["resp_rate_mean"],
            2,
            10,
            30
        )

        state["temp"] = update_value(
            state["temp"],
            row["temp_mean"],
            0.2,
            35,
            40
        )

        # record for this patient
        record = {
            "timestamp": datetime.now(),
            "patient_id": pid,
            "heart_rate": round(state["heart_rate"], 2),
            "bp_sys": round(state["bp_sys"], 2),
            "bp_dia": round(state["bp_dia"], 2),
            "spo2": round(state["spo2"], 2),
            "resp_rate": round(state["resp_rate"], 2),
            "temp": round(state["temp"], 2)
        }

        records.append(record)

    # save batch to CSV bronze file
    live_df = pd.DataFrame(records)

    if not os.path.exists(output_file):
        live_df.to_csv(output_file, index=False)
    else:
        live_df.to_csv(output_file, mode='a', header=False, index=False)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generated {len(records)} records")

    # Move to next batch
    current_index += BATCH_SIZE

    # Wait before next cycle
    time.sleep(SLEEP_TIME)