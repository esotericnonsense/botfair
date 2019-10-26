# botfair

Rust bindings for the Betfair SportsAPING.

To re-generate the bindings from the Betfair XML documentation, you will need
to `cd genapi; ./main.sh` which fetches the documentation from Betfair's
servers and runs a python script on them to generate the Rust bindings.

If you just want to use the bindings, this is not necessary as the result is
already present in the crate.

This is a work in progress, more information coming soon.

## License

For open source software, botfair is subject to the GNU AGPLv3, contained
in the document LICENSE.AGPLv3 which should be distributed with the software.

This means that you need to licence your software under the same terms. In
particular, this means that software that makes use of this library must
make available its' source code to the users of said software, whether that
software is interacted with over a network or by the end users directly.

For closed source software, exceptions may be made at the discretion of the
author.

For paid support, licensing queries, or general banter, please use the below
contact details:

## Contact

Daniel Edgecumbe botfair@esotericnonsense.com
