"""JWT Handler"""

from typing import Optional, Annotated

import os
import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWTError, InvalidTokenError
from pydantic import BaseModel

class JWTCred(BaseModel):
    """Authenticated JWT User Credential"""

    azp: str
    iss: str

    exp: int
    iat: int
    nbf: int

    sub: str


class JWTBearer(HTTPBearer):
    """JWT Auth Bearer Handler for FastAPI Methods"""

    def __init__(self, jwks_url: str, credential_model: JWTCred = JWTCred):
        super().__init__()

        if jwks_url is None:
            jwks_url = os.environ['JWKS_URL']

        self.jwks_client = PyJWKClient(jwks_url)
        self.credential_model = credential_model

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=401, detail="Invalid authentication scheme."
                )

            try:
                token = credentials.credentials
                signing_key = self.jwks_client.get_signing_key_from_jwt(token)

                data = jwt.decode(token, signing_key.key, algorithms=[signing_key.algorithm_name])

                request.state.user = self.credential_model.model_validate(data)
                return request.state.user

            except InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid or expired token.")

            except PyJWTError:
                raise HTTPException(status_code=500, detail="Unable to authenticate.")
                    
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    def require_user(self):
        return Depends(self)

    def init(self):
        self.jwks_client.get_jwk_set(refresh=True)

    def get_account_id(self):
        def get_account_id_for_clerk(user: Annotated[JWTCred, Depends(self)]) -> str:
            return user.sub

        return get_account_id_for_clerk