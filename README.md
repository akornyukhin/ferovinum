# Take Home assignment

To run everything:

1. Create a .env file and populate with the following
   `PORT=4000
THIRD_PARTY_SERVER_ENDPOINT=http://127.0.0.1`

2. `pip install -r requirements.txt`
3. In one terminal run `python third_party_server/server.py`
4. In another terminal run `uvicorn app.main:app`
5. Use either Postman or CURL to access the endpoint "http://localhost:8000//request-transport"

For CURL:
`
curl -X POST http://localhost:8000/request-transport \
 -H "Content-Type: application/json" \
 -d '{
"clientId": "Samsung",
"productId": "Apple",
"quantity": 10,
"origin": "A",
"destination": "B",
"collectionTime": "19/05/2024 7:01:43"
}'

For Postman request body:
`{
    "clientId": "Samsung",
    "productId": "Apple",
    "quantity": 10,
    "origin": "A",
    "destination": "B",
    "collectionTime": "19/05/2024 7:01:43"
}`
