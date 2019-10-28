// SPDX-Copyright: Copyright (c) 2019 Daniel Edgecumbe (esotericnonsense)
// SPDX-License-Identifier: AGPL-3.0-only
//
// This file is part of botfair.  botfair is free software: you can
// redistribute it and/or modify it under the terms of the GNU Affero General
// Public License as published by the Free Software Foundation, either version
// 3 of the License, or (at your option) any later version.
//
// botfair is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
// for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with botfair.  If not, see <http://www.gnu.org/licenses/>.

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

#[derive(Debug, Deserialize)]
pub struct RpcError {
    code: i32,
    // TODO: parse these. e.g. ANGX-0003 is exception 3
    message: String,
}

#[derive(Deserialize)]
pub struct RpcResponse<T> {
    jsonrpc: String,
    result: Option<T>,
    error: Option<RpcError>,
    id: String,
}

impl<T> RpcResponse<T> {
    pub fn into_inner(self) -> T {
        // TODO check these? do we care?
        let _ = self.jsonrpc;
        let _ = self.id;
        self.result.expect("unhandled API exception")
    }
}
