__metaclass__ = type

from django.conf import settings
from django.contrib.auth.models import User, Group
from openid.consumer.consumer import SUCCESS
from openid.extensions import sreg
from pbs_uua_consumer.models import UserOpenID

"""
Custom authentication backend for the OpenId consumer.
For further information, consult
http://docs.djangoproject.com/en/dev/topics/auth/#writing-an-authentication-backend
"""


class IdentityAlreadyClaimed(Exception):
    pass


class OpenIDBackend:
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, **kwargs):
        openid_response = kwargs.get('openid_response')
        if openid_response is None:
            return None

        if openid_response.status != SUCCESS:
            return None

        user = None
        try:
            user_openid = UserOpenID.objects.get(
                claimed_id__exact=openid_response.identity_url)
        except UserOpenID.DoesNotExist:
            if getattr(settings, 'OPENID_CREATE_USERS', False):
                user = self.create_user_from_openid(openid_response)
        else:
            user = user_openid.user

        if user is None:
            return None

        if getattr(settings, 'OPENID_UPDATE_DETAILS_FROM_SREG', False):
            sreg_response = sreg.SRegResponse.fromSuccessResponse(
                openid_response)
            if sreg_response:
                self.update_user_details_from_sreg(user, sreg_response)

        return user

    def get_user_instance(self, username, email):
        """ this method can be overriden to update and return the instance of
        an existing user instead of creating a new user when logging in with
        OpenId
        """
        user = User.objects.create_user(username, email)
        user.save()
        return user

    def create_user_from_openid(self, openid_response):
        """ internal method for creating users from a correct OpenId auth flow """
        sreg_response = sreg.SRegResponse.fromSuccessResponse(openid_response)
        if sreg_response:
            nickname = sreg_response.get('nickname', 'openiduser')
            email = sreg_response.get('email', '')
        else:
            nickname = 'openiduser'
            email = ''

        # Pick a username for the user based on their nickname,
        # checking for conflicts.
        i = 1
        while True:
            username = nickname
            if i > 1:
                username += str(i)
            try:
                User.objects.get(username__exact=username)
            except User.DoesNotExist:
                break
            i += 1
        
        user = self.get_user_instance(username, email)

        if sreg_response:
            self.update_user_details_from_sreg(user, sreg_response)

        self.associate_openid(user, openid_response)
        return user

    def associate_openid(self, user, openid_response):
        """Associate an OpenID with a user account."""
        # Check to see if this OpenID has already been claimed.
        try:
            user_openid = UserOpenID.objects.get(
                claimed_id__exact=openid_response.identity_url)
        except UserOpenID.DoesNotExist:
            user_openid = UserOpenID(
                user=user,
                claimed_id=openid_response.identity_url,
                display_id=openid_response.endpoint.getDisplayIdentifier())
            user_openid.save()
        else:
            if user_openid.user != user:
                raise IdentityAlreadyClaimed(
                    "The identity %s has already been claimed"
                    % openid_response.identity_url)

        return user_openid

    def update_user_details_from_sreg(self, user, sreg_response):
        fullname = sreg_response.get('fullname')
        if fullname:
            # Do our best here ...
            if ' ' in fullname:
                user.first_name, _, user.last_name = fullname.rpartition(' ')
            else:
                user.first_name = u''
                user.last_name = fullname

        email = sreg_response.get('email')
        if email:
            user.email = email
        user.save()
