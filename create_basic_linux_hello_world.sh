#!/bin/bash

#
# Usage
#
# Print the usage of the script
if [ "$1" = "help" ]; then
    echo "usage: $programname [first step] [last step]"
    echo "       It will execute the steps in the range [first step, last step]"
    exit 0
fi

#
# Configuration
#
# Project directories
export WORKSPACE_DIR=workspace
export SOURCES_DIR=$WORKSPACE_DIR/sources
export BUILD_DIR=$WORKSPACE_DIR/build
export PATCHES_DIR=$WORKSPACE_DIR/patches
export RPI_FILE_TREE_DIR=$WORKSPACE_DIR/rpi_file_tree
export TOOLCHAIN_DIR=$WORKSPACE_DIR/toolchain

# Cross compiler settings
export ARCH64_ELF_CC=aarch64-none-elf-
export ARCH64_LINUX_CC=aarch64-none-linux-gnu-

# Compilation settings
export NUM_CPUS=4

#
# STEPS
#
# Total number of steps
number_of_steps=4

# Step 1
## In the first step, will produce a workspace directory tree
function step_1() {
    echo "[Step 1/$number_of_steps]: Create workspace directories"

    # Directory where downloaded sources will be stored
    mkdir -p $SOURCES_DIR

    # Directory used for building the packages
    mkdir -p $BUILD_DIR

    # Directory where the files that will be copied to de MicroSD are stored
    mkdir -p $RPI_FILE_TREE_DIR/{boot,rootfs}
}

# Step 2
## In the second step, we will cross compile the Linux Kernel
function step_2() {
    echo "[Step 2/$number_of_steps]: Compile linux kernel and copy it to the temporal file system"

    # Clone kernel version 5.4 into the $BUILD_DIR/linux/ path
    git clone --depth 1 -b rpi-5.4.y https://github.com/raspberrypi/linux $BUILD_DIR/linux/

    # Compile kernel

    # Clean kernel tree
    make -j${NUM_CPUS} ARCH=arm64 mrproper -C $BUILD_DIR/linux/

    # Configure the kernel with specific RPi 3 configuration
    make -j${NUM_CPUS} ARCH=arm64 CROSS_COMPILE=$ARCH64_ELF_CC bcmrpi3_defconfig -C $BUILD_DIR/linux/

    # Compile kernel generating the kernel image, the modules and the device trees
    make -j${NUM_CPUS} ARCH=arm64 CROSS_COMPILE=$ARCH64_ELF_CC Image modules dtbs -C $BUILD_DIR/linux/

    # Copy the device trees to the temporal file system
    make -j${NUM_CPUS} ARCH=arm64 CROSS_COMPILE=$ARCH64_ELF_CC INSTALL_MOD_PATH=$RPI_FILE_TREE/rootfs modules_install -C $BUILD_DIR/linux/

    # Copy kernel
    # Copy the kernel image
    cp workspace/build/linux/arch/arm64/boot/Image $RPI_FILE_TREE/boot/kernel8.img

    # Copy the specific device trees to the temporal file system
    cp workspace/build/linux/arch/arm64/boot/dts/broadcom/bcm2710-rpi-3-b.dtb $RPI_FILE_TREE/boot
    cp workspace/build/linux/arch/arm64/boot/dts/broadcom/bcm2837-rpi-3-b.dtb $RPI_FILE_TREE/boot

    # Copy the common device trees to the temporal file system
    mkdir $RPI_FILE_TREE/boot/overlays
    cp workspace/build/linux/arch/arm64/boot/dts/overlays/*.dtb* $RPI_FILE_TREE/boot/overlays
}

# Step 3
# In the third step we will end fitting the boot partition and configure the boot process
function step_3() {
    echo "[Step 3/$number_of_steps]: Copy the bootloader to the temporal file system and configure it"

    # Raspi specific firmware
    git clone --depth 1 -b stable https://github.com/raspberrypi/firmware/ $SOURCES_DIR/firmware

    # Copy bootloader
    cp workspace/sources/firmware/boot/bootcode.bin $RPI_FILE_TREE/boot
    cp workspace/sources/firmware/boot/fixup.dat $RPI_FILE_TREE/boot
    cp workspace/sources/firmware/boot/start.elf $RPI_FILE_TREE/boot

    # Create configuration files
    cat >$RPI_FILE_TREE/boot/config.txt <<"EOF"
# uncomment this if your display has a black border of unused pixels visible
# and your display can output without overscan
disable_overscan=1

# Enable audio (loads snd_bcm2835)
dtparam=audio=on

# Linux kernel to boot
kernel=kernel8.img

# Enable 64bits support
arm_64bit=1
EOF

    cat >$RPI_FILE_TREE/boot/cmdline.txt <<"EOF"
console=ttyAMA0,115200 console=tty1 root=PARTUUID=4dae6649-02 rootfstype=ext4 rootwait
EOF
}

# Step 4
# Compile simple init program and copy it to the file system
function step_4() {
    echo "[Step 4/$number_of_steps]: Compile simple init program and copy it to the temporal file system"

    # Create output directory
    mkdir $RPI_FILE_TREE_DIR/rootfs/sbin

    # Compile the binary as static because to keep it as simple as possible we wont include any
    # shared library (as glibc) in the final system
    ${ARCH64_LINUX_CC}g++ -static -o $RPI_FILE_TREE_DIR/rootfs/sbin/init init.cpp
}

#
# Validate input
#
first_step=$1
last_step=$2

## Number checker regular expresion
number_regular_expresion='^[0-9]+$'

## Asign default values
if [ "$first_step" = "" ]; then
    first_step=1
fi

if [ "$last_step" = "" ]; then
    last_step=$number_of_steps
fi

## Check if input is correct
if ! [[ $first_step =~ $number_regular_expresion ]]; then
    echo "error: First step must be a number" >&2
    exit 1
fi

if ! [[ $last_step =~ $number_regular_expresion ]]; then
    echo "error: Last step must be a number" >&2
    exit 1
fi

#
# Steps launcher
#
for actual_step in $(seq 1 $number_of_steps); do
    if ((($first_step <= $actual_step) && ($actual_step <= $last_step))); then
        step_$actual_step
    else
        echo "Step $actual_step have been omited"
    fi
done
