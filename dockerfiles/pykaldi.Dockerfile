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

# clone pykaldi v0.2.2
RUN git clone -b v0.2.2 --depth 1 https://github.com/pykaldi/pykaldi.git && \
    cd pykaldi && \
        git clone -b pykaldi https://github.com/pykaldi/clif

# Install all dependencies
RUN cd pykaldi/tools && \
        ./check_dependencies.sh && \
        ./install_protobuf.sh && \
        ./install_clif.sh

# Install Kaldi
COPY scripts/install_kaldi.sh ./
RUN cd pykaldi/tools && /app/install_kaldi.sh

# Create a .whl and install
RUN cd pykaldi && \
    python setup.py bdist_wheel && \
    pip install dist/pykaldi-0.2.2-cp38-cp38-linux_$(uname -m).whl && \
    find . -iname '*.o' -exec rm '{}' \; && \
    echo "🎆 Done!"
