# ATmega2560 Toolchain Docker Image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gcc-avr \
    avr-libc \
    avrdude \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Upload Bridge dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /workspace

CMD ["/bin/bash"]

