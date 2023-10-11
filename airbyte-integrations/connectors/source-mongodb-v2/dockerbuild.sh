#!/usr/bin/env bash

docker buildx build --platform linux/amd64 -f Dockerfile -t jitsucom/source-mongodb:1.0.0 --push .