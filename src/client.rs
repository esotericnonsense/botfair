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
use crate::json_rpc::{RpcRequest, RpcResponse};
use crate::result::{Error, Result};
use reqwest::{Client, Identity};
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use std::sync::{mpsc, Arc, RwLock};
use std::thread;
use std::time::Duration;

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

/// A container for the essential credentials required for the Betfair APING.
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

/// A thread-safe client with automatic login implementing all methods of the
/// Betfair SportsAPING.
///
/// [`BFClient`](BFClient) implements Sync and so can safely be wrapped in an
/// Arc for multithreaded use with the same session token.
pub struct BFClient {
    client: reqwest::Client,
    destructor: mpsc::SyncSender<()>,
    session_token: Arc<RwLock<Option<String>>>,
    creds: BFCredentials,
    proxy_uri: Option<String>,
}

impl Drop for BFClient {
    fn drop(&mut self) {
        trace!("client: destructor triggered; signalling keepalive thread");
        self.destructor
            .send(())
            .expect("unable to signal keepalive thread");
    }
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

        let session_token = Arc::new(RwLock::new(None));

        let destructor = {
            let session_token = session_token.clone();
            let proxy_uri = proxy_uri.clone();
            let (tx, rx) = mpsc::sync_channel(0); // rendezvous channel
            thread::spawn(|| {
                Self::keepalive_thread(session_token, proxy_uri, rx)
            });
            tx
        };

