FROM python:3.10-slim-buster

WORKDIR /app/

COPY . .

RUN pip install uvicorn boto3

RUN pip install -r requirements.txt

CMD uvicorn --host=0.0.0.0 main:app --reload
