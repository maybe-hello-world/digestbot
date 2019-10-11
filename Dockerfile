FROM continuumio/miniconda3:latest

# create env
COPY environment.yml /tmp/
RUN conda env create -f /tmp/environment.yml -n digest

# set created env as default
RUN echo "source activate digest" > ~/.bashrc
ENV PATH /opt/conda/envs/digest/bin:$PATH

# copy the bot
COPY digestbot /app/digestbot
ENV PYTHONPATH /app:$PYTHONPATH

CMD ["python", "/app/digestbot/main.py"]