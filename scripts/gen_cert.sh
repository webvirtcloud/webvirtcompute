#!/usr/bin/env bash
set -e

openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes -subj "/C=EU/ST=Ukraine/L=Zaporozhye/O=hostwebvirt/CN=172.32.16.10"

exit 0
