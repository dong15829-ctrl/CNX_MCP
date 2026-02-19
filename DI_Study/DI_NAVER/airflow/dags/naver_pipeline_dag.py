from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os
from datetime import timedelta

# Add project root to sys.path so we can import modules
PROJECT_ROOT = "/home/ubuntu/DI/DI_NAVER"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from main import main as run_pipeline

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'naver_api_pipeline',
    default_args=default_args,
    description='A simple DAG to run Naver API Pipeline',
    schedule_interval='*/5 * * * *', # Every 5 minutes
    start_date=days_ago(1),
    catchup=False,
    tags=['naver', 'api'],
) as dag:

    def pipeline_task():
        # Change CWD to project root so .env and DB are found
        os.chdir(PROJECT_ROOT)
        run_pipeline()

    t1 = PythonOperator(
        task_id='run_naver_pipeline',
        python_callable=pipeline_task,
    )

    t1
