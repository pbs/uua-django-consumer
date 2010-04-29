from django.test import TestCase
from django.test.client import Client
from django.http import Http404
from pbs_uua_consumer import models
from django.contrib.auth.models import User, Group

class GenericTestCase(TestCase):
    fixtures = ['test_taxonomy.json',
                'test_stations.json',
                'test_programs.json',
                'test_users.json',
                'test_webobjects.json']
    
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
        from pbs_uua_consumer import models
        reload(models)
        
        from pbs_uua_consumer.auth import OpenIDBackend
        self.backend = OpenIDBackend()
        
    
    def test_get_user(self):
        user = self.backend.get_user(1)
        self.failUnlessEqual(user.username, None)
        
        user = self.backend.get_user(2)
        self.failUnlessEqual(user.username, "admin")
    
    

    
    
    
    
