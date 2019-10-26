# botfair

Rust bindings for the Betfair SportsAPING.

To re-generate the bindings from the Betfair XML documentation, you will need
to `cd genapi; ./main.sh` which fetches the documentation from Betfair's
servers and runs a python script on them to generate the Rust bindings.

If you just want to use the bindings, this is not necessary as the result is
already present in the crate.

This is a work in progress, more information coming soon.
