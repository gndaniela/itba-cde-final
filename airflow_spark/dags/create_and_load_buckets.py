import logging
import os

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s - %(message)s", level=logging.INFO
)


def create_new_bucket(bucket_name):
    # Connect to S3 as Boto3User
    s3_client = boto3.client("s3")
    s3_resource = boto3.resource("s3")
    # Create bucket for raw files
    if s3_resource.Bucket(bucket_name).creation_date is None:
        s3_client.create_bucket(Bucket=bucket_name)
        logging.info(f"New bucket created: {bucket_name}")
    else:
        print("Bucket already exists")
        pass


def upload_directory_files(path, bucket_name):
    s3_client = boto3.client("s3")
    """Uploads a directory of raw CSV files to AWS S3"""
    print(f"Starting upload for this directory:'{path}'")
    for root, dirs, files in os.walk(path):
        for file in files:
            try:
                key = file
                s3_client.upload_file(os.path.join(root, file), bucket_name, key)
                print(f"File '{key}' uploaded to bucket '{bucket_name}'")
            except ClientError as e:
                logging.error(e)


def main():
    # create initial buckets
    # RAW KAGGLE FILES
    create_new_bucket("itba-tp-01-raw-csv")
    # CONVERTED PARQUET FILES
    create_new_bucket("itba-tp-02-parquet")
    # MODEL FILE OUTPUT
    create_new_bucket("itba-tp-03-model")
    # SPARK SCRIPTS
    create_new_bucket("itba-tp-04-scripts")
    # EMR BOOTSTRAP SCRIPT
    create_new_bucket("itba-tp-05-bootstrap")
    # EMR LOGS
    create_new_bucket("itba-tp-06-emr-logs")

    # root folder of the current file
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    path_raw = f"{dir_path}/dags/data"
    path_scripts = f"{dir_path}/dags/spark-scripts"
    path_bootstrap = f"{dir_path}/dags/bootstrap"
    upload_directory_files(path_raw, "itba-tp-01-raw-csv")
    upload_directory_files(path_scripts, "itba-tp-04-scripts")
    upload_directory_files(path_bootstrap, "itba-tp-05-bootstrap")


if __name__ == "__main__":
    main()
