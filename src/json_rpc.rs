use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct RpcRequest<T> {
    jsonrpc: String,
    method: String,
    params: T,
    id: String,
}

#[derive(Deserialize)]
pub struct RpcResponse<T> {
    jsonrpc: String,
    result: T,
    id: String,
}

impl<T> RpcRequest<T> {
    pub fn new(method: String, params: T) -> Self {
        let r: u128 = rand::random();
        RpcRequest::<T> {
            jsonrpc: "2.0".to_owned(),
            method,
            params,
            id: format!("{:x}", r),
        }
    }
}

// listEventTypes Request
// [
//     {
//         "jsonrpc": "2.0",
//         "method": "SportsAPING/v1.0/listEventTypes",
//         "params": {
//             "filter": {}
//         },
//         "id": 1
//     }
// ]
// listEventTypes Response
// [
//     {
//         "jsonrpc": "2.0",
//         "result": [
//             {
//                 "eventType": {
//                     "id": "468328",
//                     "name": "Handball"
//                 },
//                 "marketCount": 11
//             },
//             ... removed
//         ],
//         "id": 1
//     }
// ]
//
