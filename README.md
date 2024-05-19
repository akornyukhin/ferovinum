# Take Home assignment

To run everything:

1. `pip install -r requirements.txt`
2. In one terminal run `python third_party_server/server.py`
3. In another terminal run `uvicorn app.main:app`
4. Use either Postman or CURL to access the endpoint "http://localhost:8000//request-transport"

For CURL:

```
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
```

For Postman request body:

```
{
    "clientId": "Samsung",
    "productId": "Apple",
    "quantity": 10,
    "origin": "A",
    "destination": "B",
    "collectionTime": "19/05/2024 7:01:43"
}
```
