#!/bin/bash
set -eux

VMNAME="$1"
PROJECT_DIR="/home/vagrant/project"
DATA_DIR="${PROJECT_DIR}/data/sessions/${VMNAME}"
VENV_DIR="/home/vagrant/.venvs/${VMNAME}"
PYTHON_BIN="/usr/bin/python3"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git screen curl build-essential
sudo apt install -y virtualbox-guest-dkms virtualbox-guest-utils
sudo modprobe vboxsf
sudo reboot

# Ensure directories and ownership
mkdir -p "${DATA_DIR}"
mkdir -p "$(dirname ${VENV_DIR})"
chown -R vagrant:vagrant "${PROJECT_DIR}" "${DATA_DIR}"

# Create per-VM venv
if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

# Activate venv and install requirements if present
source "${VENV_DIR}/bin/activate"
if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r "${PROJECT_DIR}/requirements.txt"
else
  pip install --upgrade pip
  pip install streamlit pandas plotly xlsxwriter openpyxl
fi
deactivate

# create per-instance env file that your honeypot can read
cat > "${PROJECT_DIR}/.honeypot_instance_env_${VMNAME}.sh" <<EOF
export HONEYPOT_INSTANCE_NAME=${VMNAME}
export HONEYPOT_OUTPUT_DIR=${DATA_DIR}
EOF
chown vagrant:vagrant "${PROJECT_DIR}/.honeypot_instance_env_${VMNAME}.sh"

# kill any old screen session, then launch honeypot in detached screen
SCREEN_NAME="honeypot_${VMNAME}"
RUN_CMD="source ${VENV_DIR}/bin/activate && cd ${PROJECT_DIR} && source ./.honeypot_instance_env_${VMNAME}.sh && python run_honeypot.py --outdir \"\$HONEYPOT_OUTPUT_DIR\" --instance ${VMNAME}"

# ensure old screen removed
su - vagrant -c "screen -S ${SCREEN_NAME} -X quit || true"
# start in new detached screen
su - vagrant -c "screen -dmS ${SCREEN_NAME} bash -lc '${RUN_CMD}'"

echo "Provision finished for ${VMNAME}. Honeypot screen: ${SCREEN_NAME}"