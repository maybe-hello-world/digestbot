FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

COPY common/requirements.txt /tmp/common_requirements.txt
RUN pip install -r /tmp/common_requirements.txt --no-cache-dir
COPY ./common /app/common

COPY dbservice/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir
COPY ./dbservice/prestart.sh /app/prestart.sh
COPY ./dbservice /app/app
COPY ./dbservice/gunicorn.conf.py /gunicorn_conf.py


ENV PYTHONPATH /app:/app/app:$PYTHONPATH