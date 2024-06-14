import pandas as pd
import pyarrow as pa
from io import StringIO
import os
import boto3
import re


def convert_csv_to_parquet(s3, csv_key):
    """
    Downloads a CSV file from S3, converts it to Parquet, and uploads the Parquet file.

    Args:
      csv_key: S3 key of the CSV file
    """

    s3 = boto3.client('s3')
    bucket = 'capstone-bucket-4-friends'
    parquet_key = csv_key.replace(".csv", ".parquet")
    file_path = f"./data/{csv_key}"
    parquet_file_path = f"./data/{parquet_key}"

    s3.download_file(bucket, csv_key, file_path)
    df = pd.read_csv(file_path)

    # if csv_key.startswith("crsp"):
    #     keep = ["date", "PERMNO", "TICKER", "COMNAM", "NAICS", "PRIMEXCH", "TRDSTAT", "PRC", "VOL", "NUMTRD", "RET", "SHROUT", "NMSIND"]
    #     df = df[keep]

    # Convert DataFrame to Parquet
    table = pa.Table.from_pandas(df)
    with pa.OSFile(parquet_file_path, 'wb') as sink:
        with pa.RecordBatchFileWriter(sink, table.schema) as writer:
            writer.write_table(table)

    # Upload Parquet file to S3
    s3.upload_file(parquet_file_path, bucket, parquet_key)
    s3.delete_object(Bucket=bucket, Key=csv_key)

    # Specify the path of the file you want to delete
    try:
        # Attempt to delete the file
        os.remove(file_path)
        print(f"File '{file_path}' successfully deleted.")
    except OSError as e:
        print(f"Error deleting the file '{file_path}': {e.strerror}")