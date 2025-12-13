#!/bin/python3
import subprocess
from pathlib import Path
import os
import logging
import argparse
import shutil

# Environment variables set by dockerfile
GCC_ARM_BARE_METAL_PATH = os.environ['GCC_ARM_BARE_METAL_PATH']
GCC_ARM_LINUX_PATH = os.environ['GCC_ARM_LINUX_PATH']

# Dependencies
GIT_DEPENDENCIES = {
    "kernel": {
        "repo": "https://github.com/raspberrypi/linux",
        "branch": "rpi-5.4.y"
    },
    "bootloader": {
        "repo": "https://github.com/raspberrypi/rpi-firmware",
        "branch": "stable"
    }
}

#
# Download dependencies
#

def download_dependencies(dependencies_output_dir: Path):
    """Clone all repositories listed in dependencies."""
    for repo_name, repo_info in GIT_DEPENDENCIES.items():
        repo_url = repo_info['repo']
        branch = repo_info['branch']

        clone_path = dependencies_output_dir / repo_name

        assert (not clone_path.exists())

        print(f"Cloning {repo_name} from {repo_url}...")
        subprocess.run(['git', 'clone', '--depth', '1', repo_url,
                       clone_path, '--branch', branch], check=True)

#
# Build steps
#

def build_kernel(kernel_path: Path, output_path: Path, filesystem_boot_path: Path):
    """
    Compile kernel
    """
    logging.info("Compile kernel ... ")

    # Cross compiler path
    cross_compiler = os.path.join(GCC_ARM_BARE_METAL_PATH, "aarch64-none-elf-")

    # Clean kernel tree
    subprocess.run(["make", f"O={output_path}", "-j", str(os.cpu_count()), "ARCH=arm64",
                   f"CROSS_COMPILE={cross_compiler}", "mrproper", "-C", kernel_path], check=True, text=True)

    # Configure the kernel with specific RPi 3 configuration
    subprocess.run(["make", f"O={output_path}", "-j", str(os.cpu_count()), "ARCH=arm64",
                   f"CROSS_COMPILE={cross_compiler}", "bcmrpi3_defconfig", "-C", kernel_path], check=True, text=True)

    # Compile kernel generating the kernel image, the modules and the device trees
    subprocess.run(["make", f"O={output_path}", "-j", str(os.cpu_count()), "ARCH=arm64",
                   f"CROSS_COMPILE={cross_compiler}", "Image", "modules", "dtbs", "-C", kernel_path], check=True, text=True)

    # Copy the device trees to the temporal file system
    subprocess.run(["make", f"O={output_path}", "-j", str(os.cpu_count()), "ARCH=arm64",
                   f"CROSS_COMPILE={cross_compiler}", f"INSTALL_MOD_PATH={filesystem_boot_path}", "modules_install", "-C", kernel_path], check=True, text=True)


def copy_kernel_to_filesystem(kernel_path: Path, filesystem_boot_path: Path):
    """
    Copy kernel to boot filesystem
    """
    # Kernel image and board dtbs
    arch_arm64_boot_files_to_copy = \
        [(Path("Image"), Path("kernel8.img")),
         (Path("dts", "broadcom", "bcm2710-rpi-3-b.dtb"), Path("bcm2710-rpi-3-b.dtb")),
         (Path("dts", "broadcom", "bcm2837-rpi-3-b.dtb"), Path("bcm2837-rpi-3-b.dtb"))]
    files_to_copy = [(kernel_path / Path("arch", "arm64", "boot") / i, filesystem_boot_path / j)
                     for i, j in arch_arm64_boot_files_to_copy]

    # Make overlays folder on dst filesystem
    filesystem_overlay_path = filesystem_boot_path / "overlays"
    os.mkdir(filesystem_overlay_path)

    # Overlay dtbs
    kernel_build_overlay_path = kernel_path / \
        "arch" / "arm64" / "boot" / "dts" / "overlays"
    files_to_copy += [(src, filesystem_overlay_path / src.name)
                      for src in kernel_build_overlay_path.glob("*.dtb*")]

    # Copy files
    for src, dst in files_to_copy:
        shutil.copyfile(src, dst)


def clone_bootleader(source_path: Path) -> Path:
    """
    Clone bootloader and return path
    """
    logging.info("Clone bootloader")
    bootloader_path = source_path / "firmware"

    subprocess.run(["git", "clone", "--depth", "1", "-b", "stable", "https://github.com/raspberrypi/rpi-firmware",
                    bootloader_path], check=True, text=True)
    return bootloader_path


