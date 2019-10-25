// import requests
//
// #openssl x509 -x509toreq -in certificate.crt -out CSR.csr -signkey privateKey.key
//
//
// payload = 'username=myusername&password=password'
// headers = {'X-Application': 'SomeKey', 'Content-Type': 'application/x-www-form-urlencoded'}
//
// resp = requests.post('', data=payload, cert=('client-2048.crt', 'client-2048.key'), headers=headers)
//
// if resp.status_code == 200:
//   resp_json = resp.json()
//   print resp_json['loginStatus']
//   print resp_json['sessionToken']
// else:
//   print "Request failed."

#[macro_use]
extern crate log;

use reqwest::{Client, Identity};
use serde::{Deserialize, Serialize};
use std::fs;

mod generated_api;
mod json_rpc;

const CERTLOGIN_URI: &str =
    "https://identitysso-cert.betfair.com/api/certlogin";
const JSONRPC_URI: &str =
    "https://api.betfair.com/exchange/betting/json-rpc/v1";
const PFXFILE: &str = "/home/esotericnonsense/betfair/identity.pfx";
const APPKEYFILE: &str = "/home/esotericnonsense/betfair/betfair-app-key";
const USERFILE: &str = "/home/esotericnonsense/betfair/betfair-user";
const PASSFILE: &str = "/home/esotericnonsense/betfair/betfair-pass";

#[derive(Debug)]
enum AnyError {
    Io(std::io::Error),
    Reqwest(reqwest::Error),
    Other,
}

impl From<std::io::Error> for AnyError {
    fn from(e: std::io::Error) -> Self {
        AnyError::Io(e)
    }
}

impl From<reqwest::Error> for AnyError {
    fn from(e: reqwest::Error) -> Self {
        AnyError::Reqwest(e)
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

fn get_session_token() -> Result<String, AnyError> {
    let username = fs::read_to_string(USERFILE)?.replace("\n", "");
    let password = fs::read_to_string(PASSFILE)?.replace("\n", "");

    let proxy = reqwest::Proxy::all("socks5h://127.0.0.1:40001")?;
    let ident =
        Identity::from_pkcs12_der(std::fs::read(PFXFILE)?.as_slice(), "")?;
    let cl: Client = Client::builder().identity(ident).proxy(proxy).build()?;

    let appheader = format!("{}", rand::random::<u128>());

    let login_request_form = LoginRequestForm { username, password };
    info!("{:?}", login_request_form);
    let login_response: LoginResponse = cl
        .post(CERTLOGIN_URI)
        .header("X-Application", appheader)
        .form(&login_request_form)
        .send()?
        .json()?;

    info!("{:?}", login_response);

    match login_response.sessionToken {
        Some(token) => Ok(token),
        None => Err(AnyError::Other),
    }
}

use generated_api::{listMarketBookRequest, MarketBook, MarketId};
use json_rpc::{RpcRequest, RpcResponse};
fn try_lmb(
    session_token: String,
    market_id: MarketId,
) -> Result<Vec<MarketBook>, AnyError> {
    let app_key = fs::read_to_string(APPKEYFILE)?.replace("\n", "");

    let proxy = reqwest::Proxy::all("socks5h://127.0.0.1:40001")?;
    let cl: Client = Client::builder().proxy(proxy).build()?;

    let method = "SportsAPING/v1.0/listMarketBook".to_owned();
    let params = listMarketBookRequest {
        marketIds: vec![market_id],
        priceProjection: None,
        orderProjection: None,
        matchProjection: None,
        includeOverallPosition: None,
        partitionMatchedByStrategyRef: None,
        customerStrategyRefs: None,
        currencyCode: None,
        locale: None,
        matchedSince: None,
        betIds: None,
    };
    let rpc_request = RpcRequest::new(method, params);

    // TODO handle exceptions
    let rpc_response: RpcResponse<Vec<MarketBook>> = cl
        .post(JSONRPC_URI)
        .header("X-Application", app_key)
        .header("X-Authentication", session_token)
        .json(&rpc_request)
        .send()?
        .json()?;

    Ok(rpc_response.into_inner())
}

fn main() -> Result<(), AnyError> {
    env_logger::Builder::from_default_env()
        .target(env_logger::Target::Stderr)
        .init();

    match get_session_token() {
        Ok(x) => {
            let books: Vec<MarketBook> = try_lmb(x, "1.156586178".to_owned())?;
            info!("{:?}", books);
            let s: String = serde_json::to_string(&books).expect("whatever");
            println!("{}", s);
            Ok(())
        }
        Err(e) => {
            if let AnyError::Reqwest(f) = e {
                error!("got error {}", f);
            } else {
                error!("got error {:?}", e);
            }
            Err(AnyError::Other)
        }
    }
}
