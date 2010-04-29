from django.test import TestCase
from django.test.client import Client
from django.http import Http404
from pbs_uua_consumer.auth import OpenIDBackend

class GenericTestCase(TestCase):
    
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        
        from merlin import settings
        reload(settings)
        from merlin.config import base
        reload(base)
        from merlin.config import testing
        reload(testing)
        from merlin.apps.core import models
        reload(models)
    
    def test_get_user(self):
        input = {'user_id' : 1}
        try:
            username = get_user(input.user_id)
            self.assertEqual(username, "admin")
        except:
            pass
    
    def test_authenticate(self):
        response = {'openid_response' : {'success' : True, }}
        try:
            authenticate(response)
        except:
            pass
    
    def test_bad_method(self):
        "Non existent methods should result in a 404"
        openid_consumer = consumer()
        get = rf.get('/uua/foo/')
        self.assertRaises(Http404, openid_consumer, get, 'foo/')
    
    def test_login_begin(self):
        "Can log in with an OpenID"
        openid_consumer = MyConsumer()
        post = rf.post('/uua/', {
            'openid_url': 'https://login.pbs.org/u/'
        })
        post.session = MockSession()
        response = openid_consumer(post)
        self.assertEqual(response['Location'], 'https://login.pbs.org/u/')
        self.assert_('openid_bits' in post.session)

    def test_login_discover_fail(self):
        "E.g. the user enters an invalid URL"
        openid_consumer = MyDiscoverFailConsumer()
        post = rf.post('/uua/', {
            'openid_url': 'not-an-openid'
        })
        post.session = MockSession()
        response = openid_consumer(post)
        self.assert_(openid_consumer.openid_invalid_message in str(response))
    
    def testLoginSuccess(self):
        "Simulate a successful login"
        openid_consumer = MyConsumer()
        openid_consumer.set_mock_response(
            status = consumer.SUCCESS,
            identity_url = 'https://login.pbs.org/u/',
        )
        get = rf.get('/uua/complete/', {'openid-args': 'go-here'})
        get.session = MockSession()
        response = openid_consumer(get, 'complete/')
        self.assertEqual(
            response.content, 'You logged in as https://login.pbs.org/u/'
        )
    
    def testLoginCancel(self):
        openid_consumer = MyConsumer()
        openid_consumer.set_mock_response(
            status = consumer.CANCEL,
            identity_url = 'https://login.pbs.org/u/',
        )
        get = rf.get('/uua/complete/', {'openid-args': 'go-here'})
        get.session = MockSession()
        response = openid_consumer(get, 'complete/')
        self.assert_(
            openid_consumer.request_cancelled_message in response.content
        )
    
    def testLoginFailure(self):
        openid_consumer = MyConsumer()
        openid_consumer.set_mock_response(
            status = consumer.FAILURE,
            identity_url = 'https://login.pbs.org/u/',
        )
        get = rf.get('/uua/complete/', {'openid-args': 'go-here'})
        get.session = MockSession()
        response = openid_consumer(get, 'complete/')
        self.assert_('Failure: ' in response.content)
    
    def testLoginSetupNeeded(self):
        openid_consumer = MyConsumer()
        openid_consumer.set_mock_response(
            status = consumer.SETUP_NEEDED,
            identity_url = 'https://login.pbs.org/u/',
        )
        get = rf.get('/uua/complete/', {'openid-args': 'go-here'})
        get.session = MockSession()
        response = openid_consumer(get, 'complete/')
        self.assert_(openid_consumer.setup_needed_message in response.content)
    
    def testLogo(self):
        openid_consumer = MyConsumer()
        get = rf.get('/uua/logo/')
        response = openid_consumer(get, 'logo/')
        self.assert_('image/gif' in response['Content-Type'])
