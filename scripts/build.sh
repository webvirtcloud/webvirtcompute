#!/usr/bin/env bash
set -e

# Create virtualenv
if [[ ! -d /root/venv ]]; then
  python3 -m venv --system-site-package /root/.venv
fi

# Cleanup directory
cd /vagrant/src
if [[ -d dist || -d build ]]; then
  rm -rf dist build
fi

# Update pip
/root/.venv/bin/pip install -U pip wheel setuptools

# Install fastapi
/root/.venv/bin/pip install --no-use-pep517 --no-cache -r build.txt

echo "Creating hostvirtmgr binary..."
/root/.venv/bin/pyinstaller -p /src --hiddenimport main -F webvirtcompute.py

# Copy INI files
cp ../conf/webvirtcompute.* dist/

# Check release folder
if [[ ! -d ../release ]]; then
  mkdir ../release
fi

tar -czf ../release/webvirtcompute-rockylinux8-amd64.tar.gz --transform s/dist/webvirtcompute/ dist

echo ""
echo "Release is ready!"

exit 0
