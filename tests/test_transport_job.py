import pytest
from app.transport_job import TransportJob
from app.schema import TransportRequest
from datetime import datetime, timedelta
from requests import Response
import re
import json


def process_string_to_jsons(string):
    jsons = re.findall(
        r'{\s*"(?:\w+|\\")+"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+(?:\.\d+)?)\s*(?:,\s*"(?:\w+|\\")+"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+(?:\.\d+)?)\s*)*}', string)
    return [json.loads(j) for j in jsons]


def mock_time_negotionation_response_change():
    calls = 0

    def side_effect(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 4:
            response = Response()
            response.status_code = 200
            response._content = b'{"status": "ACCEPT", "jobId": "job123", "collectionTime": "2021-10-10T09:00:00.000Z"}'
            return response
        response = Response()
        response.status_code = 200
        response._content = b'{"status": "REJECT"}'
        return response
    return side_effect


def mock_job_status_response_change():
    calls = 0

    def side_effect(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 4:
            response = Response()
            response.status_code = 200
            response._content = b'{"status": "RELEASED"}'
            return response
        response = Response()
        response.status_code = 200
        response._content = b'{"status": "PENDING"}'
        return response
    return side_effect


def mock_product_status_response_change():
    calls = 0

    def side_effect(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 4:
            response = Response()
            response.status_code = 200
            response._content = b'{"status": "LANDED"}'
            return response
        response = Response()
        response.status_code = 200
        response._content = b'{"status": "NOT LANDED"}'
        return response
    return side_effect


@pytest.fixture
def transport_request_details():
    # Create a sample transport request object for testing
    return TransportRequest(
        clientId="Samsung",
        productId="Apple",
        quantity=10,
        origin="A",
        destination="B",
        collectionTime=(datetime.now() + timedelta(days=1)
                        ).strftime("%d/%m/%Y %H:%M:%S")
    )


def test_negotiate_collection_time(transport_request_details, mocker):
    # Create an instance of TransportJob with the transport request details
    transport_job = TransportJob(transport_request_details)

    mocker.patch("requests.post",
                 side_effect=mock_time_negotionation_response_change())

    # Call the negotiate_collection_time method
    job_id, collection_time = transport_job.negotiate_collection_time()

    assert job_id == "job123"
    assert collection_time == "2021-10-10T09:00:00.000Z"


def test_release_stock(transport_request_details, mocker):
    # Create an instance of TransportJob with the transport request details
    transport_job = TransportJob(transport_request_details)

    # Call the release_stock method
    response = Response()
    response.status_code = 200
    response._content = b'{"status": "SUCCESS"}'
    requests_post_mock = mocker.patch("requests.post", return_value=response)
    response = transport_job.release_stock()

    assert response["status"] == "SUCCESS"


def test_check_job_status(transport_request_details, mocker):
    # Create an instance of TransportJob with the transport request details
    transport_job = TransportJob(transport_request_details)

    mocker.patch("requests.get",
                 side_effect=mock_job_status_response_change())
    # Call the check_job_status method
    response = transport_job.check_job_status()

    assert response["status"] == "RELEASED"


def test_check_product_status(transport_request_details, mocker):
    # Create an instance of TransportJob with the transport request details
    transport_job = TransportJob(transport_request_details)

    mocker.patch("requests.get",
                 side_effect=mock_product_status_response_change())

    # Call the check_product_status method
    response = transport_job.check_product_status()

    assert response["status"] == "LANDED"


def test_run_job(transport_request_details, monkeypatch, mocker):
    # Create an instance of TransportJob with the transport request details
    transport_job = TransportJob(transport_request_details)

    monkeypatch.setattr(TransportJob, "negotiate_collection_time", lambda x: (
        ["job123", "2021-10-10T15:00:00.000Z"]))
    monkeypatch.setattr(TransportJob, "release_stock",
                        lambda x: {"status": "SUCCESS"})
    monkeypatch.setattr(TransportJob, "check_job_status",
                        lambda x: {"status": "RELEASED"})
    monkeypatch.setattr(TransportJob, "check_product_status",
                        lambda x: {"status": "LANDED"})

    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    # Call the run_job method
    transport_job.run_job()

    mock_open_args = mock_open.call_args_list
    assert mock_open.call_count == 2
    assert mock_open_args[0].args == (
        "./data/collection-confirmation-job123.json", "w")
    assert mock_open_args[1].args == (
        "./data/landing-confirmation-B-Apple.json", "w")
    transport_job_dict = transport_job.__dict__
    assert transport_job_dict["jobId"] == "job123"
    assert transport_job_dict["collectionTime"] == "2021-10-10T15:00:00.000Z"
    assert transport_job_dict["origin"] == "A"
    assert transport_job_dict["destination"] == "B"
    assert transport_job_dict["productId"] == "Apple"
    assert transport_job_dict["quantity"] == 10
    assert transport_job_dict["clientId"] == "Samsung"

    written_data = ''.join(call.args[0]
                           for call in mock_open().write.call_args_list)
    written_data = process_string_to_jsons(written_data)
    assert written_data[0] == {
        "productId": "Apple", "quantity": 10, "collectionTime": "2021-10-10T15:00:00.000Z"}
    assert written_data[1] == {"quantity": 10}
