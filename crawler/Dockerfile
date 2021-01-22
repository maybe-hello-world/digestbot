FROM python:3.9.1-slim-buster

COPY crawler/requirements.txt /tmp/requirements.txt

# create env
RUN apt update \
    && apt install -y gcc \
    && pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && apt remove -y gcc \
    && apt autoremove -y \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/*

# copy the bot
COPY ./common /app/common
COPY ./crawler /app/crawler
ENV PYTHONPATH /app:$PYTHONPATH

CMD ["python", "/app/crawler/main.py"]