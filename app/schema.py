from pydantic import BaseModel, field_validator
from datetime import datetime


class TransportRequest(BaseModel):
    clientId: str
    productId: str
    quantity: int
    origin: str
    destination: str
    collectionTime: str
