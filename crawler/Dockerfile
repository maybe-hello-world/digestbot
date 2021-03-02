FROM python:3.9.1-slim-buster

COPY common/requirements.txt /tmp/common_requirements.txt
COPY crawler/requirements.txt /tmp/requirements.txt

# create env
RUN pip install -r /tmp/common_requirements.txt
RUN pip install -r /tmp/requirements.txt

# copy the bot
COPY ./common /app/common
COPY ./crawler /app/crawler
ENV PYTHONPATH /app:$PYTHONPATH

CMD ["python", "/app/crawler/main.py"]