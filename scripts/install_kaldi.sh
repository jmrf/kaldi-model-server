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

architecture=$(uname -m)
say @magenta[["Architecure is: ${architecture}"]]

if [ $architecture == x86_64 ]; then
	say @magenta[["Installing MKL with: $KALDI_DIR/tools/extras/install_mkl.sh"]]
	$KALDI_DIR/tools/extras/install_mkl.sh
elif [ $architecture == armv7l ]; then
  # NOTE: This script has to be copied from 'scripts/', not present by default
  #       in the kaldi repo.
	say @magenta[["Installing OpenBlas with: $KALDI_DIR/tools/extras/install_openblas_armv7.sh"]]
  $KALDI_DIR/tools/extras/install_openblas_armv7.sh
else
	say @magenta[["Installing OpenBlas with: $KALDI_DIR/tools/extras/install_openblas.sh"]]
	$KALDI_DIR/tools/extras/install_openblas.sh
fi


make -j $(nproc)

cd ../src
./configure \
  --shared \
  --use-cuda=no \
  --static-math=yes

make clean -j && make depend -j && make -j $(nproc)

say @green[[ "🎉 Done installing Kaldi." ]]
