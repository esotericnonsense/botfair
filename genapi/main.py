#!/usr/bin/env python3
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

from typing import Optional, List, Tuple
from xml.etree.ElementTree import Element, parse
from enum import Enum, auto
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin

import string


@dataclass
class Value(DataClassJsonMixin):
    """A value as per BF API"""

    name: str
    _id: Optional[int]
    description: Optional[str]


@dataclass
class Param(DataClassJsonMixin):
    """A parameter as per the BF API"""

    name: str
    _type: str
    description: Optional[str]
    mandatory: bool
    values: Optional[List[Value]]


@dataclass
class SimpleResponse(DataClassJsonMixin):
    """A simple response"""

    _type: str
    description: Optional[str]


@dataclass
class ExceptionResponse(DataClassJsonMixin):
    """A simple exception response"""

    _type: str
    description: Optional[str]


@dataclass
class Operation(DataClassJsonMixin):
    """An operation as per the BF API"""

    name: str
    since: str
    description: Optional[str]
    params: List[Param]
    simple_response: SimpleResponse
    exceptions: List[ExceptionResponse]


@dataclass
class ExceptionType(DataClassJsonMixin):
    """An exception type as per the BF API"""

    name: str
    description: Optional[str]
    prefix: str
    params: List[Param]


@dataclass
class SimpleType(DataClassJsonMixin):
    """An exception type as per the BF API"""

    name: str
    _type: str
    description: Optional[str]
    values: Optional[List[Value]]


@dataclass
class DataType(DataClassJsonMixin):
    """An exception type as per the BF API"""

    name: str
    description: Optional[str]
    params: List[Param]


@dataclass
class APING(DataClassJsonMixin):
    """Parsed Betfair APING"""

    description: Optional[str]
    operations: List[Operation]
    data_types: List[DataType]
    exception_types: List[ExceptionType]
    simple_types: List[SimpleType]


class ParentType(Enum):
    OPERATION = auto()
    DATA_TYPE = auto()
    EXCEPTION_TYPE = auto()
    SIMPLE_TYPE = auto()


def parse_type(_type: str) -> str:
    _type = _type.replace(" ", "")  # sanity

    allowable: str = string.ascii_letters + string.digits

    if _type.startswith("list("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in allowable for x in inner_type)
        _type = f"List[{inner_type}]"

    elif _type.startswith("set("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in allowable for x in inner_type)
        _type = f"Set[{inner_type}]"

    elif _type.startswith("map("):
        inner_type_1, inner_type_2 = (
            _type.replace(")", "", 1)
            .split("(", maxsplit=1)[1]
            .split(",", maxsplit=1)
        )
        assert all(x in allowable for x in inner_type_1), inner_type_1
        assert all(x in allowable for x in inner_type_2), inner_type_2
        _type = f"Map[{inner_type_1}, {inner_type_2}]"

    return _type


def strip_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None

    return " ".join([x.strip() for x in s.split("\n")]).strip()


def parse_description(el: Element) -> Optional[str]:
    assert el.tag == "description"
    assert not el.attrib
    assert len(el) == 0

    if el.text is None:
        return None

    s: Optional[str] = strip_string(el.text)
    if s is None:
        return None

    if s == "":
        return None

    return s


def parse_exceptions(el: Element) -> List[ExceptionResponse]:
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not strip_string(el.text)

    exceptions: List[ExceptionResponse] = []
    for child in el:  # type: Element
        if child.tag == "exception":
            _type = child.attrib.pop("type")
            assert not child.attrib
            assert not strip_string(child.text)
            assert len(child) == 1

            _type = parse_type(_type)
            description = parse_description(child[0])
            exceptions.append(
                ExceptionResponse(_type=_type, description=description)
            )
            continue

        raise NotImplementedError(child.tag)

    return exceptions


