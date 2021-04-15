FROM python:3.9.1-slim-buster

# copy common libs and reqs
COPY common/requirements.txt /tmp/common_requirements.txt
RUN pip install -r /tmp/common_requirements.txt --no-cache-dir
COPY ./common /app/common

# copy needed libs and reqs
COPY crawler/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir
COPY ./crawler /app/crawler

ENV PYTHONPATH /app:$PYTHONPATH

CMD ["python", "/app/crawler/main.py"]