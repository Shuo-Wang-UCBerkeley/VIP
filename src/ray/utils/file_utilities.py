import os

import boto3
import pandas as pd

s3 = boto3.client("s3")
bucket = "capstone-bucket-4-friends"


def convert_csv_to_parquet(csv_key, delete_file=False):
    """
    Downloads a CSV file from S3, converts it to Parquet, and uploads the Parquet file.

    Args:
      csv_key: S3 key of the CSV file
    """

    parquet_key = csv_key.replace(".csv", ".parquet")
    file_path = f"./data/{csv_key}"
    parquet_file_path = f"./data/{parquet_key}"

    s3.download_file(bucket, csv_key, file_path)
    df = pd.read_csv(file_path)

    df.to_parquet(parquet_file_path)

    # Upload Parquet file to S3
    s3.upload_file(parquet_file_path, bucket, parquet_key)

    if delete_file:
        s3.delete_object(Bucket=bucket, Key=csv_key)

        # Specify the path of the file you want to delete
        try:
            # Attempt to delete the file
            os.remove(file_path)
            print(f"File '{file_path}' successfully deleted.")
        except OSError as e:
            print(f"Error deleting the file '{file_path}': {e.strerror}")


def s3_download(s3_path):
    """
    download from s3 into the data folder.

    Returns:
        the target file path in local folder
    """
    file_name = s3_path.split('/')[1]
    # print(file_name)
    target_path = f"../../data/{file_name}"
    # print(target_path)

    s3.download_file(bucket, s3_path, target_path)

    return os.path.abspath(target_path)