def copy_bootloader_to_filesystem(bootloader_path: Path, filesystem_boot_path: Path):
    """
    Copy bootloader to filesystem
    """
    files_to_copy = [Path("bootcode.bin"), Path(
        "fixup.dat"), Path("start.elf")]
    for src_name in files_to_copy:
        shutil.copyfile(bootloader_path / src_name,
                        filesystem_boot_path / src_name)


def copy_configuration_to_filesystem(filesystem_boot_path: Path):
    """
    Configuration to filesystem
    """
    # Configuration for bootloader
    bootloader_configuration = \
        "disable_overscan=1\n"\
        "dtparam=audio=on\n"\
        "kernel=kernel8.img\n"\
        "arm_64bit=1"
    with open(filesystem_boot_path / "config.txt", "w+", encoding="utf-8") as f:
        f.write(bootloader_configuration)

    # kernel params
    kernel_params = "console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait"
    with open(filesystem_boot_path / "cmdline.txt", "w+", encoding="utf-8") as f:
        f.write(kernel_params)


def build_simple_init_and_copy_to_filesystem(filesystem_root_folder_path: Path, src_dir: Path):
    """
    Build simple init program and copy to filesystem
    """
    sbin_path = filesystem_root_folder_path / "sbin"
    os.mkdir(sbin_path)
    cross_compile_gcc = os.path.join(
        GCC_ARM_LINUX_PATH, "aarch64-none-linux-gnu-g++")
    subprocess.run([cross_compile_gcc, "-static", "-o",
                   sbin_path/"init",  src_dir / "init.cpp"], check=True, text=True)


def make_image(filesystem_boot_path: Path, filesystem_root_folder_path: Path, out_image_path: Path):
    """
    Make booteable image
    """
    # Layout image
    partition_table_size_mb = 1
    boot_partition_size_mb = 128
    rootfs_partition_size_mb = 128

    filesystem_size_mb = boot_partition_size_mb + \
        rootfs_partition_size_mb + partition_table_size_mb

    # Create image file
    logging.info("Create image file ...")
    out_image_path.unlink(missing_ok=True)
    subprocess.run(
        ["fallocate", "-l", f"{filesystem_size_mb}MiB", out_image_path], check=True, text=True)

    # Allocate partitions
    logging.info("Allocate partitions ...")
    sfdisk_input = f",{boot_partition_size_mb}M,0x0c,*\n" \
        f",{rootfs_partition_size_mb}M,0x83,\n"
    subprocess.run(["sfdisk", out_image_path],
                   input=sfdisk_input, check=True, text=True)

    # Create root fs partition
    logging.info("Create rootfs partition ...")
    root_fs_image = Path(f"{out_image_path}.rootfs.img")
    root_fs_image.unlink(missing_ok=True)
    subprocess.run(["mke2fs",  "-L", "rootfs", "-N", "0", "-d", filesystem_root_folder_path, "-m", "5", "-r", "1",
                   "-t", "ext4", root_fs_image, f"{rootfs_partition_size_mb}M"], check=True, text=True)

    # Create boot partition
    logging.info("Create boot partition ...")
    boot_image = Path(f"{out_image_path}.boot.img")
    boot_image.unlink(missing_ok=True)
    subprocess.run(["mkfs.vfat", "-F", "16", "-v", "-C", boot_image, str(
        boot_partition_size_mb*1024), "-n" "boot"], check=True, text=True)
    subprocess.run(["mcopy", "-i", boot_image] +
                   list(filesystem_boot_path.glob("*")) + ["::"], check=True, text=True)

    # Copy partitions to image file
    logging.info("Copy partitions to image file ...")
    subprocess.run(["dd", f"if={boot_image}", f"of={out_image_path}", "bs=1024",
                   f"seek={partition_table_size_mb * 1024}"], check=True, text=True)
    subprocess.run(["dd", f"if={root_fs_image}", f"of={out_image_path}", "bs=1024",
                   f"seek={(boot_partition_size_mb + partition_table_size_mb) * 1024}"], check=True, text=True)

    # Delete boot and rootfs partitions
    root_fs_image.unlink()
    boot_image.unlink()


