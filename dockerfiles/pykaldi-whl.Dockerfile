FROM ubuntu:18.04 as stage1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    ca-certificates \
    git \
    g++ \
    gfortran \
    libtool \
    make \
    patch \
    python2.7 \
    python3 \
    sox \
    subversion \
    unzip \
    wget \
    zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir /app


WORKDIR /app

# Copy installation scripts
COPY scripts/install_kaldi.sh scripts/install_openblas_armv7.sh ./

# Install Kaldi
RUN ln -s /usr/bin/python2.7 /usr/bin/python
