import pytest
from starlette.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.schema import TransportRequest

client = TestClient(app)


def test_request_transport(mocker):
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

    mocker.patch(
        "app.main.run_transport_job", return_value=None)
    mocked_background_task = mocker.patch(
        "app.main.BackgroundTasks.add_task", return_value=None)
    # Test with valid data
    response = client.post("/request-transport", json=valid_data.model_dump())
    assert response.status_code == 200
    assert response.json() == {"message": "Transportation requested"}
    assert mocked_background_task.call_count == 1
    assert mocked_background_task.call_args_list[0][0][1] == valid_data

    # Test with invalid origin
    response = client.post("/request-transport",
                           json=invalid_origin_data.model_dump())
    assert response.status_code == 400
    assert response.json() == {'detail': {
        'status': 'ERROR', 'error_message': 'Invalid origin "C" or destination "B". Valid values are "A" or "B".'}}

    # Test with invalid destination
    response = client.post("/request-transport",
                           json=invalid_destination_data.model_dump())
    assert response.status_code == 400
    assert response.json() == {"detail": {
        "status": "ERROR", "error_message": "Origin and destination cannot be the same."}}
