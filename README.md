__Work in progress__

# Introduction
This project aims to create a basic Linux system on the Raspberry Pi 3 Model B from scratch.

It boots the Linux kernel (64 bits) and launches a binary that I use as init. The binary launched is generated from init.cpp file.

This is a personal project that I use for learning purposes. Feel free to fork it if it fits your needs.

# Prerequisites
Ubuntu:
```bash
$ sudo apt install git bc bison flex libssl-dev make libc6-dev libncurses5-dev
```

Fedora:
```bash
$ sudo dnf install git bc bison flex openssl-devel make glibc-devel ncurses-devel
```

Then for booth distributions, you need to download linaro toolchain for cross compiling from the official [ARM developers page](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-a/downloads).  
You must download **AArch64 GNU/Linux target (aarch64-none-linux-gnu)** and **AArch64 ELF bare-metal target (aarch64-none-elf)**.  

```bash
# Download and untar aarch64-none-linux-gnu in toolchain folder
$ wget --directory-prefix=toolchain https://developer.arm.com/-/media/Files/downloads/gnu-a/10.2-2020.11/binrel/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu.tar.xz
$ mkdir toolchain/gcc-10-aarch64-none-linux-gnu
$ tar -xvf toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu.tar.xz -C toolchain

# Download and untar aarch64-none-elf in toolchain folder
$ wget --directory-prefix=toolchain https://developer.arm.com/-/media/Files/downloads/gnu-a/10.2-2020.11/binrel/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf.tar.xz
$ mkdir toolchain/gcc-10-aarch64-none-elf
$ tar -xvf toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf.tar.xz -C toolchain
```

Then, you must include the bin folder of them in the **PATH** variable. 

```bash
export PATH=${PWD}/toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-linux-gnu/bin:${PWD}/toolchain/gcc-arm-10.2-2020.11-x86_64-aarch64-none-elf/bin:${PATH}
```

# Create minimal distro in temp directory
```bash
$ ./create_basic_linux_hello_world.sh
```

# Format SDCARD
The second step is to format the SDCARD with two partitions.  
The first one with a size around 256 MB must be in formt vFAT.  
The second one with the remaining space must be in format EXT4.  

```bash
# Change for your SDCARD dev
export SDCARD_DEV=sdX

# Umount mounted filesystems
umount ${SDCARD_DEV}*

# Create a new partition table on your device (it will delete everything in the sdcard)
# TODO: Must be fixed
# sudo parted --script ${SDCARD_DEV} \
#     mklabel msdos \
#     mkpart primary fat32 4194kB 250MiB \
#     mkpart primary ext4 250MiB 100% \
#     set 2 lba off
```

# Copy temp directory to the SDCARD
```bash
# Change for your workspace dir
export WORKSPACE_DIR=workspace

# Create a temporal copy of the files to transfer
mkdir -p ${WORKSPACE_DIR}/temp/{boot,rootfs}
cp -a -r ${WORKSPACE_DIR}/rpi_file_tree/boot/* ${WORKSPACE_DIR}/temp/boot/
cp -a -r ${WORKSPACE_DIR}/rpi_file_tree/rootfs/* ${WORKSPACE_DIR}/temp/rootfs/

# Transfer device trees to root (Only rootfs, because root is in a FAT partition)
sudo chown -R root:root ${WORKSPACE_DIR}/temp/rootfs/

# Mount SDCARD
mkdir -p ${WORKSPACE_DIR}/mnt/boot/
mkdir -p ${WORKSPACE_DIR}/mnt/rootfs/

sudo mount -t vfat -o uid=1000,gid=1000 -n /dev/${SDCARD_DEV}1 ${WORKSPACE_DIR}/mnt/boot/
sudo mount -t ext4 -n /dev/${SDCARD_DEV}2 ${WORKSPACE_DIR}/mnt/rootfs/

# Copy all to SDCARD
cp -a -r ${WORKSPACE_DIR}/temp/boot/* ${WORKSPACE_DIR}/mnt/boot/
sudo cp -a -r ${WORKSPACE_DIR}/temp/rootfs/* ${WORKSPACE_DIR}/mnt/rootfs/

# Sync writes
sync

# Umount
sudo umount ${WORKSPACE_DIR}/mnt/boot
sudo umount ${WORKSPACE_DIR}/mnt/rootfs
rm -r ${WORKSPACE_DIR}/mnt

# Remove temp copy of files
sudo rm -r ${WORKSPACE_DIR}/temp
```
