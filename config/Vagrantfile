# Vagrantfile — creates a single honeypot VM (Ubuntu 22.04), host-only network
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "honeypot-vm"
  # create a private network: host-only (192.168.56.*)
  config.vm.network "private_network", ip: "192.168.56.50"
  # Forward public port 2222 → guest port 2222 (exposed to internet via router)
  config.vm.network "forwarded_port", guest: 2222, host: 2222, auto_correct: true
  config.vm.provider "virtualbox" do |vb|
    vb.name = "honeypot-vm"
    vb.memory = 4096
    vb.cpus = 2
  end
  # synced folder: map project to /home/vagrant/project
  config.vm.synced_folder ".", "/home/vagrant/project", type: "virtualbox"
  # provision: install python, pip, etc (simple)
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip git unzip
    # create venv if not exists
    cd /home/vagrant/project || exit 0
    if [ ! -d "venv" ]; then
      python3 -m venv venv
      /bin/bash -lc "source venv/bin/activate && pip install --upgrade pip"
    fi
  SHELL
  # Configure port forwarding for Streamlit (optional)
  config.vm.network "forwarded_port", guest: 8501, host: 8501, auto_correct: true
end
