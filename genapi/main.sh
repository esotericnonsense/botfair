#!/usr/bin/env bash
set -euxo pipefail

# First:
# $ python3 -m virtualenv env
# $ source env/bin/activate
# $ pip install -r requirements.txt

_output="$(realpath ../src/generated_api.rs)"

echo "Writing generated API to ${_output}"
./main.py | rustfmt --config max_width=79 > "${_output}"
