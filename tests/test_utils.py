import pytest
from datetime import datetime, timedelta
from app.utils import validate_request_data
from app.schema import TransportRequest


def test_validate_request_data():
    valid_data = TransportRequest(
        clientId="Samsung",
        productId="Apple",
        quantity=10,
        origin="A",
        destination="B",
        collectionTime=(datetime.now() + timedelta(days=1)
                        ).strftime("%d/%m/%Y %H:%M:%S")
    )
    invalid_origin_data = TransportRequest(
        clientId="Samsung",
        productId="Apple",
        quantity=10,
        origin="C",
        destination="B",
        collectionTime=(datetime.now() + timedelta(days=1)
                        ).strftime("%d/%m/%Y %H:%M:%S")
    )
    invalid_destination_data = TransportRequest(
        clientId="Samsung",
        productId="Apple",
        quantity=10,
        origin="A",
        destination="A",
        collectionTime=(datetime.now() + timedelta(days=1)
                        ).strftime("%d/%m/%Y %H:%M:%S")
    )

    # Test with valid data
    validate_request_data(valid_data)

    # Test with invalid origin
    with pytest.raises(Exception) as e_info:
        validate_request_data(invalid_origin_data)

        assert str(
            e_info.value) == 'Invalid origin "C" or destination "B". Valid values are "A" or "B".'

    # Test with invalid destination
    with pytest.raises(Exception) as e_info:
        validate_request_data(invalid_destination_data)
        assert str(e_info.value) == "Origin and destination cannot be the same."
