from datetime import datetime, timedelta
from app.schema import TransportRequest
import requests
import json
import os
import time
from dotenv import load_dotenv
load_dotenv()

base_url = os.environ.get(
    "THIRD_PARTY_SERVER_ENDPOINT") + ":" + os.environ.get("PORT")


class TransportJob():
    def __init__(
        self,
        transport_request_details: TransportRequest
    ):
        self.clientId = transport_request_details.clientId
        self.productId = transport_request_details.productId
        self.quantity = transport_request_details.quantity
        self.origin = transport_request_details.origin
        self.destination = transport_request_details.destination
        self.collectionTime = transport_request_details.collectionTime
        self.jobId = ""

    def negotiate_collection_time(self):
        collectionTime = datetime.strptime(
            self.collectionTime, "%d/%m/%Y %H:%M:%S") + timedelta(days=1)
        collectionTime = datetime(
            collectionTime.year, collectionTime.month, collectionTime.day, 9, 0, 0)
        while True:
            response = requests.post(
                base_url + "/carrier/request-job",
                json={
                    "clientId": self.clientId,
                    "productId": self.productId,
                    "quantity": self.quantity,
                    "origin": self.origin,
                    "destination": self.destination,
                    "collectionTime": collectionTime.isoformat()
                })

            if response.json()["status"] == "REJECT":
                collectionTime = collectionTime + timedelta(hours=1)
            else:
                response_data = response.json()
                return response_data["jobId"], response_data["collectionTime"]

    def release_stock(self):
        response = requests.post(
            base_url + f"/warehouse/{self.origin}/release",
            json={
                "productId": self.productId,
                "quantity": self.quantity,
                "collectionTime": self.collectionTime
            }
        )
        return response.json()

    def check_job_status(self):
        while True:
            response = requests.get(
                base_url + f"/carrier/job/{self.jobId}/status"
            )

            if response.json()["status"] == "RELEASED":
                return response.json()

            time.sleep(1)

    def check_product_status(self):
        while True:
            response = requests.get(
                base_url +
                f"/warehouse/{self.destination}/product/{self.productId}/status",
            )

            if response.json()["status"] == "LANDED":
                return response.json()

            time.sleep(1)

    def run_job(self):
        # Negotiating collection time
        print("Negotiating collection time")
        self.jobId, self.collectionTime = self.negotiate_collection_time()
        print(
            f"Collection time confirmed.\nThe collection time for {self.jobId} if {self.collectionTime}")

        # Writting a confirmation file
        file_name = f"collection-confirmation-{self.jobId}.json"
        with open(f"./data/{file_name}", "w") as file:
            json.dump({
                "productId": self.productId,
                "quantity": self.quantity,
                "collectionTime": self.collectionTime
            }, file, indent=4)

        # Releasing a product from the warehouse
        print(
            f"{self.jobId}: Releasing {self.quantity} of {self.productId} from warehouse {self.origin}")
        self.release_stock()
        print(
            f"{self.jobId}: {self.quantity} of {self.productId} were released from warehouse {self.origin}")

        # Checking the job status
        self.check_job_status()

        # Check product status
        print(f"{self.jobId}: Checking product landing status")
        self.check_product_status()
        print(
            f"{self.jobId}: {self.quantity} of {self.productId} landed in warehouse {self.destination}")

        # Writting a landing confirmation file
        file_name = f"landing-confirmation-{self.destination}-{self.productId}.json"
        with open(f"./data/{file_name}", "w") as file:
            json.dump({
                "quantity": self.quantity,
            }, file, indent=4)
