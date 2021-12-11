FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y \
    portaudio19-dev \
    redis-server \
    autoconf \
    automake \
    cmake \
    curl \
    g++ \
    git \
    graphviz \
    libatlas3-base \
    libtool \
    make \
    pkg-config \
    subversion \
    unzip \
    wget \
    zlib1g-dev \
    virtualenv \
    python2.7 \
    python3-dev \
    python3.8 \
    python3.8-dev \
    libsamplerate0 \
    sox \
    software-properties-common \
    gfortran \
    alsa-utils


RUN mkdir /app
WORKDIR /app

# TODO: Host this elsewhere always accesible
RUN wget -q \
    https://ltdata1.informatik.uni-hamburg.de/pykaldi/pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl


COPY requirements.txt \
    scripts/install_kaldi.sh \
    scripts/install_mkl.sh ./

# Install Kaldi
RUN ./install_mkl.sh
RUN ln -s /usr/bin/python2.7 /usr/bin/python && \
    ./install_kaldi.sh && \
    rm pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl && \
    find . -name "*.o" -type f -delete

# Add Kaldi to the path
ENV KALDI_ROOT=/app/kaldi
ENV LD_LIBRARY_PATH=$KALDI_ROOT/src/lib:$KALDI_ROOT/tools/openfst-1.6.7/lib:$LD_LIBRARY_PATH
ENV PATH=$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/../kaldi_lm/:$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin/:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/kwsbin:$KALDI_ROOT/src/nnet3bin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/tools/sph2pipe_v2.5/:$KALDI_ROOT/src/rnnlmbin:$PWD:$PATH

# Create and add the python venv to the path
RUN virtualenv -p /usr/bin/python3.8 .pykaldi_env
ENV VIRTUAL_ENV=/app/.pykaldi_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install python deps
RUN pip3 install -r requirements.txt && \
    pip3 install pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl

# Copy the repo code
COPY kserver ./kserver

# CMD [ "python", "-m", "kserver.run", "-m", "12" ]
VOLUME ["/app/models"]
CMD [ "python3", "-m", "kserver.run", "-l" ]
