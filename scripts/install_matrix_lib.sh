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
	say @magenta[["Installing MKL with: $cwd/install_mkl.sh"]]
	$cwd/install_mkl.sh
elif [[ $architecture == arm ]]; then
	say @magenta[["Installing OpenBlas with: $cwd/install_openblas.sh"]]
	$cwd/install_openblas.sh
else
	say @red[["Don't know what to do for Architecture $architecture. Exiting..."]]
	exit 1
fi