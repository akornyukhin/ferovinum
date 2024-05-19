from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os
import random
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Mock database to store job and product information
jobs = {}
jobStatusQueries = {}
warehouses = {
    'A': {},
    'B': {},
}

timeWindows = {}


def generate_time_window():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    start_hour = 9 + random.randint(0, 7)  # Random hour between 9am and 4pm
    start_window = datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, start_hour)
    # Random hour between start hour + 1 and 5pm
    end_hour = start_window.hour + 1 + \
        random.randint(0, 16 - start_window.hour)
    end_window = datetime(tomorrow.year, tomorrow.month,
                          tomorrow.day, end_hour)
    return {'start': start_window, 'end': end_window}


def format_date(date):
    return date.strftime('%Y/%m/%d %H:%M:%S')

# Endpoint 1: POST carrier/request-job


@app.route('/carrier/request-job', methods=['POST'])
def request_job():
    data = request.json
    print('/carrier/request-job', data)
    clientId = data.get('clientId')
    productId = data.get('productId')
    quantity = data.get('quantity')
    origin = data.get('origin')
    destination = data.get('destination')
    collectionTime = data.get('collectionTime')

    # Check if origin and destination are valid
    if origin not in ['A', 'B'] or destination not in ['A', 'B']:
        response = {'status': "ERROR",
                    'error': "Invalid origin or destination"}
        print(f'Invalid origin "{origin}" or destination "{destination}"')
        return jsonify(response), 400

    if origin == destination:
        response = {'status': "ERROR",
                    'error': "Origin and destination cannot be the same"}
        print('Origin and destination cannot be the same')
        return jsonify(response), 400

    timeWindowKey = f'{productId}-{quantity}-{origin}-{destination}'
    timeWindow = timeWindows.get(timeWindowKey)

    if not timeWindow:
        timeWindow = generate_time_window()
        timeWindows[timeWindowKey] = timeWindow
    print(timeWindow)

    collectionDateTime = datetime.fromisoformat(collectionTime)
    if collectionDateTime < timeWindow['start'] or collectionDateTime > timeWindow['end']:
        response = {'status': "REJECT"}
        print(
            f'Collection time "{format_date(collectionDateTime)}" is not within the suitable time window')
        print(
            f'Suitable time window is between {format_date(timeWindow["start"])} and {format_date(timeWindow["end"])}')
        return jsonify(response)

    jobId = f'job_{os.urandom(7).hex()}'
    jobs[jobId] = {
        'clientId': clientId,
        'productId': productId,
        'quantity': quantity,
        'origin': origin,
        'destination': destination,
        'collectionTime': collectionTime
    }

    response = {'status': "ACCEPT", 'jobId': jobId,
                'collectionTime': collectionTime}
    print(f'Job request accepted with jobId: {jobId}')
    print('Current jobs:', ''.join(
        f'\n - {jobId}: {job["collectionTime"]}' for jobId, job in jobs.items()))
    return jsonify(response)

# Endpoint 2: GET carrier/job/<jobId>/status


