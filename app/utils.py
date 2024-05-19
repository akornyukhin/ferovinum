from datetime import datetime, timedelta
from app.schema import TransportRequest


def validate_request_data(data: TransportRequest):
    origin = data.origin
    destination = data.destination
    collectionTime = data.collectionTime

    # Check if origin and destination are valid
    if origin not in ["A", "B"] or destination not in ["A", "B"]:
        response = {"status": "ERROR",
                    "error": "Invalid origin or destination"}
        raise Exception(
            f'Invalid origin "{origin}" or destination "{destination}. Valid values are "A" or "B"')

    if origin == destination:
        response = {"status": "ERROR",
                    "error": "Origin and destination cannot be the same"}
        raise Exception("Origin and destination cannot be the same")

    try:
        datetime.strptime(collectionTime, "%d/%m/%Y %H:%M:%S")
    except Exception as e:
        raise Exception(str(e))

    collectionTime = datetime.strptime(
        collectionTime, "%d/%m/%Y %H:%M:%S") + timedelta(days=1)
    collectionTime = datetime(
        collectionTime.year, collectionTime.month, collectionTime.day, 9, 0, 0)
