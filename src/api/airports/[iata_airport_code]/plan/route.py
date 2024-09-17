from fastapi import APIRouter, Request
from models.pydantic.plan import Plan 
from sequel.metering.openmeter import has_sufficient_balance
from sequel.llm.openai import openai_client, OpenAIParsedResponse

router = APIRouter()

@router.post("", dependencies=[
    has_sufficient_balance(feature="plans_created", grants=1)
])
async def prompt_for_plan(iata_airport_code: str, request: Request) -> Plan:
    return OpenAIParsedResponse(
        openai_response=await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": "You are a travel planner. Provide a detailed 7-day itinerary."
                },
                {
                    "role": "user",
                    "content":  f"Generate a 7-day travel plan for a week near the airport with IATA code {iata_airport_code}. For each day, provide activities for morning, afternoon, evening, and night."
                }
            ],
            user=request.state.user.sub,
            response_format=Plan
        ),
       request=request
    )