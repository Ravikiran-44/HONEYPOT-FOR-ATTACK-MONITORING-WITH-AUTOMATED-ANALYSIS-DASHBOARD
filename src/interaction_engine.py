def banner_for(service="ssh"):
    if service == "ssh": return "SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.10\n"
    if service == "http": return "HTTP/1.1 200 OK\nServer: Apache/2.4.18 (Ubuntu)\n\n"
    return "\n"

def fake_response_for(cmd):
    cmd = cmd.lower().strip()
    if cmd.startswith("uname"): return "Linux fakehost 4.15.0-99-generic\n"
    if "whoami" in cmd: return "root\n"
    return "Command executed (simulated)\n"
