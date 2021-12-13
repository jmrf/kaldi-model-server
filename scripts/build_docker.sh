#!/usr/bin/env bash

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

# check current directory
current_dir=${PWD##*/}
if [ "$current_dir" == "scripts" ]; then
    say @red[["This scripts should be executed from the root folder as: ./scripts/build_mai_docker.sh"]]
    exit
fi


VERSION=$(python -c 'import kserver; print(kserver.__version__)')

say @blue[["Using version $VERSION"]]

{
    # build for both platforms
    say @magenta[["🛠️  Starting linux/amd64,linux/arm/v7 build..."]]
    docker buildx build --rm \
      --platform linux/amd64,linux/arm/v7 \
      -t jmrf/asr-server:${VERSION} \
      -t jmrf/asr-server:latest \
      -f dockerfiles/asr.Dockerfile .
} || {
    say @magenta[["🛠️  Starting regular build..."]]
    docker build --rm  \
      -t jmrf/asr-server:${VERSION} \
      -t jmrf/asr-server:latest \
      -f dockerfiles/asr.Dockerfile .
} || {
  say @red[["Couldn't build Docker kserver image... exiting"]];
  exit 1;
}
