from unittest.mock import Mock
import pytest
from fastsession import FastSessionMiddleware


@pytest.fixture
def middleware():
    return FastSessionMiddleware(
        app=None,  # 実際のテストでは有効なASGIアプリを提供する
        secret_key="test",
        skip_session_header=[
            {"header_name": "X-FastSession-Skip", "header_value": "skip"},
            {"header_name": "X-Another-Skip-Header", "header_value": "skip"}
        ]
    )


def test_should_skip_session_management_with_multiple_skip_headers(middleware):
    # スキップするヘッダが複数存在する場合、それぞれがTrueを返すことを確認する
    request1 = Mock()
    request1.headers = {"X-FastSession-Skip": "skip"}
    assert middleware.should_skip_session_management_by_checking_header(request1) == True

    request2 = Mock()
    request2.headers = {"X-Another-Skip-Header": "skip"}
    assert middleware.should_skip_session_management_by_checking_header(request2) == True


def test_should_not_skip_session_management_with_multiple_skip_headers_and_different_values(middleware):
    # スキップするヘッダが複数存在するが、値が異なる場合、それぞれがFalseを返すことを確認する
    request1 = Mock()
    request1.headers = {"X-FastSession-Skip": "other"}
    assert middleware.should_skip_session_management_by_checking_header(request1) == False

    request2 = Mock()
    request2.headers = {"X-Another-Skip-Header": "other"}
    assert middleware.should_skip_session_management_by_checking_header(request2) == False
