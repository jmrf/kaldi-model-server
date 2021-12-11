FROM uhhlt/kaldi-model-server

RUN apt-get update && \
    apt-get install -y \
    python3.8 \
    python3.8-dev


RUN mkdir /app
WORKDIR /app

COPY requirements.txt .

# Add the kaldi venv to the path
ENV VIRTUAL_ENV=/projects/kaldi-model-server/pykaldi_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Add the Kaldi root to the path
ENV KALDI_ROOT=/projects/kaldi-model-server/kaldi
ENV LD_LIBRARY_PATH=$KALDI_ROOT/src/lib:$KALDI_ROOT/tools/openfst-1.6.7/lib:$LD_LIBRARY_PATH
ENV PATH=$KALDI_ROOT/src/lmbin/:$KALDI_ROOT/../kaldi_lm/:$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin/:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/kwsbin:$KALDI_ROOT/src/nnet3bin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/tools/sph2pipe_v2.5/:$KALDI_ROOT/src/rnnlmbin:$PWD:$PATH


RUN pip install -r requirements.txt

VOLUME ["/app/models"]

# Copy the repo contents
COPY kserver ./kserver
COPY conf ./conf
CMD [ "python", "-m", "kserver.run", "-l" ]
