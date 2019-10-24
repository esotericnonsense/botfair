#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from typing import Optional, Set

from xml.etree.ElementTree import Element


from enum import Enum, auto
class ParentType(Enum):
    OPERATION = auto()
    DATA_TYPE = auto()
    EXCEPTION_TYPE = auto()
    SIMPLE_TYPE = auto()

OBSERVED_TYPES: Set[str] = set()
OBSERVED_ENUMS: Set[str] = set()

def strip_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None

    return " ".join([x.strip() for x in s.split("\n")]).strip()

def parse_description(el: Element) -> None:
    assert el.tag == "description"
    assert not el.attrib
    assert len(el) == 0
    if el.text is not None: # nullable string
        print(strip_string(el.text))

def parse_exceptions(el: Element) -> None:
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not strip_string(el.text)

    child: Element
    for child in el:
        if child.tag == "exception":
            _type = child.attrib.pop("type")
            OBSERVED_TYPES.add(_type)
            print(f"exception {_type}")
            assert not child.attrib
            assert not strip_string(child.text)
            assert len(child) == 1
            parse_description(child[0])
            continue

        print(child.tag)
        raise NotImplementedError

def parse_value(el: Element, _parent: ParentType) -> None:
    name = el.attrib.pop("name")
    OBSERVED_ENUMS.add(name)

    if _parent == ParentType.EXCEPTION_TYPE:
        _id_str: str = el.attrib.pop("id")
        assert _id_str.isdigit()
        _id = int(_id_str)
        print(f"value {_id} {name}")

    elif _parent == ParentType.SIMPLE_TYPE:
        print(f"value {name}")

    else:
        raise NotImplementedError(f"value: {_parent}")

    assert not el.attrib, el.attrib
    assert not strip_string(el.text)

    assert len(el) == 1
    parse_description(el[0])

def parse_validValues(el: Element, _parent: ParentType) -> None:
    assert not el.attrib
    assert not strip_string(el.text)

    child: Element
    for child in el:
        if child.tag == "value":
            parse_value(child, _parent=_parent)
            continue

        raise NotImplementedError(f"validValues child {child.tag}")

def parse_parameter(el: Element, _parent: ParentType) -> None:
    mandatory: bool
    try:
        mandatory_str = el.attrib.pop("mandatory")
        assert mandatory_str == "true"
        mandatory = True
    except Exception:
        mandatory = False

    name = el.attrib.pop("name")
    _type = el.attrib.pop("type")
    OBSERVED_TYPES.add(_type)
    print(f"param {name}: {_type} (mandatory={mandatory})")

    assert not el.attrib
    assert not strip_string(el.text)

    description_observed = False  # should be unique

    child: Element
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if _parent == ParentType.EXCEPTION_TYPE and child.tag == "validValues":
            parse_validValues(child, _parent=ParentType.EXCEPTION_TYPE)
            continue

        raise NotImplementedError(f"parameter {_parent} {child.tag}")

def parse_request(el: Element) -> None:
    assert el.tag == "request"
    assert not el.attrib
    assert not strip_string(el.text)
    for child in el:
        if child.tag == "parameter":
            parse_parameter(child, _parent=ParentType.OPERATION)
            continue

        raise NotImplementedError


def parse_parameters(el: Element) -> None:
    # operation

    assert el.tag == "parameters"
    assert not el.attrib
    assert not strip_string(el.text)

    child: Element
    for child in el:
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

            OBSERVED_TYPES.add(_type)
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

    child: Element
    for child in el:
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

    child: Element
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "parameter":
            parse_parameter(child, _parent=ParentType.DATA_TYPE)
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
            parse_parameter(child, _parent=ParentType.EXCEPTION_TYPE)
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

    child: Element
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        # if child.tag == "parameter":
        #     parse_parameter(child, _parent=ParentType.SIMPLE_TYPE)
        #     continue
        if child.tag == "validValues":
            parse_validValues(child, _parent=ParentType.SIMPLE_TYPE)
            continue

        print(child.tag)
        raise NotImplementedError

def main() -> None:
    tree = ET.parse("SportsAPING.xml")
    root: Element = tree.getroot()

    child: Element
    for child in root:
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

    print("done")

if __name__ == "__main__":
    main()
