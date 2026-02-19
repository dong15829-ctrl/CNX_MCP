#!/bin/bash
export AIRFLOW_HOME=~/DI/DI_NAVER/airflow
export PATH=~/DI/DI_NAVER/venv/bin:$PATH

# Start Scheduler in background
./venv/bin/airflow scheduler &
echo "Scheduler started with PID $!"

# Start Webserver
./venv/bin/airflow webserver -p 8082
