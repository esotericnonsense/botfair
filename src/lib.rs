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

#[macro_use]
extern crate log;

use reqwest::{Client, Identity};
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use std::sync::{Arc, RwLock};

// TODO this should not be public, re-export relevant parts
pub mod generated_api;
mod json_rpc;

use crate::json_rpc::{RpcRequest, RpcResponse};

#[derive(Debug)]
pub enum Error {
    Io(std::io::Error),
    Reqwest(reqwest::Error),
    BFLoginFailure(String),
    General(String),
    Other,
}

pub type Result<T> = std::result::Result<T, Error>;

impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Error::Io(e)
    }
}

impl From<reqwest::Error> for Error {
    fn from(e: reqwest::Error) -> Self {
        Error::Reqwest(e)
    }
}

#[derive(Debug, Serialize)]
struct LoginRequestForm {
    username: String,
    password: String,
}

#[derive(Debug, Deserialize)]
#[allow(non_snake_case)]
struct LoginResponse {
    sessionToken: Option<String>,
    loginStatus: String, // TODO enum this
}

pub struct BFCredentials {
    username: String,
    password: String,
    pfx: Vec<u8>,
    app_key: String,
}

impl BFCredentials {
    pub fn new(
        username: String,
        password: String,
        pfx_path: String,
        app_key: String,
    ) -> Result<Self> {
        let pfx = std::fs::read(pfx_path)?;
        Ok(BFCredentials {
            username,
            password,
            pfx,
            app_key,
        })
    }

    fn as_login_request_form(&self) -> LoginRequestForm {
        LoginRequestForm {
            username: self.username.clone(),
            password: self.password.clone(),
        }
    }
    fn pfx(&self) -> &Vec<u8> {
        &self.pfx
    }
    fn app_key(&self) -> &String {
        &self.app_key
    }
}

pub struct BFClient {
    client: reqwest::Client,
    session_token: Arc<RwLock<Option<String>>>,
    creds: BFCredentials,
    proxy_uri: Option<String>,
}

impl BFClient {
    pub fn new(
        creds: BFCredentials,
        proxy_uri: Option<String>,
    ) -> Result<Self> {
        let client: reqwest::Client = match &proxy_uri {
            Some(uri) => {
                let proxy = reqwest::Proxy::all(uri)?;
                Client::builder().proxy(proxy).build()?
            }
            None => reqwest::Client::new(),
        };
        Ok(BFClient {
            client,
            session_token: Arc::new(RwLock::new(None)),
            creds,
            proxy_uri,
        })
    }

    // TODO keepalive
    // https://identitysso.betfair.com/api/keepAliveo
    // Accept (mandatory)
    // Header that signals that the response should be returned as JSON	application/json
    // X-Authentication (mandatory)
    // Header that represents the session token that needs to be keep alive	Session Token
    // X-Application (optional)
    // Header the Application Key used by the customer to identify the product.	App Key
    // Response structure
    //
    //
    // {
    //   "token":"<token_passed_as_header>",
    //   "product":"product_passed_as_header",
    //   "status":"<status>",
    //   "error":"<error>"
    // }
    // Status values
    //
    //
    // SUCCESS
    // FAIL
    // Error values
    //
    //
    // INPUT_VALIDATION_ERROR
    // INTERNAL_ERROR
    // NO_SESSION

    // general notes
    // We would therefore recommend that all Betfair API request are sent with the ‘Accept-Encoding: gzip, deflate’ request header.
    // We recommend that Connection: keep-alive header is set for all requests to guarantee a persistent connection and therefore reducing latency. Please note: Idle keep-alive connection to the API endpoints are closed every 3 minutes.
    // You should ensure that you handle the INVALID_SESSION_TOKEN error within your code by creating a new session token via the API login method.

    fn req_internal<T1: Serialize, T2: DeserializeOwned>(
        &self,
        maybe_token: &Option<String>,
        rpc_request: &RpcRequest<T1>,
    ) -> Result<RpcResponse<T2>> {
        match maybe_token {
            None => Err(Error::General(
                "req_internal: must login first".to_owned(),
            )),
            Some(token) => {
                const JSONRPC_URI: &str =
                    "https://api.betfair.com/exchange/betting/json-rpc/v1";

                Ok(self
                    .client
                    .post(JSONRPC_URI)
                    .header("X-Application", self.creds.app_key())
                    .header("X-Authentication", token)
                    .json(&rpc_request)
                    .send()?
                    .json()
                    .unwrap())
            }
        }
    }

    /// Perform a request, logging in if necessary, fail if login
    pub fn req<T1: Serialize, T2: DeserializeOwned>(
        &self,
        req: RpcRequest<T1>,
    ) -> Result<RpcResponse<T2>> {
        // Initially acquire the token via a read lock

        trace!("Taking token read lock");
        let token_lock = self.session_token.read().unwrap();
        let mut token = token_lock.clone();
        drop(token_lock);
        trace!("Dropped token read lock");

        loop {
            // TODO: exponential backoff

            info!("Performing a request");
            match self.req_internal(&token, &req) {
                Ok(resp) => return Ok(resp),
                Err(_) => {
                    info!("Not logged in");
                    // Assume the only error possible is an auth error

                    trace!("Taking token write lock");
                    let mut token_lock = self.session_token.write().unwrap();

                    if *token_lock == token {
                        *token_lock = Some(self.login()?);
                    }
                    token = token_lock.clone();

                    drop(token_lock); // drops at end of scope but we log
                    trace!("Dropped token read lock");
                }
            }
        }
    }

    fn login(&self) -> Result<String> {
        const CERTLOGIN_URI: &str =
            "https://identitysso-cert.betfair.com/api/certlogin";

        let ident =
            Identity::from_pkcs12_der(self.creds.pfx().as_slice(), "")?;

        let client: reqwest::Client = match &(self.proxy_uri) {
            Some(uri) => {
                let proxy = reqwest::Proxy::all(uri)?;
                Client::builder().identity(ident).proxy(proxy).build()?
            }
            None => Client::builder().identity(ident).build()?,
        };

        let login_request_form = self.creds.as_login_request_form();

        info!("LoginRequest ...");
        let login_response: LoginResponse = client
            .post(CERTLOGIN_URI)
            .header(
                "X-Application",
                format!("schroedinger_{}", rand::random::<u128>()),
            )
            .form(&login_request_form)
            .send()?
            .json()?;

        info!("LoginResponse: {:?}", login_response.loginStatus);

        match login_response.sessionToken {
            Some(token) => Ok(token),
            None => Err(Error::BFLoginFailure(format!(
                "loginStatus: {}",
                login_response.loginStatus
            ))),
        }
    }
}
