# PIC18F4550 Toolchain Docker Image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install MPLAB XC8 (requires manual download in production)
# For now, this is a placeholder
RUN echo "MPLAB XC8 installation required"

# Install Upload Bridge dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /workspace

CMD ["/bin/bash"]

