#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $(uname -s) != Linux ]]; then
  echo 'Run this script inside the Ubuntu Linux VM.' >&2
  exit 1
fi
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch python3-venv python3-pip iputils-ping docker.io
sudo systemctl start openvswitch-switch docker
python3 -m venv --system-site-packages .venv-linux
.venv-linux/bin/python -m pip install -r requirements.txt
sudo docker build -f linux/Dockerfile.ryu -t qkd-ryu:local .
echo 'Setup finished. Follow linux/README.md for the two-terminal experiment.'
