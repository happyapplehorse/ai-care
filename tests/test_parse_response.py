import pytest
from typing import Generator

from ai_care import AICare
from ai_care.parse_response import parse_response, _extract_info


@pytest.fixture
def ai_care():
    ai_care = AICare()
    yield ai_care
    ai_care.clear_timer(clear_preserved=True, default_task_num_authority_external="Highest")

def test_parse_response(ai_care: AICare):
    # Setup
    response1 = "AA000101:stay silent"
    response2 = "AA000202:speak content"
    response3 = "AA000303:content"
    response_stream1 = (x for x in ["AA", "0001", "01", ":stay ", "si", "lent"])
    response_stream2 = (x for x in ["AA", "0002", "0", "2:spe", "ak ", "now"])
    response_stream3 = (x for x in ["AA", "0002", "02", ":spe", "ak ", "now"])
    response_stream4 = (x for x in ["AA", "0003", "03", ":parameter ", "content"])
    
    # Action
    choice_code1, content1 = parse_response(ai_care=ai_care, response=response1)
    choice_code2, content2 = parse_response(ai_care=ai_care, response=response2)
    choice_code3, content3 = parse_response(ai_care=ai_care, response=response3)
    choice_code_stream1, content_stream1 = parse_response(ai_care=ai_care, response=response_stream1)
    choice_code_stream2, content_stream2 = parse_response(ai_care=ai_care, response=response_stream2)
    choice_code_stream3, content_stream3 = parse_response(ai_care=ai_care, response=response_stream3)
    choice_code_stream4, content_stream4 = parse_response(ai_care=ai_care, response=response_stream4)
    
    # Assert
    assert choice_code1 == "01"
    assert content1 == "stay silent"
    assert choice_code2 == "02"
    assert content2 == "speak content"
    assert choice_code3 == "03"
    assert content3 == "content"
    assert choice_code_stream1 == "01"
    assert content_stream1 == "stay silent"
    assert choice_code_stream2 == "02"
    assert isinstance(content_stream2, Generator)
    assert ''.join(x for x in content_stream2) == "speak now"
    assert choice_code_stream3 == "02"
    assert ''.join(x for x in content_stream3) == "speak now"
    assert choice_code_stream4 == "03"
    assert content_stream4 == "parameter content"

def test_extract_info():
    # Setup
    case1 = "AA0"
    case2 = "ABCd04"
    case3 = "ABCd4560"
    case4 = "AA000202:content"

    # Action
    code1, content1 = _extract_info(case1)
    code2, content2 = _extract_info(case2)
    code3, content3 = _extract_info(case3)
    code4, content4 = _extract_info(case4)

    # Assert
    assert code1 == ("AA", None, None, None)
    assert content1 == None
    assert code2 == ("AB", "Cd", "04", None)
    assert content2 == None
    assert code3 == ("AB", "Cd", "45", "60")
    assert content3 == None
    assert code4 == ("AA", "00", "02", "02")
    assert content4 == "content"
