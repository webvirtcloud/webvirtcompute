from fastapi import HTTPException


def raise_error_msg(msg):
    raise HTTPException(status_code=400, detail=json.dumps(str(msg)))
