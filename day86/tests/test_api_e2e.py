from ai_testing.api_e2e import StreamEvent, combine_text, parse_sse, validate_e2e_response


def test_sse_parser_keeps_event_type_id_and_multiline_data():
    events = parse_sse('event: token\nid: 1\ndata: {"text":"退"}\n\n' 'event: token\ndata: 款\n\n')

    assert events == [
        StreamEvent("token", '{"text":"退"}', "1"),
        StreamEvent("token", "款"),
    ]
    assert combine_text(events) == "退款"


def test_e2e_validator_reuses_chat_contract_and_adds_request_id():
    assert validate_e2e_response({"answer": "ok", "sources": [], "request_id": "r1"}) == []
    assert "request_id 必须是字符串" in validate_e2e_response(
        {"answer": "ok", "sources": [], "request_id": 1}
    )