def parse_value(el: Element, parent: ParentType) -> Value:
    name = el.attrib.pop("name")

    _id: Optional[int]
    if parent == ParentType.EXCEPTION_TYPE:
        _id_str: str = el.attrib.pop("id")
        assert _id_str.isdigit()
        _id = int(_id_str)

    elif parent == ParentType.SIMPLE_TYPE:
        _id = None

    else:
        raise NotImplementedError(f"value: {parent}")

    assert not el.attrib, el.attrib
    assert not strip_string(el.text)

    assert len(el) == 1
    description = parse_description(el[0])

    return Value(name=name, _id=_id, description=description)


def parse_validValues(el: Element, parent: ParentType) -> List[Value]:
    assert not el.attrib
    assert not strip_string(el.text)

    values: List[Value] = []
    for child in el:  # type: Element
        if child.tag == "value":
            values.append(parse_value(child, parent=parent))
            continue

        raise NotImplementedError(child.tag)

    return values


def parse_parameter(el: Element, parent: ParentType) -> Param:
    mandatory: bool
    try:
        mandatory_str = el.attrib.pop("mandatory")
        if mandatory_str == "true":
            mandatory = True
        else:
            assert mandatory_str == "false"
            mandatory = False
    except KeyError:
        mandatory = False

    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    _type = parse_type(_type)

    assert not el.attrib
    assert not strip_string(el.text)

    description: Optional[str] = None
    values: Optional[List[Value]] = None
    for child in el:  # type: Element
        if child.tag == "description":
            assert description is None
            description = parse_description(child)
            continue
        if parent == ParentType.EXCEPTION_TYPE and child.tag == "validValues":
            values = parse_validValues(child, parent=ParentType.EXCEPTION_TYPE)
            continue

        raise NotImplementedError(child.tag)

    return Param(
        name=name,
        _type=_type,
        description=description,
        mandatory=mandatory,
        values=values,
    )


def parse_request(el: Element) -> List[Param]:
    assert el.tag == "request"
    assert not el.attrib
    assert not strip_string(el.text)

    params: List[Param] = []
    for child in el:  # type: Element
        if child.tag == "parameter":
            param = parse_parameter(child, parent=ParentType.OPERATION)
            params.append(param)
            continue

        raise NotImplementedError(child.tag)

    return params


def parse_parameters(
    el: Element
) -> Tuple[List[Param], SimpleResponse, List[ExceptionResponse]]:
    assert el.tag == "parameters"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "request":
            params = parse_request(child)
            continue
        if child.tag == "simpleResponse":
            _type = child.attrib.pop("type")
            assert not child.attrib
            assert not strip_string(child.text)

            assert len(child) == 1
            description = parse_description(child[0])

            simple_response = SimpleResponse(
                _type=parse_type(_type), description=description
            )
            continue
        if child.tag == "exceptions":
            exceptions = parse_exceptions(child)
            continue

        raise NotImplementedError(child.tag)

    return (params, simple_response, exceptions)


def parse_operation(el: Element) -> Operation:
    assert el.tag == "operation"
    name = el.attrib.pop("name")
    since = el.attrib.pop("since")
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "description":
            assert not child.attrib
            assert len(child) == 0
            description = strip_string(child.text)
            continue
        if child.tag == "parameters":
            params, simple_response, exceptions = parse_parameters(child)
            continue

        raise NotImplementedError(child.tag)

    return Operation(
        name=name,
        since=since,
        description=description,
        params=params,
        simple_response=simple_response,
        exceptions=exceptions,
    )


def parse_dataType(el: Element) -> DataType:
    assert el.tag == "dataType"
    name = el.attrib.pop("name")
    assert not el.attrib
    assert not strip_string(el.text)

    description: Optional[str] = None
    params: List[Param] = []
    for child in el:  # type: Element
        if child.tag == "description":
            assert description is None
            description = parse_description(child)
            continue
        if child.tag == "parameter":
            params.append(parse_parameter(child, parent=ParentType.DATA_TYPE))
            continue

        raise NotImplementedError(child.tag)

    return DataType(name=name, description=description, params=params)


