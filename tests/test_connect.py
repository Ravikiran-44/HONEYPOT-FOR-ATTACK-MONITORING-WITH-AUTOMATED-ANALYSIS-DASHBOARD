# -*- coding: utf-8 -*-
import socket

s = socket.socket()
s.settimeout(8)
try:
    s.connect(("127.0.0.1", 2222))
    banner = s.recv(4096).decode(errors="ignore")
    print("BANNER:", banner)
except Exception as e:
    print("CONNECT ERROR:", repr(e))
finally:
    s.close()
