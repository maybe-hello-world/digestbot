FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

COPY dbservice/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./common /app/common
COPY ./dbservice /app/app
ENV PYTHONPATH /app:/app/app:$PYTHONPATH