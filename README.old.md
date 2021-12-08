# Kaldi-model-server



> See example/ - An example HTML5 application that visualizes decoded speech with confidence values

To start the web demo run:

```bash
/etc/init.d/redis-server start
python3 event_server.py
```

and then in a different window:

```bash
python3 nnet3_model.py
```

You can browse to http://127.0.0.1:5000/ and should see words appear as you speak into your microphone. Word confidences are computed after an utterance is decoded and visualized with different levels of greyness.

## Installation

Check [these updated instruction](http://ltdata1.informatik.uni-hamburg.de/pykaldi/README.txt)
 to quickly install PyKaldi.

To install dependencies for PyKaldi and kaldi-model-server on Ubuntu do:

```bash
# Ubuntu Linux
sudo apt-get install portaudio19-dev redis-server autoconf automake cmake curl g++ git graphviz libatlas3-base libtool make pkg-config subversion unzip wget zlib1g-dev virtualenv python3-dev libsamplerate0
```



The easist way to install PyKaldi and kaldi-model-server is in a virtual environment (named pykaldi_env):

```bash
mkdir ~/projects/
cd ~/projects/
git clone https://github.com/pykaldi/pykaldi
git clone https://github.com/uhh-lt/kaldi-model-server

cd kaldi-model-server

virtualenv -p python3 pykaldi_env
source ./pykaldi_env/bin/activate
```

Install Python3 pip dependencies:

```bash
pip3 install numpy pyparsing ninja redis pyyaml pyaudio flask flask_cors bs4 samplerate scipy
```

Compile and install Protobuf, CLIF and KALDI dependencies (compiliation can take some time unfortunatly):

```bash
cd  ~/projects/pykaldi/tools/
./check_dependencies.sh  # checks if system dependencies are installed
./install_protobuf.sh ~/projects/kaldi-model-server/pykaldi_env/bin/python3  # installs both the Protobuf C++ library and the Python package
./install_clif.sh ~/projects/kaldi-model-server/pykaldi_env/bin/python3  # installs both the CLIF C++ library and the Python package
./install_kaldi.sh ~/projects/kaldi-model-server/pykaldi_env/bin/python3 # installs the Kaldi C++ library
```

Now install PyKaldi:

```bash
cd ~/projects/pykaldi
~/projects/pykaldi$ python3 setup.py install
```

You can test the install with:

```bash
~/projects/pykaldi$ python3 setup.py test
```
You need to download the model:

```bash
cd ~/projects/kaldi-model-server
./download_example_models.sh
```

Whenever you want to run nnet3_model.py you have to run source ./bin/activate once per Bash session:

```bash
cd ~/projects/kaldi-model-server
source ./bin/activate
python3 nnet3_model.py
```
