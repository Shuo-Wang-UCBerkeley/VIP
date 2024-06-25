"""File to serve as place for functions for cleaning and processing CRSP data."""

import pandas as pd

# Define data types from the Colab notebook
dtype_spec = {
    "PERMNO": "int64",
    "date": "object",
    "NAMEENDT": "object",
    "SHRCD": "float64",
    "EXCHCD": "float64",
    "SICCD": "object",
    "NCUSIP": "object",
    "TICKER": "object",
    "COMNAM": "object",
    "SHRCLS": "object",
    "TSYMBOL": "object",
    "NAICS": "float64",
    "PRIMEXCH": "object",
    "TRDSTAT": "object",
    "SECSTAT": "object",
    "PERMCO": "int64",
    "ISSUNO": "int64",
    "HEXCD": "int64",
    "HSICCD": "object",
    "CUSIP": "object",
    "DCLRDT": "object",
    "DLAMT": "float64",
    "DLPDT": "object",
    "DLSTCD": "float64",
    "NEXTDT": "object",
    "PAYDT": "object",
    "RCRDDT": "object",
    "SHRFLG": "float64",
    "HSICMG": "float64",
    "HSICIG": "float64",
    "DISTCD": "float64",
    "DIVAMT": "float64",
    "FACPR": "float64",
    "FACSHR": "float64",
    "ACPERM": "float64",
    "ACCOMP": "float64",
    "SHRENDDT": "object",
    "NWPERM": "float64",
    "DLRETX": "object",
    "DLPRC": "float64",
    "DLRET": "object",
    "TRTSCD": "float64",
    "NMSIND": "float64",
    "MMCNT": "float64",
    "NSDINX": "float64",
    "BIDLO": "float64",
    "ASKHI": "float64",
    "PRC": "float64",
    "VOL": "float64",
    "RET": "object",
    "BID": "float64",
    "ASK": "float64",
    "SHROUT": "float64",
    "CFACPR": "float64",
    "CFACSHR": "float64",
    "OPENPRC": "float64",
    "NUMTRD": "float64",
    "RETX": "object",
    "vwretd": "float64",
    "vwretx": "float64",
    "ewretd": "float64",
    "ewretx": "float64",
    "sprtrn": "float64",
}

# Columns to keep
columns = [
    "PERMNO",
    "date",
    "SHRCD",
    "EXCHCD",
    "SICCD",
    "NCUSIP",
    "TICKER",
    "COMNAM",
    "TSYMBOL",
    "NAICS",
    "PRIMEXCH",
    "TRDSTAT",
    "SECSTAT",
    "PERMCO",
    "ISSUNO",
    "HEXCD",
    "HSICCD",
    "CUSIP",
    "HSICMG",
    "HSICIG",
    "DLAMT",
    "ACPERM",
    "DLRET",
    "BIDLO",
    "ASKHI",
    "PRC",
    "VOL",
    "RET",
    "BID",
    "ASK",
    "SHROUT",
    "CFACPR",
    "CFACSHR",
    "OPENPRC",
    "NUMTRD",
    "RETX",
    "vwretd",
    "vwretx",
    "ewretd",
    "ewretx",
    "sprtrn",
]


# Functions from EDA
def load_csv(file_path, dtype_spec):
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path, dtype=dtype_spec, low_memory=False)
        return df
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def load_parquet(file_path):
    """Load data from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
        return df
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def clean_data(df):
    """Apply common EDA preprocessing steps."""
    # Convert date columns to datetime
    date_columns = [
        "date",
        "NAMEENDT",
        "DCLRDT",
        "DLPDT",
        "NEXTDT",
        "PAYDT",
        "RCRDDT",
        "SHRENDDT",
    ]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Drop columns with typically more than 80% nulls
    df = df[columns]

    # Fill missing values for numerical columns with 0
    numeric_columns = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)  # not sure if we want to do this

    # Fill missing values for object columns with 'Unknown'
    object_columns = df.select_dtypes(include=["object"]).columns
    df[object_columns] = df[object_columns].fillna("Unknown")

    return df


# Functions from milestone goals


def additional_cleaning(df):
    """Additional cleaning steps."""
    # Keep only securities with more than 128 days of return records
    df = df.groupby("PERMNO").filter(lambda x: len(x) > 128)

    # Remove severe outliers
    df["RET"] = pd.to_numeric(df["RET"], errors="coerce")
    df = df[
        df["RET"].between(df["RET"].quantile(0.01), df["RET"].quantile(0.99))
    ]  # Check with Rachel if this is enough/too much

    # Apply log transformation and normalization to the return
    df["RET"] = np.log1p(df["RET"])
    df["RET"] = (df["RET"] - df["RET"].mean()) / df["RET"].std()

    # Create additional features
    df["market_return"] = df["vwretd"]  # Value-Weighted Return (includes distributions)
    df["industry"] = df["NAICS"].apply(lambda x: str(x)[:2] if pd.notnull(x) else "Unknown")

    return df


# Function that calls all other functions to use
def clean_and_process_data(file_path, file_type="csv"):
    """Load, clean, and process data."""
    if file_type == "csv":
        df = load_csv(file_path, dtype_spec)
    elif file_type == "parquet":
        df = load_parquet(file_path)
    else:
        raise ValueError("Unsupported file type. Use 'csv' or 'parquet'.")

    if df is not None:
        df = clean_data(df)
        df = additional_cleaning(df)
    return df
