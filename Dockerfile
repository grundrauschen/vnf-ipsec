FROM alpine:latest
LABEL maintainer="tobias.famulla@travelping.com"

ENV LANG=en_US.utf8

RUN apk add --update --no-cache strongswan tcpdump iproute2 python3 python3-dev build-base && \
        pip3 install --upgrade pip && \
        pip3 install pipenv vici && \
        mkdir -p /opt/vnfipsec

ADD . /opt/vnfipsec
WORKDIR /opt/vnfipsec
RUN pipenv install

ENTRYPOINT ["pipenv", "run", "python", "/opt/vnfipsec/vnfipsec.py"]
