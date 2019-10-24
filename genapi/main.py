import xml.etree.ElementTree as ET
from typing import Optional

from xml.etree.ElementTree import Element

OBSERVED_TYPES = set()
OBSERVED_ENUMS = set()

def strip_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None

    return " ".join([x.strip() for x in s.split("\n")]).strip()

def parse_description(el: Element):
    assert el.tag == "description"
    assert not el.attrib
    assert len(el) == 0
    if el.text is not None: # nullable string
        print(strip_string(el.text))

def parse_exceptions(el: Element):
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not strip_string(el.text)
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

def parse_value(el: Element) -> None:
    _id_str: str = el.attrib.pop("id")
    assert _id_str.isdigit()
    _id = int(_id_str)
    name = el.attrib.pop("name")
    OBSERVED_ENUMS.add(name)

    assert not el.attrib
    assert not strip_string(el.text)

    assert len(el) == 1
    parse_description(el[0])

    print(f"value {_id} {name}")

def parse_validValues(el: Element) -> None:
    assert not el.attrib
    assert not strip_string(el.text)

    for child in el:
        if child.tag == "value":
            parse_value(child)
            continue

        raise NotImplementedError(f"validValues child {child.tag}")

def parse_parameter(el: Element) -> None:
    try:
        mandatory = el.attrib.pop("mandatory")
        assert mandatory == "true"
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
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "validValues":
            parse_validValues(child)
            continue

        raise NotImplementedError

def parse_request(el: Element):
    assert el.tag == "request"
    assert not el.attrib
    assert not strip_string(el.text)
    for child in el:
        if child.tag == "parameter":
            parse_parameter(child)
            continue

        raise NotImplementedError


def parse_parameters(el: Element):
    assert el.tag == "parameters"
    assert not el.attrib
    assert not strip_string(el.text)
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
            parameters = parse_parameters(child)
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
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "parameter":
            parse_parameter(child)
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
    for child in el:
        if child.tag == "description":
            assert not description_observed
            description_observed = True
            parse_description(child)
            continue
        if child.tag == "parameter":
            parse_parameter(child)
            continue

        print(child.tag)
        raise NotImplementedError

def main():
    tree = ET.parse("SportsAPING.xml")
    root = tree.getroot()

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

        raise NotImplementedError(f"root {child.tag}")

if __name__ == "__main__":
    main()
