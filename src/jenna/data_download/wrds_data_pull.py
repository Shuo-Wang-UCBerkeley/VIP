import wrds
import pandas as pd
from datetime import datetime

# Connect to WRDS
db = wrds.Connection()

# Set date range
start_date = "2018-01-01"
end_date = "2023-12-31"

# CRSP Daily Stock Data
crsp_query = f"""
    SELECT a.permno, a.date, a.prc, a.ret, a.shrout, a.vol,
           b.gvkey, b.linktype, b.linkprim
    FROM crsp.dsf a
    LEFT JOIN crsp.ccmxpf_linktable b
    ON a.permno = b.lpermno
    AND b.linktype IN ('LC', 'LU')
    AND b.linkprim IN ('P', 'C')
    AND a.date BETWEEN b.linkdt AND COALESCE(b.linkenddt, '2023-12-31')
    WHERE a.date BETWEEN '{start_date}' AND '{end_date}'
"""
crsp_data = db.raw_sql(crsp_query)

# Compustat Fundamentals Quarterly
compustat_query = f"""
    SELECT gvkey, datadate, fyearq, fqtr, atq, ceqq, dlttq, dlcq, niq
    FROM comp.fundq
    WHERE datadate BETWEEN '{start_date}' AND '{end_date}'
"""
compustat_data = db.raw_sql(compustat_query)

# Convert date columns to datetime
crsp_data["date"] = pd.to_datetime(crsp_data["date"])
compustat_data["datadate"] = pd.to_datetime(compustat_data["datadate"])

# Merge datasets
merged_data = pd.merge(
    crsp_data,
    compustat_data,
    left_on=["gvkey", "date"],
    right_on=["gvkey", "datadate"],
    how="left",
)

# Forward fill Compustat data (optional, fills in missing quarterly data)
merged_data = merged_data.sort_values(["permno", "date"])
fill_columns = ["atq", "ceqq", "dlttq", "dlcq", "niq", "fyearq", "fqtr"]
merged_data[fill_columns] = merged_data.groupby("permno")[fill_columns].ffill()

# Save to CSV
merged_data.to_csv("crsp_compustat_merged_2018_2023.csv", index=False)

# Close the connection
db.close()

print("Data extraction and merging complete. File saved as CSV.")
