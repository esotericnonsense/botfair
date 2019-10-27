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

//! # botfair
//!
//! The `botfair` crate provides Rust bindings for the Betfair SportsAPING.
//! Automatic login.
//! Coming soon: automatic keep-alive.
//!
//! ## Example
//! ```
//! use botfair::generated_types::{MarketBook, MarketCatalogue};
//! use botfair::generated_types::{MarketFilter, MarketId};
//! use botfair::result::Result;
//! use botfair::{BFClient, BFCredentials};
//!
//! fn main() -> Result<()> {
//!     let bf_creds = BFCredentials::new(
//!         "my_username".to_owned(),
//!         "my_password".to_owned(),
//!         "/path/to/pfx/file".to_owned(),
//!         "my_appkey".to_owned()
//!     ).unwrap();
//!
//!     let bf_client = BFClient::new(
//!         bf_creds,
//!         None
//!     ).unwrap();
//!
//!     // This is all rather verbose at the moment.
//!     // What will the future bring?
//!     let market_filter = MarketFilter {
//!         textQuery: None,
//!         exchangeIds: None,
//!         eventTypeIds: None,
//!         eventIds: None,
//!         competitionIds: None,
//!         marketIds: None,
//!         venues: None,
//!         bspOnly: None,
//!         turnInPlayEnabled: None,
//!         inPlayOnly: None,
//!         marketBettingTypes: None,
//!         marketCountries: None,
//!         marketTypeCodes: None,
//!         marketStartTime: None,
//!         withOrders: None,
//!         raceTypes: None,
//!     };
//!
//!     // List ten arbitrary markets
//!     let catalogues: Vec<MarketCatalogue> =
//!         bf_client.listMarketCatalogue(market_filter, None, None, 10, None)?;
//!
//!     println!("{:?}", catalogues);
//!     Ok(())
//! }
//! ```

#[macro_use]
extern crate log;

pub mod client;
mod generated_methods;
mod generated_requests;
pub mod generated_types;
mod json_rpc;
pub mod result;

pub mod prelude {
    pub use crate::client::BFClient;
    pub use crate::client::BFCredentials;
}

pub use crate::client::BFClient;
pub use crate::client::BFCredentials;
