#!/bin/bash

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

arch=$(uname -m)

say @cyan[["Detected architecture: $arch"]]

if [ $arch == x86_64 ]; then
    say @green[["Downloading..."]]
    gdown --id 1rEDy6G64dZE9piTCoLC7k5JLsUEC9iKU
elif [ $arch == armv7 ]; then
    say @green[["Downloading..."]]
    gdown --id 1kwCikTCH7pX3IXrl03xprs_gyJjYXKJR
else
    say @red[["No available wheel for $arch!"]]
fi

say @green[["Installing pyKaldi wheel..."]]
pip install $WHEEL_NAME
rm $WHEEL_NAME

