#!/bin/bash


GPG_KEY_ID="Daniel Gaspar"
SUPERSET_VERSION=0.35.0


GPG_PRIVATE_KEY=$(gpg --export-secret-keys -a "${GPG_KEY_ID}")
GPG_PUBLIC_KEY=$(gpg --export -a "${GPG_KEY_ID}")

docker build --no-cache -t apache-superset:${SUPERSET_VERSION} -f Dockerfile.make_tarball .

docker run --rm -ti \
  -e VERSION=0.35.0 \
  -e GPG_PRIVATE_KEY="$GPG_PRIVATE_KEY" \
  -e GPG_PUBLIC_KEY="$GPG_PUBLIC_KEY" \
  apache-superset:${SUPERSET_VERSION}
