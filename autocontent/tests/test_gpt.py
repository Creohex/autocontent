#!pytest -s


from ..gpt import Completion


def test_request_simple():
    compl = Completion()
    result = compl.request("Say 123")
    assert "123" in result
