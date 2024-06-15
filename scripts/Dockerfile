FROM ubuntu:20.04
# Dependencies from central repo
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y tzdata
RUN apt-get install -y git bc bison flex libssl-dev make libc6-dev libncurses5-dev wget xz-utils python3 mtools dosfstools qemu-utils

# ARM compiler
RUN mkdir /toolchain
# Linux compiler
RUN wget https://developer.arm.com/-/media/Files/downloads/gnu-a/10.2-2020.11/binrel/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu.tar.xz -P /toolchain
RUN tar -xf /toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu.tar.xz -C /toolchain
ENV GCC_ARM_LINUX_PATH=/toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu/bin
# Bare metal compiler
RUN wget https://developer.arm.com/-/media/Files/downloads/gnu-a/10.2-2020.11/binrel/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf.tar.xz -P /toolchain
RUN tar -xf /toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf.tar.xz -C /toolchain
ENV GCC_ARM_BARE_METAL_PATH=/toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf/bin

# Entry
ENV HOME=/root/
ENV USER=root
ENTRYPOINT /bin/bash