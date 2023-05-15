import time

from fastsession.timed_signature_serializer import TimedSignatureSerializer


def test_token_expiration():
    """
    Test that a token with a 1 second expiration becomes invalid after 2 seconds.

    有効期限1秒のトークンが2秒後に無効になることをテストする。
    """
    serializer = TimedSignatureSerializer('MY_SECRET_KEY', expired_in=1)
    dict_obj = {'session_id': 999}
    token = serializer.encode(dict_obj)

    time.sleep(2)
    data, err = serializer.decode(token)
    assert data is None and err == "SignatureExpired", "Token did not expire as expected."


def test_token_no_expiration():
    """
    Test that a token with no expiration remains valid even after 2 seconds.

    有効期限がないトークンが2秒後も有効であることをテストする。
    """
    serializer = TimedSignatureSerializer('MY_SECRET_KEY', expired_in=0)
    dict_obj = {'session_id': 999}
    token = serializer.encode(dict_obj)

    time.sleep(2)
    data, err = serializer.decode(token)
    assert data is not None and err is None and data['session_id'] == 999, "Failed to decode or session_id does not match."


def test_token_tampering():
    """
    Test that tampering with a token makes it invalid.

    トークンを改ざんすると無効になることをテストする。
    """
    serializer = TimedSignatureSerializer('MY_SECRET_KEY', expired_in=3600)
    dict_obj = {'session_id': 999}
    token = serializer.encode(dict_obj)

    tampered_token = token[:-1] + 'a'
    data, err = serializer.decode(tampered_token)
    assert data is None and err == "InvalidSignature", "Tampered token did not cause an error as expected."
