# ------------------ 1st stage ------------------
# Compiling Kaldi 2.0
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
RUN ln -s /usr/bin/python2.7 /usr/bin/python && \
    ./install_kaldi.sh


# ------------------ 2nd stage ------------------
FROM python:3.8-slim

RUN mkdir /app
WORKDIR /app

COPY --from=stage1 /app/kaldi /app/kaldi

# Add Kaldi to the path
ENV KALDI_ROOT=/app/kaldi
ENV LD_LIBRARY_PATH=$KALDI_ROOT/src/lib:$KALDI_ROOT/tools/openfst-1.6.7/lib:$LD_LIBRARY_PATH
ENV PATH=$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/../kaldi_lm/:$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin/:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/kwsbin:$KALDI_ROOT/src/nnet3bin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/tools/sph2pipe_v2.5/:$KALDI_ROOT/src/rnnlmbin:$PWD:$PATH

# Copy the repo code
COPY kserver ./kserver
COPY requirements.txt pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl ./

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libsamplerate0 \
        portaudio19-dev \
        python3-pyaudio && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Python deps
RUN pip3 install -r requirements.txt && \
    pip3 install pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl

VOLUME ["/app/models"]
VOLUME ["/app/conf"]
ENTRYPOINT [ "python", "-m", "kserver.run" ]
