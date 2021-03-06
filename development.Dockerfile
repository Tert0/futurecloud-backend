FROM python:3.9-alpine

RUN apk add --no-cache build-base musl-dev gcc yaml-dev

RUN pip install pipenv

WORKDIR /app

COPY Pipfile .

COPY Pipfile.lock .

RUN python -m pipenv install --system --deploy

COPY config.yaml .

CMD uvicorn app.main:app --reload --port 80 --host 0.0.0.0