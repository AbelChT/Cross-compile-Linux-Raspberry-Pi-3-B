# Introduction
The aims of this proyect is to create a basic linux system on the Raspberry Pi 3 Model B from scratch.

# Prerequisites
Ubuntu:
```bash
sudo apt install git bc bison flex libssl-dev make libc6-dev libncurses5-dev
```

Fedora:
```bash
sudo dnf install git bc bison flex openssl-devel make glibc-devel ncurses-devel
```

Booth:

Download linaro toolchain for cross compiling from the official [ARM developers page](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-a/downloads).  
You must download **AArch64 GNU/Linux target (aarch64-none-linux-gnu)** and **AArch64 ELF bare-metal target (aarch64-none-elf)**.  
Then, you must include the bin folder of them in the **PATH** variable.  

# Create minimal distro in temp directory
```bash
./create_basic_linux_hello_world.sh
```

# Format SDCARD
The second step is to format the SDCARD with two partitions.  
The first one with a size around 256 MB must be in formt vFAT.  
The second one with the remaining space must be in format EXT4.  

# Copy temp directory to the SDCARD
```bash
# Change for your workspace dir
export WORKSPACE_DIR=workspace

# Change for your SDCARD dev
export SDCARD_DEV=sdX

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
