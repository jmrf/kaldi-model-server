# Kaldi Server

Kaldi-model-server is a simple Kaldi model server for online decoding with TDNN
chain nnet3 models.
It is written in pure Python and uses [PyKaldi](https://github.com/pykaldi/pykaldi)
to interface Kaldi as a library. It is mainly meant for live decoding with real
microphones and for single-user applications that need to work with realtime
speech recognition locally (e.g. dictation, voice assistants) or an aggregation
of multiple audio speech streams (e.g. decoding meeting speech).

Computations currently happen on the device that interfaces the microphone.
The [redis](https://redis.io) messaging server and a event server that can send
[server-sent event notifications](https://www.w3schools.com/html/html5_serversentevents.asp)
to a web browser can also be run on different devices.

Kaldi-model-server works on Linux (preferably Ubuntu / Debian based) and Mac OS X.
Because redis supports a [wide range of different programming languages](https://redis.io/clients),
it can easily be used to interact with decoded speech output in realtime with your favourite
programming language.

For demonstration purposes we added an simple demo example application that uses a
Python based event server with [Flask](https://palletsprojects.com/p/flask/)
(event_server.py) to display the recognized words in a simple HTML5 app running in a browser window.


## Table of Contents

<!--ts-->
   * [Kaldi Server](#kaldi-server)
      * [Table of Contents](#table-of-contents)
      * [How To](#how-to)
         * [Installation](#installation)
            * [Ubuntu dependencies](#ubuntu-dependencies)
            * [Kaldi &amp; pre-built pykaldi binaries](#kaldi--pre-built-pykaldi-binaries)

<!-- Added by: jose, at: Wed Dec  8 21:13:12 CET 2021 -->

<!--te-->

## How To

### Installation


#### Ubuntu dependencies

```bash
./scripts/install_ubuntu_deps.sh
```

#### Kaldi & pre-built pykaldi binaries


First we need to get the environment ready and install `kaldi`:

```bash

```

Then we can install `pykaldi`:

```bash
wget https://ltdata1.informatik.uni-hamburg.de/pykaldi/pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl
pip install pykaldi-0.2.0-cp38-cp38-linux_x86_64.whl
```

> Check [these instruction](http://ltdata1.informatik.uni-hamburg.de/pykaldi/README.txt)
> to quickly install PyKaldi.

> Installation scripts and PyKaldi wheels available
> [here](https://ltdata1.informatik.uni-hamburg.de/pykaldi/)


