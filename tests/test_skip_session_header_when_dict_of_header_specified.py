from unittest.mock import Mock
import pytest
from fastsession import FastSessionMiddleware


@pytest.fixture
def middleware():
    return FastSessionMiddleware(
        app=None,  # 実際のテストでは有効なASGIアプリを提供する
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"}
    )


def test_should_skip_session_management_by_checking_header_with_skip_header(middleware):
    # スキップするヘッダが存在する場合、Trueを返すことを確認する
    request = Mock()
    request.headers = {"X-FastSession-Skip": "skip"}

    assert middleware.should_skip_session_management_by_checking_header(request) == True


def test_should_skip_session_management_by_checking_header_without_skip_header(middleware):
    # スキップするヘッダが存在しない場合、Falseを返すことを確認する
    request = Mock()
    request.headers = {"X-Other-Header": "value"}

    assert middleware.should_skip_session_management_by_checking_header(request) == False


def test_should_skip_session_management_by_checking_header_with_skip_header_and_different_value(middleware):
    # スキップするヘッダが存在するが値が異なる場合、Falseを返すことを確認する
    request = Mock()
    request.headers = {"X-FastSession-Skip": "other"}

    assert middleware.should_skip_session_management_by_checking_header(request) == False