@app.route('/carrier/job/<jobId>/status', methods=['GET'])
def job_status(jobId):
    job = jobs.get(jobId)
    if not job:
        response = {'status': "NOT FOUND"}
        print(f'Job with jobId "{jobId}" not found')
        return jsonify(response)

    jobQuery = jobStatusQueries.get(jobId)
    currentTime = datetime.now()

    if not jobQuery:
        generatedTime = currentTime + timedelta(seconds=random.randint(3, 6))
        jobStatusQueries[jobId] = {'timestamp': generatedTime, 'status': None}
        response = {'status': "PENDING"}
        print(
            f'Processing Job "{jobId}" for the first time. Job status is PENDING.')
        return jsonify(response)

    if jobQuery['status'] is not None:
        response = {'status': jobQuery['status']}
        print(
            f'Job "{jobId}" status is {jobQuery["status"]}, this status will not change.')
        return jsonify(response)

    if jobQuery['timestamp'] > currentTime:
        response = {'status': "PENDING"}
        print(f'Job "{jobId}" status is PENDING.')
        return jsonify(response)

    origin = job['origin']
    productId = job['productId']
    destination = job['destination']
    releaseMessage = warehouses[origin].get(productId)

    if releaseMessage:
        if releaseMessage['quantity'] == job['quantity'] and releaseMessage['collectionTime'] == job['collectionTime']:
            jobQuery['status'] = "RELEASED"
            response = {'status': "RELEASED"}
            landingTime = currentTime + \
                timedelta(seconds=random.randint(3, 10))
            warehouses[destination][productId] = {
                'landingTime': landingTime, 'quantity': job['quantity']}
            print(f'Job "{jobId}" status is RELEASED.')
            filename = f'./data/expected-collection-confirmation-{jobId}.json'
            with open(filename, 'w') as f:
                json.dump(
                    {'productId': productId, 'quantity': job['quantity'], 'collectionTime': job['collectionTime']}, f, indent=2)
            print(f'Expected collection confirmation saved to {filename}')
            return jsonify(response)
        else:
            print(
                f'Collection failed, quantity or collectionTime does not match, expected: {releaseMessage["quantity"]}, {releaseMessage["collectionTime"]}, got: {job["quantity"]}, {job["collectionTime"]}')

    jobQuery['status'] = "COLLECTION FAILED"
    response = {'status': "COLLECTION FAILED"}
    print(f'Job "{jobId}" status is COLLECTION FAILED.')
    return jsonify(response)

# Endpoint 3: POST warehouse/<warehouseId>/release


@app.route('/warehouse/<warehouseId>/release', methods=['POST'])
def warehouse_release(warehouseId):
    data = request.json
    print(f'/warehouse/{warehouseId}/release', data)
    if warehouseId not in ['A', 'B']:
        response = {'status': "ERROR", 'error': "Invalid warehouse ID"}
        print(f'Invalid warehouse ID "{warehouseId}"')
        return jsonify(response), 400

    productId = data.get('productId')
    quantity = data.get('quantity')
    collectionTime = data.get('collectionTime')

    warehouses[warehouseId][productId] = {
        'quantity': quantity, 'collectionTime': collectionTime}
    response = {'status': "SUCCESS"}
    print(f'Product "{productId}" released from warehouse "{warehouseId}"')
    return jsonify(response)

# Endpoint 4: GET warehouse/<warehouseId>/product/<productId>/status


@app.route('/warehouse/<warehouseId>/product/<productId>/status', methods=['GET'])
def product_status(warehouseId, productId):
    if warehouseId not in ['A', 'B']:
        response = {'status': "ERROR", 'error': "Invalid warehouse ID"}
        print(f'Invalid warehouse ID "{warehouseId}"')
        return jsonify(response), 400

    landingEntry = warehouses[warehouseId].get(productId)
    if not landingEntry:
        response = {'status': "NOT FOUND"}
        print(f'Product "{productId}" not found at warehouse "{warehouseId}"')
        return jsonify(response)

    currentTime = datetime.now()
    if landingEntry.get('landingTime', currentTime) < currentTime:
        response = {'status': "LANDED"}
        print(f'Product "{productId}" at warehouse "{warehouseId}" has LANDED')
        filename = f'./data/expected-landing-confirmation-{warehouseId}-{productId}.json'
        with open(filename, 'w') as f:
            json.dump({'quantity': landingEntry['quantity']}, f, indent=2)
        print(f'Expected landing confirmation saved to {filename}')
    else:
        response = {'status': "NOT LANDED"}
        print(
            f'Product "{productId}" at warehouse "{warehouseId}" has NOT LANDED')

    return jsonify(response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4001))
    print(f'3rd Party Server is running on port {port}')
    app.run(port=port)
