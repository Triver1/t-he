#!/usr/bin/env python3
"""Flashes every Tot-HE-m half on USB without touching it: asks each half its side over VIA's raw HID channel,
restarts it into the UF2 bootloader (VIA's id_bootloader_jump, handled in he_config.c) and copies the matching
image onto the RPI-RP2 drive. Needs the VIA firmware already on the half, read-write access to its hidraw device
(udev rule for 746d:7e57) and udisksctl to mount the drive.
usage: flash.py [image prefix]   (default uf2/tot_he_m_via, giving tot_he_m_via_left.uf2 and _right.uf2)
"""
import glob
import os
import select
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'uf2', 'tot_he_m_via')
VID_PID = '746D:7E57'
ID_CUSTOM_GET_VALUE, ID_BOOTLOADER_JUMP, ID_HE_SIDE = 0x08, 0x0B, 8


def via_devices():
    """hidraw nodes of the VIA interface (usage page 0xFF60) of every half on USB"""
    out = []
    for p in glob.glob('/sys/class/hidraw/*'):
        if VID_PID in os.path.realpath(p) and b'\x06\x60\xff' in open(p + '/device/report_descriptor', 'rb').read():
            out.append('/dev/' + os.path.basename(p))
    return out


def command(fd, *data):
    os.write(fd, bytes([0]) + bytes(data) + bytes(32 - len(data)))
    if not select.select([fd], [], [], 1)[0]:
        return None
    return os.read(fd, 32)


def bootloader_drive(timeout):
    end = time.time() + timeout
    while time.time() < end:
        for line in subprocess.run(['lsblk', '-lno', 'NAME,LABEL'], capture_output=True, text=True).stdout.splitlines():
            name, _, label = line.partition(' ')
            if label.strip() == 'RPI-RP2':
                return '/dev/' + name
        time.sleep(0.2)
    return None


def side_of(dev):
    """'left' or 'right' as the half reports it, None for firmware without the side query"""
    try:
        fd = os.open(dev, os.O_RDWR)
    except OSError:
        return None
    reply = command(fd, ID_CUSTOM_GET_VALUE, 0, ID_HE_SIDE)
    os.close(fd)
    if not reply or reply[0] == 0xFF:
        return None
    return 'left' if reply[3] else 'right'


def flash(dev, side):
    image = f'{PREFIX}_{side}.uf2'
    print(f'{dev}: {side} half, restarting into the bootloader')
    fd = os.open(dev, os.O_RDWR)
    os.write(fd, bytes([0, ID_BOOTLOADER_JUMP]) + bytes(31))
    os.close(fd)
    drive = bootloader_drive(10)
    if not drive:
        sys.exit(f'{dev}: the bootloader drive did not appear')
    subprocess.run(['udisksctl', 'mount', '-b', drive], capture_output=True)
    mount = subprocess.run(['findmnt', '-no', 'TARGET', drive], capture_output=True, text=True).stdout.strip()
    shutil.copy(image, mount)
    os.sync()
    print(f'{side} half: flashed {os.path.basename(image)}')
    time.sleep(3)   # let it boot and enumerate before looking for the next half


# one half at a time, looking again after each, since a flashed half comes back as a new device
done = set()
while True:
    todo = [(d, s) for d in via_devices() for s in [side_of(d)] if s not in done]
    if not todo:
        break
    dev, side = todo[0]
    if side is None:
        sys.exit(f'{dev}: no side reply; flash this half once with the BOOT button (older firmware)')
    flash(dev, side)
    done.add(side)
if not done:
    sys.exit('no Tot-HE-m half with VIA firmware found on USB')
