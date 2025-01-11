from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
import typing as t
import os
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key to encode and decode JWT tokens
SECRET_KEY = os.getenv("SECRET_KEY", "BidsInfoGlobalSecret")
ALGORITHM = "HS256"
get_bearer_token = HTTPBearer(auto_error=False)

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_access_token(jwt_token: str) -> bool:
    try:
        print(jwt_token)
        decoded_jwt = jwt.decode(
            jwt_token, SECRET_KEY,algorithms=[ALGORITHM])
        return {'verified': True, 'user': decoded_jwt}
    except (ExpiredSignatureError, Exception, InvalidSignatureError) as e:
        print(e)
        return {'verified': False, 'email': ''}
    
def get_current_user(auth: t.Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),) -> str:
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Unauthenticated User, Please login first.",
                "data": None,
            },

            
        )
    
    verification = verify_access_token(auth.credentials)
    if not verification['verified']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Unauthenticated User, Please login first.",
                "data": None,
            },
        )
  
    return {'token': auth.credentials, 'user': verification['user']}


