# Nuvoton M051 Toolchain Docker Image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gcc-arm-none-eabi \
    binutils-arm-none-eabi \
    git \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Nu-Link tools (requires manual download in production)
RUN echo "Nu-Link tools installation required"

# Install Upload Bridge dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /workspace

CMD ["/bin/bash"]

