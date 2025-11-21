# ESP32-S3 Toolchain Docker Image
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

# Install ESP-IDF for ESP32-S3
RUN git clone --recursive https://github.com/espressif/esp-idf.git /opt/esp-idf && \
    cd /opt/esp-idf && \
    ./install.sh esp32s3 && \
    echo ". /opt/esp-idf/export.sh" >> /root/.bashrc

# Install esptool
RUN pip3 install esptool

# Install Upload Bridge dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /workspace

CMD ["/bin/bash"]

