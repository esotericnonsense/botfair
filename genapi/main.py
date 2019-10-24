#!/usr/bin/env python3

from typing import Optional, Set, List, Dict
from xml.etree.ElementTree import Element, parse
from enum import Enum, auto
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from collections import defaultdict

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
    mandatory: bool
    values: Optional[List[Value]]


@dataclass
class Operation(DataClassJsonMixin):
    """An operation as per the BF API"""

    name: str
    since: str
    description: Optional[str]
    params: List[Param]


@dataclass
class BfEnum(DataClassJsonMixin):
    """An enum as per the BF API"""

    name: str
    members: List[str]


@dataclass
class ExceptionType(DataClassJsonMixin):
    """An exception type as per the BF API"""

    name: str
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


class ParentType(Enum):
    OPERATION = auto()
    DATA_TYPE = auto()
    EXCEPTION_TYPE = auto()
    SIMPLE_TYPE = auto()


OBSERVED_TYPES: Set[str] = set()
OBSERVED_ENUMS: Dict[str, List[str]] = defaultdict(list)

ALLOWABLE = string.ascii_letters + string.digits


def parse_type(_type: str) -> str:
    _type = _type.replace(" ", "")  # sanity

    if _type.startswith("list("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in ALLOWABLE for x in inner_type)
        _type = f"List[{inner_type}]"

    elif _type.startswith("set("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in ALLOWABLE for x in inner_type)
        _type = f"Set[{inner_type}]"

    elif _type.startswith("map("):
        inner_type_1, inner_type_2 = (
            _type.replace(")", "", 1)
            .split("(", maxsplit=1)[1]
            .split(",", maxsplit=1)
        )
        assert all(x in ALLOWABLE for x in inner_type_1), inner_type_1
        assert all(x in ALLOWABLE for x in inner_type_2), inner_type_2
        _type = f"Map[{inner_type_1}, {inner_type_2}]"

    OBSERVED_TYPES.add(_type)
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

    return strip_string(el.text)


def parse_exceptions(el: Element) -> None:
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "exception":
            _type = child.attrib.pop("type")
            parse_type(_type)
            # print(f"exception {_type}")
            assert not child.attrib
            assert not strip_string(child.text)
            assert len(child) == 1
            parse_description(child[0])
            continue

        # print(child.tag)
        raise NotImplementedError


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

        raise NotImplementedError(f"validValues child {child.tag}")

    return values


def parse_parameter(el: Element, parent: ParentType) -> Param:
    mandatory: bool
    try:
        mandatory_str = el.attrib.pop("mandatory")
        assert mandatory_str == "true"
        mandatory = True
    except Exception:
        mandatory = False

    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    _type = parse_type(_type)
    # print(f"param {name}: {_type} (mandatory={mandatory})")

    assert not el.attrib
    assert not strip_string(el.text)

    description_observed = False  # should be unique

    values: Optional[List[Value]] = None
    for child in el:  # type: Element
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if parent == ParentType.EXCEPTION_TYPE and child.tag == "validValues":
            values = parse_validValues(child, parent=ParentType.EXCEPTION_TYPE)
            continue

        raise NotImplementedError(f"parameter {parent} {child.tag}")

    return Param(name=name, _type=_type, mandatory=mandatory, values=values)


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

        raise NotImplementedError

    return params


def parse_parameters(el: Element) -> List[Param]:
    assert el.tag == "parameters"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "request":
            # print("request")
            params = parse_request(child)
            continue
        if child.tag == "simpleResponse":
            _type = child.attrib.pop("type")
            assert not child.attrib
            assert not strip_string(child.text)

            assert len(child) == 1
            parse_description(child[0])

            parse_type(_type)
            # print(f"returns {_type}")
            continue
        if child.tag == "exceptions":
            # print("exceptions")
            parse_exceptions(child)
            continue

        raise NotImplementedError

    return params


def parse_operation(el: Element) -> Operation:
    assert el.tag == "operation"
    name = el.attrib.pop("name")
    since = el.attrib.pop("since")
    assert not el.attrib
    assert not strip_string(el.text)
    # print("===")
    # print(name)

    for child in el:  # type: Element
        if child.tag == "description":
            assert not child.attrib
            assert len(child) == 0
            description = strip_string(child.text)
            continue
        if child.tag == "parameters":
            params = parse_parameters(child)
            continue

        # print(OBSERVED_TYPES)
        raise NotImplementedError

    return Operation(
        name=name, since=since, description=description, params=params
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

        # print(child.tag)
        raise NotImplementedError

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

        raise NotImplementedError

    return ExceptionType(name=name, prefix=prefix, params=params)


def parse_simpleType(el: Element) -> SimpleType:
    assert el.tag == "simpleType"
    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    assert not el.attrib
    assert not strip_string(el.text)
    # print("===")
    # print(name, _type)

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

        raise NotImplementedError

    return SimpleType(
        name=name, _type=_type, values=values, description=description
    )


def main() -> None:
    tree = parse("SportsAPING.xml")
    root: Element = tree.getroot()
    assert not strip_string(root.text)

    description: Optional[str] = None
    operations: List[Operation] = []
    data_types: List[DataType] = []
    exception_types: List[ExceptionType] = []
    simple_types: List[SimpleType] = []
    for child in root:  # type: Element
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

        raise NotImplementedError(f"root {child.tag}")

    # for x in sorted(list(OBSERVED_TYPES)):
    #     print(x)

    # for k, v in OBSERVED_ENUMS.items():
    #     print(k)
    #     for x in v:
    #         print(f"    {x}")

    # x = Operation.schema().dumps(operations, many=True)
    # x = DataType.schema().dumps(data_types, many=True)
    # x = ExceptionType.schema().dumps(exception_types, many=True)
    # x = SimpleType.schema().dumps(simple_types, many=True)

    # print(x)


if __name__ == "__main__":
    main()
