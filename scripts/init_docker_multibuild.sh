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

say @magenta[["⚒️ Current docker builders:"]]
docker buildx ls

# https://docs.docker.com/desktop/multi-arch/
# https://docs.docker.com/engine/reference/commandline/buildx_build/
# https://www.docker.com/blog/getting-started-with-docker-for-arm-on-linux/
# Create a multi-builder for: linux/amd64,linux/arm/v7
say @magenta[["🏗️ Creating a buildx for: linux/amd64,linux/arm/v7"]]
docker buildx create \
    --name multi-builder \
    --platform linux/amd64,linux/arm/v7 \
    --use
docker buildx inspect --bootstrap

say @magenta[["🏗️ Registering Arm executables to run on x64"]]
docker run --rm --privileged docker/binfmt:820fdd95a9972a5308930a2bdfb8573dd4447ad3
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
