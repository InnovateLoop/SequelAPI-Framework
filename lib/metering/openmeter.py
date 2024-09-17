import os
import uuid
import time
from fastapi import Request, Depends, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_dict
from openmeter import Client
import requests

openmeter_bearer_token = os.environ.get("OPENMETER_API_SECRET_TOKEN")
openmeter_client = Client(
    endpoint="https://openmeter.cloud",
    headers={
    "Accept": "application/json",
    "Authorization": f"Bearer {openmeter_bearer_token}",
    },
)

class CloudEventMetering(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        response = await call_next(request)

        duration = time.monotonic() - start_time

        if (response.status_code >= 200 and response.status_code < 300) and hasattr(request.state, 'user'):
            request_metering_event = CloudEvent(
                attributes={
                    "id": request.state.request_id,
                    "type": "api_request",
                    "source": "fastapi",
                    "subject": request.state.user.sub
                },
                data={
                    "duration": duration,
                    "method": request.method,
                    "path": request.scope['root_path'] + request.scope['route'].path,
                },
            )

            openmeter_client.ingest_events(to_dict(request_metering_event))

        return response

def has_sufficient_balance(feature: str, grants: int = 1):
    def has_balance_for_feature(request: Request):
        if hasattr(request.state, 'user'):
            response = requests.request(
                "GET",  
                f"https://openmeter.cloud/api/v1/subjects/{request.state.user.sub}/entitlements/{feature}/value", 
                headers={
                    'accept': 'application/json',
                    'Authorization': f'Bearer {openmeter_bearer_token}'
                }, data={}).json()
            
            if response["hasAccess"] and response["balance"] >= grants:
                return response
            else:
                raise HTTPException(status_code=429, detail="User does not have sufficient balance.")
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return Depends(has_balance_for_feature)