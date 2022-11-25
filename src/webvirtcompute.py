#!/usr/bin/env python3

import os
import main
import uvicorn
from settings import HOST, PORT


if __name__ == "__main__":
    if "venv" in os.environ.get("_"):
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True, access_log=False)
    else:
        uvicorn.run("main:app", host=HOST, port=PORT, log_level="info")
