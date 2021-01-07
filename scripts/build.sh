#!/usr/bin/env bash
set -e

# Create virtualenv
python3 -m venv --system-site-package /root/venv

# Update pip
/root/venv/bin/pip install -U pip

# Install fastapi
/root/venv/bin/pip install pyinstaller fastapi uvicorn

# Cleanup directory
cd /vagrant/src
if [[ -d dist || -d build ]]; then
  rm -rf dist build
fi

echo "Creating hostvirtmgr binary..."
/root/venv/bin/pyinstaller -y --clean hostvirtmgr.spec

# Copy INI files
cp ../conf/hostvirtmgr.ini dist/

# Check release folder
if [[ ! -d ../release ]]; then
  mkdir ../release
fi

tar -czf ../release/hostvirtmgr-centos8-amd64.tar.gz --transform s/dist/hostvirtmgr/ dist

echo ""
echo "Release is ready!"
