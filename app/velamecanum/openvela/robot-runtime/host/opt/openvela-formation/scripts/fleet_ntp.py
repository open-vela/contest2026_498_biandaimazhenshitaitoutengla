#!/usr/bin/env python3
"""Minimal LAN NTP server so the robots share one ROS timestamp clock."""

import socket
import struct
import time

NTP_EPOCH = 2_208_988_800


def timestamp() -> bytes:
    now = time.time() + NTP_EPOCH
    seconds = int(now)
    fraction = int((now - seconds) * (1 << 32))
    return struct.pack("!II", seconds & 0xFFFFFFFF, fraction)


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("192.168.1.201", 123))
    while True:
        packet, sender = sock.recvfrom(512)
        if len(packet) < 48 or (packet[0] & 7) != 3:
            continue
        received = timestamp()
        version = (packet[0] >> 3) & 7
        response = bytearray(48)
        response[0] = (version << 3) | 4
        response[1] = 1
        response[2] = packet[2]
        response[3] = 0xEC  # precision 2^-20 seconds
        response[12:16] = b"LOCL"
        response[16:24] = received
        response[24:32] = packet[40:48]
        response[32:40] = received
        response[40:48] = timestamp()
        sock.sendto(response, sender)


if __name__ == "__main__":
    main()
