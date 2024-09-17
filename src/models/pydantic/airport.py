from pydantic import BaseModel

class Airport(BaseModel):
    icao: str
    iata: str
    name: str
    city: str
    subd: str
    country: str
    elevation: int
    lat: float
    lon: float
    tz: str
    lid: str