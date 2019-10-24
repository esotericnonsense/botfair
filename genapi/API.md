JSON-RPC docs

You can POST a request to the API using JSON-RPC at
https://api.betfair.com/exchange/betting/json-rpc/v1

Headers:
X-Application: appkey
X-Authentication: session_token
Content-Type: application/json

listEventTypes Request
[
    {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listEventTypes",
        "params": {
            "filter": {}
        },
        "id": 1
    }
]
listEventTypes Response
[
    {
        "jsonrpc": "2.0",
        "result": [
            {
                "eventType": {
                    "id": "468328",
                    "name": "Handball"
                },
                "marketCount": 11
            },
            ... removed
        ],
        "id": 1
    }
]