def parse_exceptionType(el: Element) -> ExceptionType:
    assert el.tag == "exceptionType"
    name = el.attrib.pop("name")
    prefix = el.attrib.pop("prefix")
    assert not el.attrib
    assert not strip_string(el.text)

    description: Optional[str] = None
    params: List[Param] = []
    for child in el:  # type: Element
        if child.tag == "description":
            assert description is None
            description = parse_description(child)
            continue
        if child.tag == "parameter":
            params.append(
                parse_parameter(child, parent=ParentType.EXCEPTION_TYPE)
            )
            continue

        raise NotImplementedError(child.tag)

    return ExceptionType(
        name=name, description=description, prefix=prefix, params=params
    )


def parse_simpleType(el: Element) -> SimpleType:
    assert el.tag == "simpleType"
    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    assert not el.attrib
    assert not strip_string(el.text)

    values: Optional[List[Value]] = None
    description: Optional[str] = None
    for child in el:  # type: Element
        if child.tag == "description":
            assert description is None
            description = parse_description(child)
            continue
        if child.tag == "validValues":
            assert values is None
            values = parse_validValues(child, parent=ParentType.SIMPLE_TYPE)
            continue

        raise NotImplementedError(child.tag)

    return SimpleType(
        name=name, _type=_type, values=values, description=description
    )


def parse_aping(el: Element) -> APING:
    # We ignore the attributes here deliberately.
    assert not strip_string(el.text)

    description: Optional[str] = None
    operations: List[Operation] = []
    data_types: List[DataType] = []
    exception_types: List[ExceptionType] = []
    simple_types: List[SimpleType] = []
    for child in el:  # type: Element
        if child.tag == "description":
            assert description is None
            description = parse_description(child)
            continue
        if child.tag == "operation":
            operations.append(parse_operation(child))
            continue
        if child.tag == "dataType":
            data_types.append(parse_dataType(child))
            continue
        if child.tag == "exceptionType":
            exception_types.append(parse_exceptionType(child))
            continue
        if child.tag == "simpleType":
            simple_types.append(parse_simpleType(child))
            continue

        raise NotImplementedError(child.tag)

    return APING(
        description=description,
        operations=operations,
        data_types=data_types,
        exception_types=exception_types,
        simple_types=simple_types,
    )


def aping_name_to_rust_name(name: str) -> str:
    # These are keywords in Rust. We need to figure out how
    #   to handle these later.
    direct_conversions = {"type": "r#type", "id": "r#id", "async": "r#async"}

    try:
        return direct_conversions[name]
    except KeyError:
        pass

    return name


def python_type_to_rust_type(_type: str, mandatory: bool = True) -> str:
    # This is a bit hacky, particularly for the compound types,
    #   but the API is simple enough that this works anyway.

    # We assume sets are actually vectors because otherwise the API
    #   is insane.

    direct_conversions = {
        "double": "f64",
        "string": "String",  # possibly a &str
        "dateTime": "DateTime<Utc>",  # possibly an unaware DT
        # These are pretty hacky, we should parse properly
        "Set[string]": "Vec<String>",
        "Map[string, string]": "HashMap<String, String>",
        "Map[string, Matches]": "HashMap<String, Matches>",
    }

    try:
        _type = direct_conversions[_type]
    except KeyError:
        _type = _type.replace("List[", "Vec<")
        _type = _type.replace("Map[", "HashMap<")
        _type = _type.replace("Set[", "Vec<")
        _type = _type.replace("]", ">")

    if mandatory is False:
        return f"Option<{_type}>"

    return _type


def generate_rust_simple_types(simple_types: List[SimpleType]) -> List[str]:
    """
    Return API bindings for the simpleTypes.
    """

    types: List[str] = []
    for simple_type in simple_types:  # type: SimpleType
        if simple_type.description is not None:
            types.append(f"/// {simple_type.description}")

        if simple_type.values is None:
            rust_type: str = python_type_to_rust_type(simple_type._type)
            types.append(f"pub type {simple_type.name} = {rust_type};")
            continue
        else:
            # All of the enums are stringly typed, this is a sanity check
            assert simple_type._type == "string"

            variants: List[str] = []
            for value in simple_type.values:
                if value.description is not None:
                    variants.append(f"/// {value.description}")
                variants.append(f"{value.name},")
            variants_str = "\n".join(variants)
            types.append(
                f"""#[derive(Debug, Deserialize, Serialize)]
pub enum {simple_type.name} {{
{variants_str}
}}"""
            )
            continue

    return types


