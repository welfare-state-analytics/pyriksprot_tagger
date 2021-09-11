from typing import List

from workflow.model import Protocol, convert, parse
from workflow.model.model import Speech


def test_convert_to_xml():

    template_name: str = "speeches.xml.jinja"
    protocol: Protocol = parse.ProtocolMapper.to_protocol("tests/test_data/fake/prot-1958-fake.xml")
    speeches: List[Speech] = protocol.to_speeches(merge_strategy='chain')

    assert protocol is not None

    converter: convert.ProtocolConverter = convert.ProtocolConverter(template_name)

    result: str = converter.convert(protocol, speeches, "prot-200203--18.xml")

    expected = """<?xml version="1.0" encoding="UTF-8"?>
<protocol name="prot-1958-fake" date="1958">
    <speech speaker="A" speech_id="c01" speech_date="1958" speech_index="1">
Hej! Detta är en mening.
Jag heter Ove.
Vad heter du?
    </speech>
    <speech speaker="B" speech_id="c03" speech_date="1958" speech_index="2">
Jag heter Adam.
    </speech>
    <speech speaker="B" speech_id="c03" speech_date="1958" speech_index="3">
Ove är dum.
    </speech>
</protocol>"""

    assert result == expected

    protocol: Protocol = parse.ProtocolMapper.to_protocol("tests/test_data/fake/prot-1958-fake.xml")
    speeches: List[Speech] = protocol.to_speeches(merge_strategy='n')

    result: str = converter.convert(protocol, speeches, "prot-200203--18.xml")

    expected = """<?xml version="1.0" encoding="UTF-8"?>
<protocol name="prot-1958-fake" date="1958">
    <speech speaker="A" speech_id="c01" speech_date="1958" speech_index="1">
Hej! Detta är en mening.
    </speech>
    <speech speaker="A" speech_id="c02" speech_date="1958" speech_index="2">
Jag heter Ove.
Vad heter du?
    </speech>
    <speech speaker="B" speech_id="c03" speech_date="1958" speech_index="3">
Jag heter Adam.
Ove är dum.
    </speech>
</protocol>"""
    assert result == expected

    protocol: Protocol = parse.ProtocolMapper.to_protocol(
        "tests/test_data/fake/prot-1958-fake.xml",
    )
    speeches: List[Speech] = protocol.to_speeches(merge_strategy='who')

    result: str = converter.convert(protocol, speeches, "prot-200203--18.xml")

    expected = """<?xml version="1.0" encoding="UTF-8"?>
<protocol name="prot-1958-fake" date="1958">
    <speech speaker="A" speech_id="c01" speech_date="1958" speech_index="1">
Hej! Detta är en mening.
Jag heter Ove.
Vad heter du?
    </speech>
    <speech speaker="B" speech_id="c03" speech_date="1958" speech_index="2">
Jag heter Adam.
Ove är dum.
    </speech>
</protocol>"""
    assert result == expected
