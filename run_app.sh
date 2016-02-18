#!/bin/bash
/mycircos/redis-3.0.7/src/redis-server &
cd /u/mycircos/mycircos 
celery -A app.celery_tasks.celery_app worker -C --concurrency=2 &
python run.py
