#!/usr/bin/env bash

# A script that can be used to synchronise the DLSA code and rust executable to DAS5. The rust binary has to be cross
# compiled as we have not set up a rust nightly compilation setup on DAS5. Note this script requires SSH aliases to be
# set up as discussed in `DAS5.md`.

if [ "$(basename "$PWD")" != "DLSA" ]; then
    echo "Current directory is not DLSA. Exiting..."
    exit 1
fi

if ! docker info &> /dev/null; then
  echo "Docker daemon is not running. Exiting..."
  exit 1
fi

cd rust &&
make build-linux-avx2 && # The docker daemon should be running for this.
cd .. &&
rsync -ru --delete --progress --exclude='/.git' --filter="dir-merge,- .gitignore" ./* DAS5:DLSA &&

rsync -ru --delete --progress --exclude '*/' rust/target/x86_64-unknown-linux-musl/release/* DAS5:DLSA/rust/target/release
# Make sure the directories used here exist (on the host and on the DAS5 remote).
