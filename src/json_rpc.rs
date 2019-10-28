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

use crate::generated_exceptions::errorCode;
use crate::result::{Error, Result};
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
    code: i32, // TODO are these ever meaningful?
    message: errorCode,
}

#[derive(Deserialize)]
pub struct RpcResponse<T> {
    jsonrpc: String,
    result: Option<T>,
    error: Option<RpcError>,
    id: String,
}

impl<T> RpcResponse<T> {
    // TODO: rustic way to perform this?
    pub fn into_inner(self) -> Result<T> {
        let _ = self.jsonrpc; // This should always be "2.0".
        let _ = self.id; // We could check this against the request.
        match (self.error, self.result) {
            (Some(rpc_error), _) => {
                Err(Error::APINGException(rpc_error.message))
            }
            (None, Some(result)) => Ok(result),
            (None, None) => Err(Error::JSONRPCError),
        }
    }
}
