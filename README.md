# Introduction
This project aims to create a basic Linux system on the Raspberry Pi 3 Model B from scratch for learning purposes.
The system will contains the Linux kernel compiled for AARCH64. As init it will be used the file src/init.cpp.

# Prerequisites
For building the project we will use docker (or podman).

Debian based distributions:
```bash
$ sudo apt install podman
```

# Create minimal distro

Launch an interactive shell inside the Docker container:
```bash
$ cd scripts/build_environment.sh
```

Once in the container run:
```bash
cd src
./scripts/build.py
```

This Python script will do the following:
- Download bootloader
- Download kernel and build it
- Build src/init.cpp
- Assemble a disk image with the distro

The disk image will be located in **workspace_\<timestamp\>/filesystem/basic_system.iso**.
This image can be copied to the Raspberry Pi SDCard using the Raspberry Pi Imager tool.
