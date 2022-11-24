import json
import boto3
import logging
import os
import datetime
from datetime import timedelta
import urllib3

DAG_ID = os.environ["DAG_ID"]  #'spark_submit_airflow'
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()

# setup logging to stdout, or just use print()
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger().setLevel(logging.getLevelName(LOG_LEVEL))

ex_date = datetime.datetime.now() + timedelta(days=-1)
ex_date = ex_date.strftime("%Y-%m-%dT%H:%M:%S%zZ")


def lambda_handler(event, context):
    print("Getting Airflow instance private IP...")

    ec2 = boto3.client("ec2")
    filters = [{"Name": "tag:Name", "Values": ["NewInstance"]}]
    reservations = ec2.describe_instances(Filters=filters)

    private_ip = reservations["Reservations"][0]["Instances"][0]["PrivateIpAddress"]

    # TODO implement
    print(private_ip)

    print("Sending Airflow API a request to run the dag")
    http = urllib3.PoolManager()

    headers = {"Content-Type": "application/json"}

    headers.update(urllib3.make_headers(basic_auth="airflow:airflow"))

    logging.info(f"Triggering Airflow DAG {DAG_ID}")

    url = f"http://{private_ip}:8080/api/v1/dags/{DAG_ID}/dagRuns"
    payload = json.dumps(
        {
            "dag_run_id": "lambda_run_" + datetime.datetime.utcnow().isoformat(),
            "execution_date": ex_date,
            "conf": {},
        }
    )

    response = http.request(
        "POST", url=url, body=payload, headers=headers, retries=False
    )

    print(f"Response status: {response.status}")

    data = json.loads(response.data)

    print(f"Response details: {data}")
