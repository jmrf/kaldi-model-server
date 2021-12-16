
# Build the pykaldi builder iamge
docker buildx build --push \
    --platform linux/amd64,linux/arm/v7 \
    -t jmrf/pykaldi-whl:latest \
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
    python3.8 python3.8-dev python3.8-distutils python3.8-venv

# ln -sf /usr/bin/python2.7 /usr/bin/python
# ln -sf /usr/bin/python3.8 /usr/bin/python3

python3.8 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install \
        numpy \
        pyparsing \
        ninja  # not required but strongly recommended


git clone https://github.com/pykaldi/pykaldi.git
cd pykaldi
git clone -b pykaldi https://github.com/pykaldi/clif
# git clone -b pykaldi https://github.com/pykaldi/kaldi


cd tools
./check_dependencies.sh  # checks if system dependencies are installed
./install_protobuf.sh    # installs both the C++ library and the Python package
./install_clif.sh        # installs both the C++ library and the Python package
./install_kaldi.sh       # installs the C++ library
cd ..

cd tools/kaldi/tools/extras && \
    ./install_mkl.sh && \
    cd -

export KALDI_ROOT=/app/pykaldi/tools/kaldi
export LD_LIBRARY_PATH=$KALDI_ROOT/src/lib:$KALDI_ROOT/tools/openfst-1.6.7/lib:$LD_LIBRARY_PATH
export PATH=$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/../kaldi_lm/:$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin/:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/kwsbin:$KALDI_ROOT/src/nnet3bin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/tools/sph2pipe_v2.5/:$KALDI_ROOT/src/rnnlmbin:$PWD:$PATH


python setup.py bdist_wheel

