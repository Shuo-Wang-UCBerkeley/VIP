import os
from pathlib import Path

import boto3
import pandas as pd

s3 = boto3.client("s3")
bucket = "capstone-bucket-4-friends"
current_dir = Path(__file__).parent.resolve()
data_dir = current_dir.joinpath("../../../data").resolve()


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


def s3_download(s3_path) -> str:
    """
    download from s3 into the data folder.

    Returns:
        the target file path in local folder
    """
    # print(data_dir)
    file_name = s3_path.split("/")[1]
    # print(file_name)
    target_path = data_dir.joinpath(file_name).absolute()
    # print(target_path)
    s3.download_file(bucket, s3_path, target_path)

    return str(target_path)


def s3_upload(s3_path, file_path=None):
    """
    upload from data folder into the s3 path

    Returns:
        the target file path in local folder
    """
    if file_path is None:
        file_name = s3_path.split("/")[1]
        file_path = data_dir.joinpath(file_name).absolute()

    s3.upload_file(file_path, bucket, s3_path)
