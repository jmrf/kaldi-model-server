#!/bin/bash

# Installation script for Kaldi

set -e
set -o pipefail

say() {
 echo "$@" | sed \
         -e "s/\(\(@\(red\|green\|yellow\|blue\|magenta\|cyan\|white\|reset\|b\|u\)\)\+\)[[]\{2\}\(.*\)[]]\{2\}/\1\4@reset/g" \
         -e "s/@red/$(tput setaf 1)/g" \
         -e "s/@green/$(tput setaf 2)/g" \
         -e "s/@yellow/$(tput setaf 3)/g" \
         -e "s/@blue/$(tput setaf 4)/g" \
         -e "s/@magenta/$(tput setaf 5)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}

# TODO: Install from own fork repo to avoid changes
KALDI_GIT="-b pykaldi https://github.com/jmrf/kaldi"
KALDI_DIR="$PWD/kaldi"

if [ ! -d "$KALDI_DIR" ]; then
  git clone $KALDI_GIT $KALDI_DIR
else
  say @yellow[[ "$KALDI_DIR already exists!" ]]
fi

cd "$KALDI_DIR/tools"
git pull


# Prevent kaldi from switching default python version
mkdir -p "python"
touch "python/.use_default_python"

./extras/check_dependencies.sh

architecture=""
case $(uname -m) in
    i386)   architecture="386" ;;
    i686)   architecture="386" ;;
    amd64)   architecture="amd64" ;;
    x86_64) architecture="x86_64" ;;
    arm)    dpkg --print-architecture | grep -q "arm64" && architecture="arm64" || architecture="arm" ;;
esac

say @magenta[["Architecure is: ${architecture}"]]

cwd=$(dirname $0)
if [ $architecture == x86_64 ]; then
	say @magenta[["Installing MKL with: ./extras/install_mkl.sh"]]
	./extras/install_mkl.sh
elif [[ $architecture == arm ]]; then
	say @magenta[["Installing OpenBlas with: ./extras/install_openblas.sh"]]
	./extras/install_openblas.sh
else
	say @red[["Don't know what to do for Architecture $architecture. Exiting..."]]
	exit 1
fi


make -j4

cd ../src
./configure \
  --shared \
  --use-cuda=no \
  --static-math=yes

make clean -j && make depend -j && make -j4

say @green[[ "🎉 Done installing Kaldi." ]]
