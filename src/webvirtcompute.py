#!/usr/bin/env python3

import os
import shutil
import uvicorn
from settings import HOST, PORT
from cert import gen_self_signed_cert


if __name__ == "__main__":
    try:
        key_file, cert_file = gen_self_signed_cert()
        uvicorn.run("main:app", host=HOST, port=PORT, ssl_keyfile=key_file, ssl_certfile=cert_file, log_level="info")
    finally:
        shutil.rmtree(os.path.dirname(key_file), ignore_errors=True)
