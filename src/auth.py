from secrets import compare_digest
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()
token = '24636cd05baf2c0b50dff3488a64660b597beda48497112e3d6d9a0085329088'


def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = compare_digest(credentials.username, token)
    correct_password = compare_digest(credentials.password, token)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Basic"},
        )
    return token
