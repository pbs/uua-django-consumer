from django.contrib.auth.models import User
from django.db import models

from django.db.models.signals import pre_delete

class Nonce(models.Model):
    server_url = models.CharField(max_length=2047)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=40)

    def __unicode__(self):
        return u"Nonce: %s, %s" % (self.server_url, self.salt)


class Association(models.Model):
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)

    def __unicode__(self):
        return u"Association: %s, %s" % (self.server_url, self.handle)

def delete_openid_user(sender, instance=None, **kwargs):
    if instance:
        try:
            openid_user = UserOpenID.objects.get(user=instance)
            openid_user.delete()
        except UserOpenID.DoesNotExist:
            pass

pre_delete.connect(delete_openid_user, sender=User)

class UserOpenID(models.Model):
    user = models.ForeignKey(User)
    claimed_id = models.CharField(max_length=255, unique=True)
    display_id = models.TextField(max_length=2047)
