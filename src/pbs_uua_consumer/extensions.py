from base64 import urlsafe_b64encode
from os import urandom
import time, hmac, hashlib
from binascii import hexlify

from openid.message import registerNamespaceAlias, \
     NamespaceAliasRegistrationError
from openid.extension import Extension
from openid import oidutil


ns_uri_ui_extension = 'http://pbs.org/openid/extensions/ui/1.0'
OPENID_UI_TYPE = 'http://pbs.org/openid/extensions/ui/1.0'
registerNamespaceAlias(ns_uri_ui_extension, 'ui')

ns_uri_signed = 'http://pbs.org/openid/extensions/signature_verification/1.0'
registerNamespaceAlias(ns_uri_signed, 'signature_verification')

"""
Custom extensions are defined here.
They are required by login.pbs.org for enhanced security and user experience.
"""
def make_token(length=32):
    return urlsafe_b64encode(urandom(length)).strip("=")


class UIExtension(Extension):
    ns_uri = ns_uri_ui_extension
    ns_alias = 'ui'

    def __init__(self, mode=None):
        self.mode = mode

    def __str__(self):
        return '<UIExtension mode:%s >' % (
            self.mode
        )
    def getExtensionArgs(self):
        return {
            'mode':self.mode,
        }

    @classmethod
    def fromRequest(cls, request):
        args = request.message.getArgs(cls.ns_uri)
        if args:
            return cls(args['mode'])

    @classmethod
    def fromResponse(cls, response):
        args = response.message.getArgs(cls.ns_uri)
        if args:
            return cls(args['mode'])

class SignatureVerification(Extension):
    ns_uri = ns_uri_signed
    ns_alias = 'signature_verification'

    def __init__(self, consumer_key, secret_key=None, request_token=None,
                hmac=None, timestamp=None):
        self.request_token = request_token or make_token()
        self.secret_key = secret_key
        self.consumer_key = consumer_key
        self.hmac = hmac
        self.timestamp = timestamp or int(time.time())

    def __str__(self):
        return '<SignatureVerification request_token:%s secret_key:%s consumer_key:%s hmac:%s timestamp:%s>' % (
            self.request_token, self.secret_key, self.consumer_key, self.hmac, self.timestamp
        )

    def getExtensionArgs(self):
        if not self.secret_key:
            raise RuntimeError("You haven't set the UUA_CONSUMER_SECRET_KEY value in your project settings file")

        self.hmac = self._make_hmac(self.secret_key)

        return {
            'request_token':self.request_token,
            'consumer_key':self.consumer_key,
            'hmac':self.hmac,
            'timestamp':str(self.timestamp)
        }

    def _make_hmac(self, secret):
        return hexlify(hmac.new(
                str(secret),
                "%s-%s" % (str(self.request_token), self.timestamp),
                hashlib.sha1
        ).digest())

    @classmethod
    def fromRequest(cls, request):
        args = request.message.getArgs(cls.ns_uri)
        if args:
            try:
                timestamp = int(args['timestamp'])
            except:
                timestamp = None
            return cls(args['consumer_key'],
                request_token = args['request_token'],
                hmac = args['hmac'],
                timestamp = timestamp
            )
