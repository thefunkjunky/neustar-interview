# FROM python:3.9-alpine
FROM python:3.9-slim-bullseye
WORKDIR /script
COPY ./gen-log.py gen-log.py
COPY ./madeup.log madeup.log
CMD ["python3", "gen-log.py", "madeup.log"]
ENTRYPOINT ["tail", "-f", "/dev/null"]

