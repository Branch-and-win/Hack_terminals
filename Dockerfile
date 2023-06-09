# Instructions copied from - https://hub.docker.com/_/python/
FROM python:3.7-slim

WORKDIR /task

RUN apt-get update

COPY requirements.txt .
RUN pip install -r requirements.txt
# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]
