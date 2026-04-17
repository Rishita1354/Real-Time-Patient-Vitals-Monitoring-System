import pandas as pd
import os

# file path
file_path = r"E:\projects\Patient Vitals Data Pipeline\ICU_Patient_Monitoring_Mortality_Prediction_15000.xlsx"

# load excel
df = pd.read_excel(file_path)
df = df.sample(n=500, random_state=42)

print("Original Shape:", df.shape)
print("Columns:", df.columns.tolist())

#select required columns
selected_cols = [
    "patient_id",
    "heart_rate_mean",
    "heart_rate_std",
    "heart_rate_min",
    "heart_rate_max",
    "systolic_bp_mean",
    "spo2_mean",
    "respiratory_rate_mean",
    "temperature_mean",
    "age",
    "gender",
    "admission_type",
    "comorbidity_score",
    "apache_score",
    "sofa_score",
    "sepsis_flag",
    "mortality_label"
]

# to keep only available columns
selected_cols = [col for col in selected_cols if col in df.columns]

df = df[selected_cols]

# rename
rename_map = {
    "heart_rate_mean": "hr_mean",
    "heart_rate_std": "hr_std",
    "heart_rate_min": "hr_min",
    "heart_rate_max": "hr_max",
    "systolic_bp_mean": "bp_sys_mean",
    "diastolic_bp_mean": "bp_dia_mean",
    "respiratory_rate_mean": "resp_rate_mean",
    "temperature_mean": "temp_mean"
}

df = df.rename(columns=rename_map)

# missing values
# forward fill
df = df.ffill()

# If diastolic BP missing → derive
if "bp_dia_mean" not in df.columns and "bp_sys_mean" in df.columns:
    df["bp_dia_mean"] = df["bp_sys_mean"] * 0.66

# if std missing estimate
if "hr_std" not in df.columns and "hr_mean" in df.columns:
    df["hr_std"] = df["hr_mean"] * 0.1
# create sample id if missing
if "patient_id" not in df.columns:
    df["patient_id"] = ["P" + str(i).zfill(5) for i in range(len(df))]

# save output
output_path = r"E:\projects\Patient Vitals Data Pipeline\data\profiles\patient_profiles.csv"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df.to_csv(output_path, index=False)

print("/nProfiles Created Successfully")
print("Final Shape:", df.shape)
print("Saved at:", output_path)