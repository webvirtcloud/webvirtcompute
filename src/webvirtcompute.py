#!/usr/bin/env python3

import uvicorn
from settings import HOST, PORT
from cert import gen_self_signed_cert


if __name__ == "__main__":
    key_file, cert_file = gen_self_signed_cert()
    uvicorn.run("main:app", host=HOST, port=PORT, ssl_keyfile=key_file, ssl_certfile=cert_file, log_level="info")
