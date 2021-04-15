FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

COPY common/requirements.txt /tmp/common_requirements.txt
RUN pip install -r /tmp/common_requirements.txt --no-cache-dir
COPY ./common /app/common

COPY uiservice/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir
COPY ./uiservice /app/app
COPY ./uiservice/prestart.sh /app/prestart.sh

ENV PYTHONPATH /app:/app/app:$PYTHONPATH