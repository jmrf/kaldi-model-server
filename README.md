# Kaldi Server

Kaldi-model-server is a simple Kaldi model server for online decoding with TDNN
chain nnet3 models.
It is written in pure Python and uses [PyKaldi](https://github.com/pykaldi/pykaldi)
to interface Kaldi as a library. It is mainly meant for live decoding with real
microphones and for single-user applications that need to work with realtime
speech recognition locally (e.g. dictation, voice assistants) or an aggregation
of multiple audio speech streams (e.g. decoding meeting speech).


Kaldi-model-server works on Linux (preferably Ubuntu / Debian based) and Mac OS X.

> 🏗️ TODO: Explain the `server` component

> 🏗️ TODO: Explain the `rabbitMQ` mechanism (instead of REDIS)

## Table of Contents

<!--ts-->
   * [Kaldi Server](#kaldi-server)
      * [Table of Contents](#table-of-contents)
      * [How To](#how-to)
         * [Local Installation](#local-installation)
            * [Ubuntu dependencies](#ubuntu-dependencies)
            * [Python dependencies](#python-dependencies)
            * [Kaldi &amp; pre-built Pykaldi binaries](#kaldi--pre-built-pykaldi-binaries)
         * [Local run](#local-run)
            * [Server](#server)
            * [Client](#client)
         * [Docker Build](#docker-build)
         * [Docker run](#docker-run)

<!-- Added by: jose, at: Fri Jan 28 23:56:27 CET 2022 -->

<!--te-->

## How To

### Local Installation

> This is known to work in `Ubuntu 18.04` with a python 3.8 venv!

#### Ubuntu dependencies

```bash
./scripts/install_ubuntu_deps.sh
```

#### Python dependencies

> 💡 **Tip**: Before installing the python dependencies, it is recommended to activate a
> `virtualvenv` or `conda env`

```bash
python3.8 -m venv .venv
source .venv/bin/activate
```

or with conda:

```bash
conda create -n kaldi-server python=3.8
conda activate kaldi-server
```

Finally install all python dependencies with:

```bash
pip install -r requirements.txt
```

#### Kaldi & pre-built Pykaldi binaries


First we need to install `kaldi`:

```bash
# download, compile and install Kaldi
./scripts/install_kaldi.sh  # or install_kaldi_intel.sh
```

After compiling Kaldi severeal binaries will be created under `./kaldi/src/`.
These directories must be added to the PATH in order for `pykaldi` to work:

```bash
source paths.env
```

Then we can install `pykaldi` from pre-built wheels:
```
# download and install pykaldi
./scripts/install_pykaldi.sh
```

> Check [these instruction](http://ltdata1.informatik.uni-hamburg.de/pykaldi/README.txt)
> to see the original installation readme.

> Installation scripts and PyKaldi wheels available
> [here](https://ltdata1.informatik.uni-hamburg.de/pykaldi/)



### Local run

First download pre-trained models for English:

```bash
./scripts/download_example_models.sh
```

#### Server

```bash
source .venv/bin/activate
source paths.env
make run
```

> NOTE: You might need to find your input device first and pass it to the `make run` command!
>
> ```bash
> python -m kserver.run --list-audio-interfaces
> ```

#### Client

To trigger the ASR from the mic:

```python
import json

from kserver.rabbit import BlockingQueuePublisher

# init the rabbitMQ Publisher
pub = BlockingQueuePublisher("localhost", "asr-q", "fiona", "topic")

# Send a hotword-detected event, which will trigger ASR from the local mic
pub.send_message(json.dumps([{}]), "hotword-detected")
```


### Docker Build

There are two multi-arch (`armv7` and `x86_64`) docker images:

 - [pykaldi](dockerfiles/pykaldi.Dockerfile): an Ubuntu 18.04 image with
      kaldi, pykaldi==0.2.1 and python3.8 serving as base for the ASR server image.
      In addition, a pykaldi .whl is built which can be extracted from the
      image to install pykaldi much faster.

 - [asr](dockerfiles/Dockerfile): Containing the **pyKaldi Server** and based
      on the image above


 To build the images:

 ```bash
 # First init docker's buildx
 ./scripts/init_docker_multibuild.sh

 # Then build and push the images. Can take veeeeery long time
 make build-pykaldi-docker
 make build-docker
 ```

 To check the image has been built succesfully for both architectures:

```bash
docker manifest inspect jmrf/pykaldi:0.2.1-cp38
```

Which should output something similar to:

```json
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
   "manifests": [
      {
         "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
         "size": 2224,
         "digest": "sha256:ca3f431364cda07e5f9b801352616ef5ee89237d6b05e16b48b10be348e9cece",
         "platform": {
            "architecture": "amd64",
            "os": "linux"
         }
      },
      {
         "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
         "size": 2224,
         "digest": "sha256:b3cf3d7834985113b937b4d6809c11ab971c0f95f242ffaad50cb2e0a77485bf",
         "platform": {
            "architecture": "arm",
            "os": "linux",
            "variant": "v7"
         }
      }
   ]
}
```

From the above `sha256 digest` you can try to run the image for another
architecture by amulating with `qemu`:

```bash
docker run -it \
   -v /usr/bin/qemu-arm-static:/usr/bin/qemu-arm-static \
   jmrf/pykaldi:0.2.1-cp38@sha256:b3cf3d7834985113b937b4d6809c11ab971c0f95f242ffaad50cb2e0a77485bf
```

Alternatively:

```bash
docker run -it --platform linux/arm/v7 jmrf/pykaldi:0.2.1-cp38
```

### Docker run

The easiest way is using `docker-compose`.

To tun the asr server:

```bash
docker-compose up asr-server
```
