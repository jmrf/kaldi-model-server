docker buildx build --push \
    --platform linux/amd64,linux/arm/v7 \
    -t jmrf/asr-server:${VERSION} \
    -t jmrf/asr-server:latest \
    -f dockerfiles/asr.Dockerfile .


docker buildx build --load \
    --platform linux/amd64 \
    -t jmrf/pykaldi-whl:latest \
    -f dockerfiles/pykaldi-whl.Dockerfile .


docker run -it \
    --entrypoint /bin/bash \
    jmrf/pykaldi-whl:latest


apt-get update && \
    apt-get install -y --no-install-recommends \
    cmake \
    curl \
    graphviz \
    libatlas3-base \
    pkg-config \
    subversion \
    python3-pip \
    python3-venv \
    python3.8-dev

python3.8 -m pip install --upgrade pip
python3.8 -m pip install --upgrade setuptools
python3.8 -m pip install numpy pyparsing
python3.8 -m pip install ninja  # not required but strongly recommended

git clone https://github.com/pykaldi/pykaldi.git
cd pykaldi

git clone -b pykaldi https://github.com/pykaldi/clif
git clone -b pykaldi https://github.com/pykaldi/kaldi

ln -s /usr/bin/python2.7 /usr/bin/python



