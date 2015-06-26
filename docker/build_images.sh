#!/bin/bash

# Tag the images
TAG=latest

# Build and push all docker images
for dir in "base" "x_509" "worker" "flower" "frontend" "rabbitmq" "mongodb"; do #`find . -name Dockerfile| awk 'BEGIN {FS="/"} {print $2}'|sort -r`; do
	cd $dir
	docker build --no-cache=true -t nachtmaar/androlyze_$dir:$TAG .
	docker push nachtmaar/androlyze_$dir:$TAG
	cd ..
done
