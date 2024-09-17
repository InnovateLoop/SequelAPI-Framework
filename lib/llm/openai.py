import os, typing
from fastapi import Request
from fastapi.responses import JSONResponse

from cloudevents.http import CloudEvent
from cloudevents.conversion import to_dict
from sequel.metering.openmeter import openmeter_client
from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletion
from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTask

openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class OpenAIParsedResponse(JSONResponse):
    def __init__(
        self,
        openai_response: ParsedChatCompletion,
        request: Request,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        openai_metering_event = CloudEvent(
            attributes={
                "id": openai_response.id,
                "type": "chat_completion",
                "source": "openai",
                "subject": request.state.user.sub
            },
            data={
                "completion_tokens": openai_response.usage.completion_tokens,
                "reasoning_tokens": openai_response.usage.completion_tokens_details.reasoning_tokens,
                "prompt_tokens": openai_response.usage.prompt_tokens,
                "total_tokens": openai_response.usage.total_tokens,
                "model": openai_response.model,
                "platform": "openai",
                "request_id": request.state.request_id
            },
        )

        openmeter_client.ingest_events(to_dict(openai_metering_event))

        super().__init__(
            jsonable_encoder(openai_response.choices[0].message.parsed),
            status_code,
            headers,
            media_type,
            background,
        )