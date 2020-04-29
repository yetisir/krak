FROM python:3.9-rc-buster

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "-m", "main"]