        Ok(BFClient {
            client,
            destructor,
            session_token,
            creds,
            proxy_uri,
        })
    }

    /// This function is run once per BFClient as a thread. It ensures that the
    /// correct keepalive requests are made to the Betfair API such that the
    /// token does not expire.
    ///
    /// Note that it does not automatically re-login on expiry; for that to
    /// occur, a request must explicitly be made.
    ///
    /// In the future this could be implemented, which would reduce the latency
    /// of the first call after a (very) long spell of nothing, the so-called
    /// 'cold start problem'.
    fn keepalive_thread(
        session_token: Arc<RwLock<Option<String>>>,
        proxy_uri: Option<String>,
        rx: mpsc::Receiver<()>,
    ) {
        trace!("keepalive: thread spawned");
        let mut expired_token: Option<String> = None;
        loop {
            match rx.recv_timeout(Duration::from_millis(60000)) {
                Ok(_) => {
                    warn!("keepalive: destructor signal caught, exiting");
                    break;
                }
                Err(_) => {
                    let maybe_token: Option<String> = session_token
                        .read()
                        .expect("keepalive: could not lock session token")
                        .clone();

                    if maybe_token.is_some() && maybe_token == expired_token {
                        // TODO: login instead
                        warn!("keepalive: skipping, as token is expired");
                    }

                    match maybe_token {
                        None => {
                            debug!("keepalive: skipping, as no token");
                        }
                        Some(token) => {
                            debug!("keepalive: attempting");
                            match keepalive(&token, &proxy_uri) {
                                Ok(()) => {
                                    debug!("keepalive: successful");
                                }
                                Err(e) => {
                                    info!("keepalive failed: {:?}", e);
                                    // TODO: login instead
                                    expired_token = Some(token);
                                }
                            };
                        }
                    }
                }
            };
        }
    }

    fn req_internal<T1: Serialize, T2: DeserializeOwned>(
        &self,
        maybe_token: &Option<String>,
        rpc_request: &RpcRequest<T1>,
    ) -> Result<T2> {
        let token = match maybe_token {
            Some(x) => x,
            None => return Err(Error::SessionTokenNotPresent),
        };

        const JSONRPC_URI: &str =
            "https://api.betfair.com/exchange/betting/json-rpc/v1";

        trace!("Performing a query to the JSON-RPC api");

        // Attempt request
        let mut http_response: reqwest::Response = {
            let maybe_http_response = self
                .client
                .post(JSONRPC_URI)
                .header("X-Application", self.creds.app_key())
                .header("X-Authentication", token)
                .json(&rpc_request)
                .send();

            match maybe_http_response {
                Ok(x) => x,
                Err(e) => {
                    match e
                        .get_ref()
                        .and_then(|f| f.downcast_ref::<http::Error>())
                        .and_then(|g| {
                            Some(g.is::<http::header::InvalidHeaderValue>())
                        }) {
                        Some(true) => {
                            // This error occurs if you pass a random
                            //   string in the authentication header.
                            debug!("req_internal: InvalidHeaderValue");
                            return Err(Error::SessionTokenInvalid);
                        }
                        _ => {
                            error!("req_internal: request error {}", e);
                            return Err(Error::Reqwest(e));
                        }
                    }
                }
            }
        };

        // Attempt to deserialize
        let rpc_response: RpcResponse<T2> = match http_response.json() {
            Ok(x) => x,
            Err(e) => {
                error!("req_internal: deserialization error {}", e);
                return Err(Error::Reqwest(e));
            }
        };

        match rpc_response.into_inner() {
            Ok(x) => Ok(x),
            Err(Error::APINGException(code)) => match code {
                errorCode::INVALID_SESSION_INFORMATION
                | errorCode::NO_SESSION => Err(Error::SessionTokenInvalid),
                e => {
                    error!("req_internal: API error {:?}", e);
                    Err(Error::APINGException(e))
                }
            },
            Err(Error::JSONRPCError) => {
                error!("req_internal: no result or error?");
                Err(Error::JSONRPCError)
            }
            Err(_) => {
                unreachable!();
            }
        }
    }

    pub(super) fn req<T1: Serialize, T2: DeserializeOwned>(
        &self,
        req: RpcRequest<T1>,
    ) -> Result<T2> {
        // Initially acquire the token via a read lock

        trace!("req: taking token read lock");
        let token_lock = self.session_token.read().unwrap();
        let mut token = token_lock.clone();
        drop(token_lock);
        trace!("req: dropped token read lock");

        loop {
            debug!("req: attempting request");
            match self.req_internal(&token, &req) {
                Ok(resp) => {
                    debug!("req: request successful");
                    break Ok(resp);
                }
                Err(Error::SessionTokenNotPresent)
                | Err(Error::SessionTokenInvalid) => {
                    info!("req: login required");
                    trace!("req: taking token write lock");
                    let mut token_lock = self.session_token.write().unwrap();

                    if token != *token_lock {
                        // Another thread has already performed the login.
                        token = token_lock.clone();
                        continue;
                    }

                    token = loop {
                        debug!("login: sending request");
                        match self.login() {
                            Ok(token) => {
                                info!("login: success");
                                break Some(token);
                            }
                            Err(e) => {
                                warn!("login: failed {:?}", e);

                                // TODO: exponential backoff
                                debug!("login: sleeping for 5000ms");
                                thread::sleep(Duration::from_millis(5000));
                            }
                        }
                    };

                    *token_lock = token.clone();
                    drop(token_lock); // explicit drop for logging purposes
                    trace!("req: dropped token write lock");
                }
                Err(e) => {
                    error!("req: unhandled error {:?}", e);
                    break Err(e);
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

        let login_response: LoginResponse = client
            .post(CERTLOGIN_URI)
            .header(
                "X-Application",
                format!("schroedinger_{}", rand::random::<u128>()),
            )
            .form(&login_request_form)
            .send()?
            .json()?;
        match login_response.sessionToken {
            Some(token) => Ok(token),
            None => Err(Error::BFLoginFailure(format!(
                "loginStatus: {}",
                login_response.loginStatus
            ))),
        }
    }
}

fn keepalive(token: &String, proxy_uri: &Option<String>) -> Result<()> {
    const KEEPALIVE_URI: &str =
        "https://identitysso.betfair.com/api/keepAlive";

    let client: Client = match proxy_uri {
        Some(uri) => {
            let proxy = reqwest::Proxy::all(uri)?;
            Client::builder().proxy(proxy).build()?
        }
        None => Client::new(),
    };

    let keep_alive_response: KeepAliveResponse = client
        .get(KEEPALIVE_URI)
        .header("Accept", "application/json")
        .header(
            "X-Application",
            format!("schroedinger_{}", rand::random::<u128>()),
        )
        .header("X-Authentication", token)
        .send()?
        .json()?;

    match keep_alive_response.status {
        KeepAliveStatus::SUCCESS => Ok(()),
        KeepAliveStatus::FAIL => Err(Error::BFKeepAliveFailure(
            keep_alive_response.error.unwrap(),
        )),
    }
}

#[derive(Debug, Deserialize)]
#[allow(non_camel_case_types)]
pub enum KeepAliveError {
    // TODO should this really be public?
    #[serde(rename = "")]
    NONE,
    INPUT_VALIDATION_ERROR,
    INTERNAL_ERROR,
    NO_SESSION,
}

#[derive(Debug, Deserialize)]
#[allow(non_camel_case_types)]
enum KeepAliveStatus {
    SUCCESS,
    FAIL,
}

#[derive(Debug, Deserialize)]
#[allow(non_snake_case)]
struct KeepAliveResponse {
    token: String,
    product: String,
    status: KeepAliveStatus,
    error: Option<KeepAliveError>,
}
