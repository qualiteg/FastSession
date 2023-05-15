from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature


class TimedSignatureSerializer:
    """
        与えられた秘密鍵と有効期限を用いて、辞書型オブジェクトを署名付き文字列に変換するクラス。
        TimedJSONWebSignatureSerializer が Deprecated になったので近い機能を実装した
        This class converts a dictionary object into a signed string using the given secret key and expiration time.
    """

    def __init__(self, secret_key, expired_in=0):
        self.ser = URLSafeTimedSerializer(secret_key)
        self.expired_in = expired_in

    def encode(self, dict_obj):
        """
        辞書オブジェクトを署名付きの文字列にエンコード
        署名にはタイムスタンプが付与されるので、デコード時に署名の期限切れも判定可能
        :param dict_obj: 辞書オブジェクトを想定
        :return: 署名付き文字列

        Encodes a dictionary object into a signed string.
        The signature includes a timestamp, so it is possible to determine if the signature has expired at the time of decoding.
        :param dict_obj: A dictionary object is expected.
        :return: Signed string
        """
        return self.ser.dumps(dict_obj)

    def decode(self, token):
        """
        署名付き文字列(token)を元のPythonのオブジェクトにデコード
        署名が有効期限切れの場合、署名が改ざんなどにより無効の場合は None
        :param token:
        :param max_age:
        :return: デコードされたPythonのオブジェクトとエラーメッセージ

        Decodes a signed string (token) back into the original Python object.
        If the signature has expired or is invalid due to tampering, returns None.
        :param token:
        :param max_age:
        :return: Decoded Python object and error message
        """
        if token == None:
            return None, "NoTokenSpecified"
        try:
            if self.expired_in == 0:
                decoded_obj = self.ser.loads(token)
            else:
                decoded_obj = self.ser.loads(token, max_age=self.expired_in)
        except SignatureExpired as e:
            # 署名が期限切れ
            # The signature has expired
            return None, "SignatureExpired"
        except BadTimeSignature as e:
            # 署名が無効
            # The signature is invalid
            return None, "InvalidSignature"

        return decoded_obj, None


CASUAL_UT = False

if CASUAL_UT:
    serializer = TimedSignatureSerializer('MY_SECRET_KEY', expired_in=1)
    session_id = 1
    dict_obj = {'session_id': session_id}
    token = serializer.encode(dict_obj)
    data, err = serializer.decode(token)
    assert data is not None and err is None and data[
        'session_id'] == 1, "Failed to decode or session_id does not match."