def generate_rust_data_types(data_types: List[DataType]) -> List[str]:
    """
    Return API bindings for the dataTypes.
    """

    types: List[str] = []
    for data_type in data_types:  # type: DataType
        # types.append(str(data_type))
        # TODO: document the descriptions along with the param

        params_converted: List[Tuple[str, str]] = []
        for param in data_type.params:  # type: Param
            name: str = aping_name_to_rust_name(param.name)
            _type: str = python_type_to_rust_type(param._type, param.mandatory)
            params_converted.append((name, _type))

        def format_param(x):
            # TODO: this is super ugly. seriously?
            if x[1].startswith("Option<"):
                return f"""#[serde(skip_serializing_if = "Option::is_none")]
pub {x[0]}: {x[1]}"""

            return f"pub {x[0]}: {x[1]}"

        formatted_params: str = ", \n".join(
            format_param(x) for x in params_converted
        )
        if data_type.description is not None:
            types.append(f"/// {data_type.description}")

        types.append(
            f"""#[derive(Debug, Deserialize, Serialize)]
pub struct {data_type.name} {{ {formatted_params} }}"""
        )

    return types


@dataclass
class RustOperations:
    """Rust code derived from the BF operations"""

    request_structs: List[str]
    functions: List[str]


def generate_rust_operations(operations: List[Operation]) -> RustOperations:
    """
    Return API bindings for the operations.
    """

    request_structs: List[str] = []
    functions: List[str] = []
    for operation in operations:  # type: Operation
        # print(operation)

        params_converted: List[Tuple[str, str]] = []
        for param in operation.params:  # type: Param
            name: str = aping_name_to_rust_name(param.name)
            _type: str = python_type_to_rust_type(param._type, param.mandatory)
            params_converted.append((name, _type))

        formatted_params_args: str = ", ".join(
            ["&self"] + [f"{x[0]}: {x[1]}" for x in params_converted]
        )

        resp_type: str = python_type_to_rust_type(
            operation.simple_response._type
        )

        if len(operation.params) > 0:
            struct_name: str = f"{operation.name}Request"

            # TODO these should probably not be public, just for now
            #       so that we can test outside of jsonrpc
            def format_param(x):
                # TODO: this is super ugly. seriously?
                if x[1].startswith("Option<"):
                    return f"""#[serde(skip_serializing_if = "Option::is_none")]
pub {x[0]}: {x[1]}"""

                return f"pub {x[0]}: {x[1]}"

            formatted_params_struct: str = ", \n".join(
                format_param(x) for x in params_converted
            )

            request_structs.append(
                f"""#[derive(Serialize)]
pub struct {struct_name} {{ {formatted_params_struct} }}"""
            )

            formatted_params_declare: str = ", ".join(
                f"{x[0]}" for x in params_converted
            )

            function_interior = f"""
let req: {struct_name} = {struct_name} {{ {formatted_params_declare} }};
let rpc_request: RpcRequest<{struct_name}> = RpcRequest::new(
    \"SportsAPING/v1.0/{operation.name}\".to_owned(),
    req
);
self.req(rpc_request).map(|x| x.into_inner())?
"""
        else:
            # TODO this smells, repetition
            function_interior = f"""
let rpc_request: RpcRequest<()> = RpcRequest::new(
    \"SportsAPING/v1.0/{operation.name}\".to_owned(),
    ()
);
self.req(rpc_request).map(|x| x.into_inner())?
"""

        function_signature = f"""fn {operation.name}({formatted_params_args}) ->
Result<{resp_type}>"""
        if operation.description is not None:
            functions.append(f"/// {operation.description}")
        functions.append(
            f"""#[allow(dead_code)]
pub {function_signature} {{ {function_interior} }}"""
        )

    return RustOperations(request_structs=request_structs, functions=functions)


