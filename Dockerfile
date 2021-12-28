FROM python:3.9-alpine
WORKDIR /script
COPY ./gen-log.py gen-log.py
COPY ../madeup.log madeup.log
CMD ["python3", "gen-log.py", "madeup.log"]