def make_qemu_launcher(filesystem_path: Path, out_image_path: Path):
    """
    Make executable script to launch image through QEMU
    """
    logging.info("Creating QEMU launcher ...")
    # We need to create an SD card file compatible with QEMU
    qemu_image_name = "basic_system.qemu.img"
    qemu_image_file = filesystem_path / qemu_image_name
    qemu_image_file.unlink(missing_ok=True)
    shutil.copyfile(out_image_path, qemu_image_file)
    assert (qemu_image_file.stat().st_size < (1024 * 1024 * 512))

    logging.info("Resizing image ...")
    subprocess.run(["qemu-img", "resize", qemu_image_file,
                   "512M"], check=True, text=True)

    # File launch content
    content = \
        "#!/bin/bash\n" \
        "DIR_NAME=$(dirname \"$0\")\n" \
        "qemu-system-aarch64 " \
        "-M raspi3b " \
        "-cpu cortex-a53 "  \
        "-append \"console=ttyAMA0,115200 console=tty0 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait\" " \
        "-dtb ${DIR_NAME}/boot/bcm2710-rpi-3-b.dtb -kernel ${DIR_NAME}/boot/kernel8.img " \
        "-sd ${DIR_NAME}/" + qemu_image_name + " " \
        "-m 1G -smp 4 -serial stdio -display none"

    qemu_launch_path = filesystem_path / "launch_qemu.sh"
    qemu_launch_path.unlink(missing_ok=True)
    with open(qemu_launch_path, "a", encoding="utf-8") as f:
        f.writelines(content)

    qemu_launch_path.chmod(0o700)


def build_system(workspace_name: str, skip_build_boot_partition: bool, skip_build_userspace: bool):
    """
    Run different build steps
    """
    # Configure logger
    logging.basicConfig(level=logging.INFO)

    logging.info("Current workspace name: %s", workspace_name)
    current_file_dir = Path(__file__).parent.absolute()
    workspace_folder_path = current_file_dir.parent / workspace_name

    # Download dependencies if not present
    dependencies_folder_path = workspace_folder_path / "dependencies"
    if not dependencies_folder_path.exists():
        dependencies_folder_path.mkdir(parents=True)
        download_dependencies(dependencies_folder_path)
    else:
        logging.info(
            "Dependencies folder %s already exists. Skipping download.", dependencies_folder_path)

    kernel_source_path = dependencies_folder_path / "kernel"
    bootloader_source_path = dependencies_folder_path / "bootloader"

    # Create workspace/build folder
    build_folder_path = workspace_folder_path / "build"
    os.makedirs(build_folder_path, exist_ok=True)

    # Create workspace/source folder
    source_folder_path = workspace_folder_path / "source"
    os.makedirs(source_folder_path, exist_ok=True)

    # Create workspace/filesystem folder
    filesystem_folder_path = workspace_folder_path / "filesystem"

    filesystem_boot_folder_path = filesystem_folder_path / "boot"
    os.makedirs(filesystem_boot_folder_path, exist_ok=True)

    filesystem_root_folder_path = filesystem_folder_path / "rootfs"
    os.makedirs(filesystem_root_folder_path, exist_ok=True)

    if not skip_build_boot_partition:
        # Build kernel
        kernel_output_path = workspace_folder_path / "build" / "kernel"
        build_kernel(kernel_source_path, kernel_output_path,
                     filesystem_root_folder_path)
        copy_kernel_to_filesystem(
            kernel_output_path, filesystem_boot_folder_path)

        # Copy bootloader
        copy_bootloader_to_filesystem(
            bootloader_source_path, filesystem_boot_folder_path)

        # Copy boot configuration
        copy_configuration_to_filesystem(filesystem_boot_folder_path)

    if not skip_build_userspace:
        # Build simple init
        src_dir = current_file_dir.parent / "src"
        build_simple_init_and_copy_to_filesystem(
            filesystem_root_folder_path, src_dir)

    # Make ISO image
    image_path = filesystem_folder_path / "basic_system.img"
    make_image(filesystem_boot_folder_path,
               filesystem_root_folder_path, image_path)

    # Create QEMU launcher script
    make_qemu_launcher(filesystem_folder_path, image_path)


def main():
    """
    Entry point
    """
    parser = argparse.ArgumentParser(
        description='Build simple distro')
    parser.add_argument('--workspace', type=str, default="workspace")
    parser.add_argument('--skip-build-boot',
                        action='store_true')
    parser.add_argument('--skip-build-rootfs',
                        action='store_true')
    args = parser.parse_args()

    # Create workspace folder
    workspace_name = args.workspace
    skip_build_boot_partition = args.skip_build_boot
    skip_build_userspace = args.skip_build_rootfs

    build_system(
        workspace_name=workspace_name,
        skip_build_boot_partition=skip_build_boot_partition,
        skip_build_userspace=skip_build_userspace
    )


if __name__ == "__main__":
    main()