def generate_rust_exceptions(
    exception_types: List[ExceptionType]
) -> List[str]:
    """
    Return API bindings for the exceptionTypes.
    """

    #        def format_param(param: Param):
    #            return f"""#[serde(rename = "{exception_type.prefix}-{(param._id):04d}")]
    # {aping_name_to_rust_name(param.name)}"""

    exceptions: List[str] = []
    for exception_type in exception_types:  # type: ExceptionType
        # TODO
        # if exception_type.description is not None:
        #     exceptions.append(f"/// {exception_type.description}")

        for param in exception_type.params:
            if param.name != "errorCode":
                # TODO do not ignore
                continue

            if param.values is None:
                rust_type: str = python_type_to_rust_type(param._type)
                exceptions.append(f"pub type {param.name} = {rust_type};")
                continue
            # All of the enums are stringly typed, this is a sanity check
            assert param._type == "string"

            variants: List[str] = []
            for value in param.values:
                subvariant: List[str] = []
                if value.description is not None:
                    subvariant.append(f"/// {value.description}")
                subvariant.append(
                    f"""#[serde(rename = "{exception_type.prefix}-{(value._id):04d}")]
{value.name}"""
                )
                variants.append("\n".join(subvariant))

            variants_str = ",\n".join(variants)
            exceptions.append(
                f"""#[derive(Debug, Deserialize)]
    pub enum {param.name} {{
    {variants_str}
    }}"""
            )
            continue

    return exceptions


def main() -> None:
    tree = parse("SportsAPING.patched.xml")
    aping: APING = parse_aping(tree.getroot())

    # print(aping.to_json())

    header = [
        "//! # automatically generated",
        "//! This module has been automatically generated by botfair",
        "//! from the Betfair APING documentation at",
        "//! https://docs.developer.betfair.com",
        "//!",
        "//! Any documentation here has been generated directly from the API",
        "//! docs.",
        "",
    ]

    rust_operations: RustOperations = generate_rust_operations(
        aping.operations
    )
    rust_simple_types: List[str] = generate_rust_simple_types(
        aping.simple_types
    )
    rust_data_types: List[str] = generate_rust_data_types(aping.data_types)
    rust_exceptions: List[str] = generate_rust_exceptions(
        aping.exception_types
    )
    with open("../src/generated_types.rs", "w") as f:
        for l in header:
            f.write(l + "\n")
        a = [
            "#![allow(non_camel_case_types)]",
            "#![allow(non_snake_case)]",
            "use chrono::{DateTime, Utc};",
            "use std::collections::HashMap;",
            "use serde::{Deserialize, Serialize};",
        ]
        for l in a:
            f.write(l + "\n")
        for l in rust_simple_types:
            f.write(l + "\n")
        for l in rust_data_types:
            f.write(l + "\n")

    with open("../src/generated_methods.rs", "w") as f:
        for l in header:
            f.write(l + "\n")
        a = [
            "#![allow(non_snake_case)]",
            "use chrono::{DateTime, Utc};",
            "use crate::result::Result;",
            "use crate::json_rpc::RpcRequest;",
            "use crate::generated_requests::*;",
            "use crate::generated_types::*;",
        ]
        for l in a:
            f.write(l + "\n")
        f.write("impl crate::client::BFClient {\n")
        for l in rust_operations.functions:
            f.write(l + "\n")
        f.write("}\n")

    with open("../src/generated_requests.rs", "w") as f:
        for l in header:
            f.write(l + "\n")
        a = [
            "#![allow(non_camel_case_types)]",
            "#![allow(non_snake_case)]",
            "use chrono::{DateTime, Utc};",
            "use serde::Serialize;",
            "use crate::generated_types::*;",
        ]
        for l in a:
            f.write(l + "\n")
        for l in rust_operations.request_structs:
            f.write(l + "\n")

    with open("../src/generated_exceptions.rs", "w") as f:
        for l in header:
            f.write(l + "\n")
        a = [
            "#![allow(non_camel_case_types)]",
            "#![allow(non_snake_case)]",
            "use serde::Deserialize;",
        ]
        for l in a:
            f.write(l + "\n")
        for l in rust_exceptions:
            f.write(l + "\n")


if __name__ == "__main__":
    main()
