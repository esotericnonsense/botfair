#!/usr/bin/env python3

from typing import Optional, Set
from xml.etree.ElementTree import Element, parse
from enum import Enum, auto

import string


class ParentType(Enum):
    OPERATION = auto()
    DATA_TYPE = auto()
    EXCEPTION_TYPE = auto()
    SIMPLE_TYPE = auto()


OBSERVED_TYPES: Set[str] = set()
OBSERVED_ENUMS: Set[str] = set()

ALLOWABLE = string.ascii_letters + string.digits


def parse_type(_type: str) -> None:
    _type = _type.replace(" ", "")  # sanity

    if _type.startswith("list("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in ALLOWABLE for x in inner_type)
        OBSERVED_TYPES.add(f"[{inner_type}]")
        return

    if _type.startswith("set("):
        inner_type = _type.replace(")", "", 1).split("(", maxsplit=1)[1]
        assert all(x in ALLOWABLE for x in inner_type)
        OBSERVED_TYPES.add(f"Set({inner_type})")
        return

    if _type.startswith("map("):
        inner_type_1, inner_type_2 = (
            _type.replace(")", "", 1)
            .split("(", maxsplit=1)[1]
            .split(",", maxsplit=1)
        )
        assert all(x in ALLOWABLE for x in inner_type_1), inner_type_1
        assert all(x in ALLOWABLE for x in inner_type_2), inner_type_2
        OBSERVED_TYPES.add(f"Map({inner_type_1}, {inner_type_2})")
        return

    OBSERVED_TYPES.add(_type)


def strip_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None

    return " ".join([x.strip() for x in s.split("\n")]).strip()


def parse_description(el: Element) -> None:
    assert el.tag == "description"
    assert not el.attrib
    assert len(el) == 0
    if el.text is not None:  # nullable string
        print(strip_string(el.text))


def parse_exceptions(el: Element) -> None:
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "exception":
            _type = child.attrib.pop("type")
            parse_type(_type)
            print(f"exception {_type}")
            assert not child.attrib
            assert not strip_string(child.text)
            assert len(child) == 1
            parse_description(child[0])
            continue

        print(child.tag)
        raise NotImplementedError


def parse_value(el: Element, enum: str, parent: ParentType) -> None:
    name = el.attrib.pop("name")
    OBSERVED_ENUMS.add(f"{enum}.{name}")

    if parent == ParentType.EXCEPTION_TYPE:
        _id_str: str = el.attrib.pop("id")
        assert _id_str.isdigit()
        _id = int(_id_str)
        print(f"value {_id} {name}")

    elif parent == ParentType.SIMPLE_TYPE:
        print(f"value {name}")

    else:
        raise NotImplementedError(f"value: {parent}")

    assert not el.attrib, el.attrib
    assert not strip_string(el.text)

    assert len(el) == 1
    parse_description(el[0])


def parse_validValues(el: Element, enum: str, parent: ParentType) -> None:
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "value":
            parse_value(child, enum=enum, parent=parent)
            continue

        raise NotImplementedError(f"validValues child {child.tag}")


def parse_parameter(el: Element, parent: ParentType) -> None:
    mandatory: bool
    try:
        mandatory_str = el.attrib.pop("mandatory")
        assert mandatory_str == "true"
        mandatory = True
    except Exception:
        mandatory = False

    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    parse_type(_type)
    print(f"param {name}: {_type} (mandatory={mandatory})")

    assert not el.attrib
    assert not strip_string(el.text)

    description_observed = False  # should be unique

    for child in el:  # type: Element
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if parent == ParentType.EXCEPTION_TYPE and child.tag == "validValues":
            parse_validValues(
                child, enum=name, parent=ParentType.EXCEPTION_TYPE
            )
            continue

        raise NotImplementedError(f"parameter {parent} {child.tag}")


def parse_request(el: Element) -> None:
    assert el.tag == "request"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "parameter":
            parse_parameter(child, parent=ParentType.OPERATION)
            continue

        raise NotImplementedError


def parse_parameters(el: Element) -> None:
    # operation

    assert el.tag == "parameters"
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:  # type: Element
        if child.tag == "request":
            print("request")
            parse_request(child)
            continue
        if child.tag == "simpleResponse":
            _type = child.attrib.pop("type")
            assert not child.attrib
            assert not strip_string(child.text)

            assert len(child) == 1
            parse_description(child[0])

            parse_type(_type)
            print(f"returns {_type}")
            continue
        if child.tag == "exceptions":
            print("exceptions")
            parse_exceptions(child)
            continue

        raise NotImplementedError


def parse_operation(el: Element) -> None:
    assert el.tag == "operation"
    name = el.attrib.pop("name")
    since = el.attrib.pop("since")
    assert not el.attrib
    assert not strip_string(el.text)
    print("===")
    print(name)

    for child in el:  # type: Element
        if child.tag == "description":
            assert not child.attrib
            assert len(child) == 0
            print(strip_string(child.text))
            print()
            continue
        if child.tag == "parameters":
            parse_parameters(child)
            continue

        print(OBSERVED_TYPES)
        raise NotImplementedError


def parse_dataType(el: Element) -> None:
    assert el.tag == "dataType"
    name = el.attrib.pop("name")
    assert not el.attrib
    assert not strip_string(el.text)
    print("===")
    print(name)

    description_observed = False  # should be unique

    for child in el:  # type: Element
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "parameter":
            parse_parameter(child, parent=ParentType.DATA_TYPE)
            continue

        print(child.tag)
        raise NotImplementedError


def parse_exceptionType(el: Element) -> None:
    assert el.tag == "exceptionType"
    name = el.attrib.pop("name")
    prefix = el.attrib.pop("prefix")
    assert not el.attrib
    assert not strip_string(el.text)
    print("===")
    print(name, prefix)

    description_observed = False  # should be unique

    child: Element
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "parameter":
            parse_parameter(child, parent=ParentType.EXCEPTION_TYPE)
            continue

        print(child.tag)
        raise NotImplementedError


def parse_simpleType(el: Element) -> None:
    assert el.tag == "simpleType"
    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    assert not el.attrib
    assert not strip_string(el.text)
    print("===")
    print(name, _type)

    description_observed = False  # should be unique

    for child in el:  # type: Element
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "validValues":
            parse_validValues(child, enum=name, parent=ParentType.SIMPLE_TYPE)
            continue

        print(child.tag)
        raise NotImplementedError


def main() -> None:
    tree = parse("SportsAPING.xml")
    root: Element = tree.getroot()

    for child in root:  # type: Element
        if child.tag == "description":
            assert not child.attrib
            print(strip_string(child.text))
            continue
        if child.tag == "operation":
            parse_operation(child)
            continue
        if child.tag == "dataType":
            parse_dataType(child)
            continue
        if child.tag == "exceptionType":
            parse_exceptionType(child)
            continue
        if child.tag == "simpleType":
            parse_simpleType(child)
            continue

        raise NotImplementedError(f"root {child.tag}")

    for x in sorted(list(OBSERVED_TYPES)):
        print(x)

    for x in sorted(list(OBSERVED_ENUMS)):
        print(x)


if __name__ == "__main__":
    main()
