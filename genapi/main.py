import xml.etree.ElementTree as ET
tree = ET.parse("SportsAPING.xml")
root = tree.getroot()

from typing import Optional

from xml.etree.ElementTree import Element

OBSERVED_TYPES = set()

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

def parse_request(el: Element):
    assert el.tag == "request"
    assert not el.attrib
    assert not strip_string(el.text)
    for child in el:
        if child.tag == "parameter":
            try:
                mandatory = child.attrib.pop("mandatory")
                assert mandatory == "true"
                mandatory = True
            except Exception:
                mandatory = False

            name = child.attrib.pop("name")
            _type = child.attrib.pop("type")
            OBSERVED_TYPES.add(_type)
            print(f"param {name}: {_type} (mandatory={mandatory})")

            assert not child.attrib
            assert not strip_string(child.text)
            assert len(child) == 1
            parse_description(child[0])
            continue

        raise NotImplementedError


def parse_parameters(el: Element):
    assert el.tag == "parameters"
    assert not el.attrib
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

def parse_operation(el: Element):
    assert el.tag == "operation"
    name = el.attrib["name"]
    since = el.attrib["since"]
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


for child in root:
    if child.tag == "description":
        assert not child.attrib
        print(strip_string(child.text))
        continue
    if child.tag == "operation":
        parse_operation(child)
        continue

    raise NotImplementedError
