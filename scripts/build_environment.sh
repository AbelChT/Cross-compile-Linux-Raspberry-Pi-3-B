#!/bin/bash
# Find docker or podman
if command -v docker &> /dev/null; then
    echo "Using Docker"
    CONTAINER_APP=docker
elif command -v podman &> /dev/null; then
    echo "Using Podman"
    CONTAINER_APP=podman
else
    echo "Error: Install Docker or Podman first"
    exit 1
fi

# Build and run container
$CONTAINER_APP build -t linux-rpi-build-focal .
$CONTAINER_APP run -it --rm -v ..:/src linux-rpi-build-focal