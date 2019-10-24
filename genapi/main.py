import xml.etree.ElementTree as ET
tree = ET.parse("SportsAPING.xml")
root = tree.getroot()

from xml.etree.ElementTree import Element

OBSERVED_TYPES = set()

def parse_description(el: Element):
    assert el.tag == "description"
    assert not el.attrib
    assert len(el) == 0
    print(f"DESC {el.text.strip()}")

def parse_exceptions(el: Element):
    assert el.tag == "exceptions"
    assert not el.attrib
    assert not el.text.strip()
    for child in el:
        if child.tag == "exception":
            # type
            # description
            raise NotImplementedError
            continue

        print(child.tag)
        raise NotImplementedError

def parse_request(el: Element):
    assert el.tag == "request"
    assert not el.attrib
    assert not el.text.strip()
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
            print(f"param {name}: {_type} (mandatory={mandatory})")

            assert not child.attrib
            assert not child.text.strip()
            assert len(child) == 1
            parse_description(child[0].tag)

            OBSERVED_TYPES.add(_type) #TODO fix
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
            assert not child.text.strip()

            assert len(child) == 1
            parse_description(child[0].tag)

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
            #print("DESC", child.text.strip())
            continue
        if child.tag == "parameters":
            parameters = parse_parameters(child)
            continue

        raise NotImplementedError


for child in root:
    if child.tag == "description":
        assert not child.attrib
        print(child.text.strip())
        continue
    if child.tag == "operation":
        parse_operation(child)
        continue

    raise NotImplementedError
