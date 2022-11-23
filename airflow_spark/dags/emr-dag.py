from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.S3_hook import S3Hook
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.emr_create_job_flow_operator import (
    EmrCreateJobFlowOperator,
)
from airflow.contrib.operators.emr_add_steps_operator import EmrAddStepsOperator
from airflow.contrib.sensors.emr_step_sensor import EmrStepSensor
from airflow.contrib.operators.emr_terminate_job_flow_operator import (
    EmrTerminateJobFlowOperator,
)

from airflow.providers.docker.operators.docker import DockerOperator
from create_and_load_buckets import main

# Configurations
SCRIPTS_BUCKET_NAME = "itba-tp-04-scripts"
PARQUETS_BUCKET_NAME = "itba-tp-02-parquet"  
MODEL_BUCKET_NAME = "itba-tp-03-model" 
s3_script_convert = "convert_csv_to_parquet.py"
s3_script_model = "model_script.py"

SPARK_STEPS = [
    {
        "Name": "Convert CSVs to Parquet",
        "ActionOnFailure": "CANCEL_AND_WAIT",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                "spark-submit",
                "--deploy-mode",
                "client",
                "s3://{{ params.SCRIPTS_BUCKET_NAME }}/{{ params.s3_script_convert }}",
            ],
        },
    },
    {
        "Name": "Run predictions model",
        "ActionOnFailure": "CANCEL_AND_WAIT",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                "spark-submit",
                "--deploy-mode",
                "client",
                "s3://{{ params.SCRIPTS_BUCKET_NAME }}/{{ params.s3_script_model }}",
            ],
        },
    },
]

JOB_FLOW_OVERRIDES = {
    "Name": "Match Predictions",
    "ReleaseLabel": "emr-6.6.0",
    "Applications": [{"Name": "Hadoop"}, {"Name": "Spark"}, {"Name": "Livy"}],
    "Configurations": [
        {
            "Classification": "spark-env",
            "Configurations": [
                {
                    "Classification": "export",
                    "Properties": {"PYSPARK_PYTHON": "/usr/bin/python3"},
                }
            ],
        }
    ],
    "BootstrapActions": [ 
      { 
         "Name": "Add custom libraries",
         "ScriptBootstrapAction": { 
            "Path": "s3://itba-tp-05-bootstrap/bootstrap_script.sh"
         }
      }
   ],
    "Instances": {
        "InstanceGroups": [
            {
                "Name": "Master node",
                "Market": "SPOT",
                "InstanceRole": "MASTER",
                "InstanceType": "m4.large",
                "InstanceCount": 1,
            },
            {
                "Name": "Core - 2",
                "Market": "SPOT",
                "InstanceRole": "CORE",
                "InstanceType": "m4.large",
                "InstanceCount": 2,
            },
        ],
        "KeepJobFlowAliveWhenNoSteps": True,
        "TerminationProtected": False,
    },
    "JobFlowRole": "EMR_EC2_DefaultRole",
    "ServiceRole": "EMR_DefaultRole",
    "LogUri": "s3://itba-tp-06-emr-logs/logs",
}

default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "wait_for_downstream": True,
    "start_date": datetime(2022, 11, 9),
    "email": ["airflow@airflow.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "spark_submit_airflow",
    default_args=default_args,
    description="Load and transform with Airflow and AWS EMR-Spark",
    schedule_interval=None,
    max_active_runs=1,
)

start_data_pipeline = DummyOperator(task_id="start_data_pipeline", dag=dag)

#Create buckets and copy files
create_buckets_and_files = PythonOperator(
    dag=dag,
    task_id="create_buckets_and_files",
    python_callable=main,
)

# Create an EMR cluster
create_emr_cluster = EmrCreateJobFlowOperator(
    task_id="create_emr_cluster",
    job_flow_overrides=JOB_FLOW_OVERRIDES,
    aws_conn_id="aws_default",
    emr_conn_id="emr_default",
    dag=dag,
)

# Add your steps to the EMR cluster
step_adder = EmrAddStepsOperator(
    task_id="add_steps",
    job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
    aws_conn_id="aws_default",
    steps=SPARK_STEPS,
    params={
            "SCRIPTS_BUCKET_NAME": SCRIPTS_BUCKET_NAME,
            "PARQUETS_BUCKET_NAME": PARQUETS_BUCKET_NAME,
            "MODEL_BUCKET_NAME": MODEL_BUCKET_NAME,
            "s3_script_convert": s3_script_convert,
            "s3_script_model": s3_script_model,
    },
    dag=dag,
)

last_step = len(SPARK_STEPS) - 1
# wait for the steps to complete
step_checker = EmrStepSensor(
    task_id="watch_step",
    job_flow_id="{{ task_instance.xcom_pull('create_emr_cluster', key='return_value') }}",
    step_id="{{ task_instance.xcom_pull(task_ids='add_steps', key='return_value')["
    + str(last_step)
    + "] }}",
    aws_conn_id="aws_default",
    dag=dag,
)

# Terminate the EMR cluster
terminate_emr_cluster = EmrTerminateJobFlowOperator(
    task_id="terminate_emr_cluster",
    job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
    aws_conn_id="aws_default",
    dag=dag,
)

# # Run Flask app
# run_flask_app = DockerOperator(
#         task_id='run_flask_app',
#         image='flask-image',
#         api_version='auto',
#         auto_remove=False,
#         mount_tmp_dir=False,
#         container_name='flask-container',
#         command='echo "Message from Flask"',
#         docker_url='unix://var/run/docker.sock',
#         network_mode='bridge',
#         dag=dag
# )

end_data_pipeline = DummyOperator(task_id="end_data_pipeline", dag=dag)

start_data_pipeline >> create_buckets_and_files >> create_emr_cluster
create_emr_cluster >> step_adder >> step_checker >> terminate_emr_cluster
terminate_emr_cluster >> end_data_pipeline