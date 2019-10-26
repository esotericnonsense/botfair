use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct RpcRequest<T> {
    jsonrpc: String,
    method: String,
    params: T,
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

#[derive(Deserialize)]
pub struct RpcResponse<T> {
    jsonrpc: String,
    result: T,
    id: String,
}

impl<T> RpcResponse<T> {
    pub fn into_inner(self) -> T {
        // TODO check these? do we care?
        let _ = self.jsonrpc;
        let _ = self.id;
        self.result
    }
}
