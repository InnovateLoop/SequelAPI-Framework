from fastapi import APIRouter
import airportsdata
from models.pydantic.airport import Airport

router = APIRouter()
airports = airportsdata.load('IATA')

@router.get("")
async def get_airport(iata_airport_code: str) -> Airport:
    return airports[iata_airport_code.upper()]