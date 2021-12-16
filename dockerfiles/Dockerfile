# ------------------ 1st stage ------------------
# Compiling Kaldi 2.0
FROM ubuntu:18.04 as stage1


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    cmake \
    curl \
    gfortran \
    git \
    g++ \
    graphviz \
    libatlas3-base \
    libtool \
    make \
    pkg-config \
    python2.7 \
    python3.8 \
    python3.8-dev \
    python3.8-distutils \
    python3.8-venv \
    sox \
    subversion \
    unzip \
    wget \
    zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir /app


WORKDIR /app


# Create and add the python venv to the path
RUN python3.8 -m venv .pykaldi_env
ENV VIRTUAL_ENV=/app/.pykaldi_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install \
    numpy \
    pyparsing \
    wheel \
    ninja  # not required but strongly recommended

RUN git clone https://github.com/pykaldi/pykaldi.git && \
    cd pykaldi && \
    git clone -b pykaldi https://github.com/pykaldi/clif

# Install all dependencies
RUN cd pykaldi/tools && \
    ./check_dependencies.sh && \
    ./install_protobuf.sh && \
    ./install_clif.sh

COPY scripts/install_kaldi.sh scripts/install_openblas_armv7.sh ./
RUN cd pykaldi/tools && \
    /app/install_kaldi.sh


# ------------------ 2nd stage ------------------
FROM python:3.8-slim

RUN mkdir /app
WORKDIR /app

COPY --from=stage1 /app/pykaldi /app/pykaldi

# Add Kaldi to the path
ENV KALDI_ROOT=/app/pykaldi/tools/kaldi
ENV LD_LIBRARY_PATH=$KALDI_ROOT/src/lib:$KALDI_ROOT/tools/openfst-1.6.7/lib:$LD_LIBRARY_PATH
ENV PATH=$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/../kaldi_lm/:$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin/:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/kwsbin:$KALDI_ROOT/src/nnet3bin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/tools/sph2pipe_v2.5/:$KALDI_ROOT/src/rnnlmbin:$PWD:$PATH

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        gfortran \
        portaudio19-dev \
        python3-pyaudio \
        libsamplerate0 \
        libopenblas-dev liblapack-dev libffi-dev && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Copy the repo code
COPY kserver ./kserver
COPY requirements.txt ./

# Python deps
RUN pip3 install \
    pykaldi/dist/pykaldi-0.2.1-cp38-cp38-linux_$(unage -m).whl
RUN pip install -r requirements.txt

VOLUME ["/app/models"]
VOLUME ["/app/conf"]

ENTRYPOINT [ "python", "-m", "kserver.run" ]
