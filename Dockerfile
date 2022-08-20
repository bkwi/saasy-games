from python:3.10.6-slim-buster

ENV PROJECT_DIR=/app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PYTHONUNBUFFERED=TRUE

COPY ./requirements.txt $PROJECT_DIR/requirements.txt
RUN pip install -r $PROJECT_DIR/requirements.txt

COPY ./games $PROJECT_DIR/games
COPY ./templates $PROJECT_DIR/templates

WORKDIR $PROJECT_DIR
