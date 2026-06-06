FROM alpine:3.19

RUN apk add --no-cache \
    ansible \
    openssh-client \
    rsync \
    git \
    bash

WORKDIR /workspace

# Copia os requirements e instala as collections
COPY requirements.yml /tmp/
RUN ansible-galaxy collection install -r /tmp/requirements.yml
