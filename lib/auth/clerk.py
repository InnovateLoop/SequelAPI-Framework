"""Clerk JWT Handler"""

import os
from typing import Optional, List, Annotated
from fastapi import Depends
from sequel.auth.jwks import JWTBearer, JWTCred
from pydantic import BaseModel

class ClerkJWTActor(BaseModel):
    """JWT Actor (if impersonating user)"""

    iss: str
    sid: str
    sub: str


class ClerkJWTCred(JWTCred):
    """Authenticated JWT User Credential"""

    azp: str
    iss: str

    exp: int
    iat: int
    nbf: int

    sid: str
    sub: str

    org_id: Optional[str] = None
    org_role: Optional[str] = None
    org_slug: Optional[str] = None
    org_permissions: Optional[List[str]] = None

    act: Optional[ClerkJWTActor] = None

class ClerkBearerAuthProvider(JWTBearer):
    """Clerk Auth Bearer Handler for FastAPI Methods"""

    def __init__(self, clerk_public_url: str = None):
        if clerk_public_url is None:
            clerk_public_url = os.environ['CLERK_PUBLIC_URL']
        
        super().__init__(jwks_url=f"{clerk_public_url}/.well-known/jwks.json", credential_model=ClerkJWTCred)
  
    def get_account_id(self):
        def get_account_id_for_clerk(user: Annotated[ClerkJWTCred, Depends(self)]) -> str:
            if user.org_id:
                return user.org_id

            return user.sub

        return get_account_id_for_clerk