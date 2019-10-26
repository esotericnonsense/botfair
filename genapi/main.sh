#!/usr/bin/env bash
# SPDX-Copyright: Copyright (c) 2019 Daniel Edgecumbe (esotericnonsense)
# SPDX-License-Identifier: AGPL-3.0-only
#
# This file is part of botfair.  botfair is free software: you can
# redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# botfair is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with botfair.  If not, see <http://www.gnu.org/licenses/>.

set -euo pipefail

echo "Generating bindings from the Betfair XML." >&2
echo "---" >&2

_env=$(mktemp -d)
trap 'rm -rf "${_env}"' exit

if [[ -d "${_env}/bin" ]]; then
    echo "Virtualenv should not exist, but it does. Exiting." >&2
    exit 1
fi

echo "Creating virtualenv" >&2
python3 -m virtualenv "${_env}"

# We assume that if a venv is present, it's the correct one
set +u # cannot activate a venv with -u
if [[ -n $VIRTUAL_ENV ]]; then
    echo "Should not be in a virtualenv, but we are. Exiting." >&2
    exit 1
fi

# shellcheck source=/dev/null
. "${_env}/bin/activate"

if [[ -z $VIRTUAL_ENV ]]; then
    echo "Sourced virtualenv, but not in virtualenv. Exiting." >&2
    exit 1
fi
set -u

echo "Installing requirements into virtualenv..." >&2
pip install -q -r requirements.txt

if [[ ! -f "SportsAPING.xml" ]]; then
    echo "Downloading API docs..." >&2
    curl -OL https://docs.developer.betfair.com/download/attachments/4392337/SportsAPING.xml
    echo "done"
else
    echo "API docs already present, not downloading." >&2
fi

echo "Checking API documentation checksum" >&2
sha256sum -c SportsAPING.xml.SHA256SUM

if [[ ! -f "SportsAPING.patched.xml" ]]; then
    echo "Patching API docs..." >&2
    patch -o "SportsAPING.patched.xml" "SportsAPING.xml" \
        < "SportsAPING.xml.patch"
    echo "done"
else
    echo "API docs already patched" >&2
fi

_output="$(realpath ../src/generated_api.rs)"

echo "Writing generated API to ${_output}" >&2
./main.py | rustfmt --config max_width=79 > "${_output}"

echo "---" >&2
echo "Done!" >&2
