FROM --platform=linux/amd64 python:3.10

LABEL version="0.1"
LABEL author="Andrew Smirnov"

WORKDIR /

COPY ci/* /ci/
COPY requirements.txt /requirements.txt

RUN apt-get update && \
    apt-get install libgl1 libegl1 libxkbcommon0 libfontconfig1 libdbus-1-3 bc -y && \
    pip install --upgrade pip
RUN pip install -r requirements.txt
