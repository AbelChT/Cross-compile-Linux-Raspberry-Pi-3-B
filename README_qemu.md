__Work in progress__

First of all, create a 2 GB file that will be used as hard drive for QEMU.

```bash
VIRTUAL_DRIVE_NAME=virtual_drive_name.img
dd if=/dev/zero of=${VIRTUAL_DRIVE_NAME} bs=1k count=2000000
```

Create a partition in the virtual drive
```bash
parted -a optimal -s ${VIRTUAL_DRIVE_NAME} mklabel msdos mkpart primary fat32 4194kB 250MiB mkpart primary ext4 250MiB 100% set 2 lba off 
```

Mount the virtual drive as a loop device
```bash
sudo losetup -P /dev/loop0 ${VIRTUAL_DRIVE_NAME}
``` 

Format the partitions in the virtual drive
```bash
sudo mkfs.vfat /dev/loop0p1
```

```bash
sudo mkfs.ext4 /dev/loop0p2
```

Umount the virtual drive from the loop device
```bash
sudo losetup -d /dev/loop0
``` 