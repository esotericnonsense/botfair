# `botfair`

Rust bindings for the Betfair SportsAPING.
Automatic login.
Coming soon: automatic keep-alive.

https://git.esotericnonsense.com/pub/botfair.git - main repository
https://github.com/esotericnonsense/botfair.git - github repo, for PRs etc

## Contact

Daniel Edgecumbe (esotericnonsense)
[botfair@esotericnonsense.com](mailto:botfair@esotericnonsense.com)

## Usage
Note that `botfair` requires your certificate to be in `pfx` format.
In order to achieve this given a key and crt file, you can use the following
openssl command:

```
openssl pkcs12 -export -out client.pfx \
    -inkey client.key -in client.crt
```

`botfair` assumes no password protection for the `pfx` file.

```
let bf_creds = BFCredentials::new(
    "my_username".to_owned(),
    "my_password".to_owned(),
    "/path/to/pfx/file".to_owned(),
    "my_appkey".to_owned()
).unwrap();

let bf_client = BFClient::new(
    bf_creds,
    None
).unwrap();

// This is all rather verbose at the moment.
// What will the future bring?
let market_filter = MarketFilter {
    textQuery: None,
    exchangeIds: None,
    eventTypeIds: None,
    eventIds: None,
    competitionIds: None,
    marketIds: None,
    venues: None,
    bspOnly: None,
    turnInPlayEnabled: None,
    inPlayOnly: None,
    marketBettingTypes: None,
    marketCountries: None,
    marketTypeCodes: None,
    marketStartTime: None,
    withOrders: None,
    raceTypes: None,
};

// List ten arbitrary markets
let catalogues: Vec<MarketCatalogue> =
    bf_client.listMarketCatalogue(market_filter, None, None, 10, None)?;

println!("{:?}", catalogues);
```

## Generating the bindings

If you just want to use the crate, you can skip this section as the bindings
are already present.

To re-generate the bindings from the Betfair XML documentation, you will need
to `cd genapi; ./main.sh` which fetches the documentation from Betfair's
servers and runs a python script on them to generate the Rust bindings.

## License

For open source software, `botfair` is subject to the GNU AGPLv3, contained
in the document LICENSE.AGPLv3 which should be distributed with the software.

This means that you need to licence your software under the same terms. In
particular, this means that software that makes use of this library must
make available its' source code to the users of said software, whether that
software is interacted with over a network or by the end users directly.

For closed source software, exceptions may be made at the discretion of the
author.

For paid support, licensing queries, or general banter, please use the below
contact details:
