import re
import urllib
from urlparse import urlsplit

from django.conf import settings
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, authenticate, login as auth_login)
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render_to_response

from openid.consumer.consumer import (
    Consumer, SUCCESS, CANCEL, FAILURE)
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg, pape

from pbs_uua_consumer.store import DjangoOpenIDStore
from pbs_uua_consumer.extensions import UIExtension, SignatureVerification
from pbs_uua_consumer.extensions import make_token

next_url_re = re.compile('^/[-\w/]+$')

def sanitise_redirect_url(redirect_to):
    """Sanitise the redirection URL."""
    # Light security check -- make sure redirect_to isn't garbage.
    is_valid = True
    if not redirect_to or ' ' in redirect_to:
        is_valid = False
    elif '//' in redirect_to:
        # Allow the redirect URL to be external if it's a permitted domain
        allowed_domains = getattr(settings,
            "ALLOWED_EXTERNAL_OPENID_REDIRECT_DOMAINS", [])
        s, netloc, p, q, f = urlsplit(redirect_to)
        # allow it if netloc is blank or if the domain is allowed
        if netloc:
            # a domain was specified. Is it an allowed domain?
            if netloc.find(":") != -1:
                netloc, _ = netloc.split(":", 1)
            if netloc not in allowed_domains:
                is_valid = False

    # If the return_to URL is not valid, use the default.
    if not is_valid:
        redirect_to = settings.LOGIN_REDIRECT_URL

    return redirect_to


def make_consumer(request):
    """Create an OpenID Consumer object for the given Django request."""
    # Give the OpenID library its own space in the session object.
    session = request.session.setdefault('OPENID', {})
    store = DjangoOpenIDStore()
    return Consumer(session, store)


def render_openid_request(request, openid_request, return_to, trust_root=None):
    """Render an OpenID authentication request."""
    if trust_root is None:
        trust_root = getattr(settings, 'OPENID_TRUST_ROOT',
                             request.build_absolute_uri('/'))

    if openid_request.shouldSendRedirect():
        redirect_url = openid_request.redirectURL(
            trust_root, return_to)
        return HttpResponseRedirect(redirect_url)
    else:

        form_html = openid_request.htmlMarkup(
            trust_root, return_to, form_tag_attrs={'id': 'openid_message'})

        return HttpResponse(form_html, content_type='text/html;charset=UTF-8')


def render_response(request, message=None, status=200, template_name='openid/response.html', redirect_to=None):
    """Render a response page to the user."""
    response = render_to_string(
        template_name, {
            'redirect_to': redirect_to,
            'message': message,
        }, context_instance=RequestContext(request))
    return HttpResponse(response, status=status)

def parse_openid_response(request):
    """Parse an OpenID response from a Django request."""
    current_url = request.build_absolute_uri()
    consumer = make_consumer(request)
    return consumer.complete(dict(request.REQUEST.items()), current_url)


def login_begin(request, popup_mode=1,template_name='openid/login.html',
                redirect_field_name=REDIRECT_FIELD_NAME):
    """Begin an OpenID login request, possibly asking for an identity URL."""
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    # Get the OpenID URL to try.  First see if we've been configured
    # to use a fixed server URL.
    openid_url = getattr(settings, 'OPENID_SSO_SERVER_URL', None)

    if openid_url is None:
        return HttpResponseRedirect(redirect_field_name)

    error = None
    # create the consumer based on Django request
    consumer = make_consumer(request)
    try:
        # openid.consumer implements a discovery method.
        # we use this to see if the openid_url is a valid
        # OpenId provider
        openid_request = consumer.begin(openid_url)
    except DiscoveryFailure, exc:
        return render_response(
            request, "OpenID discovery error: %s" % (str(exc),), status=200)

    # based on the instance configuration, add PBS extensions for correct
    # use of login.pbs.org
    if hasattr(settings,'UUA_CONSUMER_SHARED_KEY') and hasattr(settings,'UUA_CONSUMER_SECRET_KEY'):
        openid_request.addExtension(SignatureVerification(
                        settings.UUA_CONSUMER_SHARED_KEY,
                        settings.UUA_CONSUMER_SECRET_KEY,
                        make_token(64) #request token to sign
                    ))

    # if we use the popover mode, add the appropriate extension

    if popup_mode==1:
        popup_mode = getattr(settings, 'OPENID_USE_POPUP_MODE', False)
    else:
        popup_mode = False
    if popup_mode:
        openid_request.addExtension(UIExtension("popup"))

    # Request some user details.
    openid_request.addExtension(
        sreg.SRegRequest(optional=['email', 'fullname', 'nickname']))

    # Construct the request completion URL, including the page we
    # should redirect to.
    return_to = request.build_absolute_uri(reverse(login_complete))

    if redirect_to:
        if '?' in return_to:
            return_to += '&'
        else:
            return_to += '?'
        return_to += urllib.urlencode({redirect_field_name: redirect_to})

    return render_openid_request(request, openid_request, return_to)


def login_complete(request, redirect_field_name=REDIRECT_FIELD_NAME):
    """ Handle the OpenId response"""
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    openid_response = parse_openid_response(request)
    if not openid_response:
        # we have no response so we should send the RP endpoint message
        return render_response(
            request, 'This is an OpenID relying party endpoint.')
    popup = UIExtension.fromResponse(openid_response)
    if openid_response.status == SUCCESS:
        # authenticate using openid custom authentication backend
        user = authenticate(openid_response=openid_response)
        if user is not None:
            if user.is_active:
                # login the user
                auth_login(request, user)
                if popup:
                    return render_response(request, status=200, redirect_to=sanitise_redirect_url(redirect_to))
                else:
                    return HttpResponseRedirect(redirect_to=sanitise_redirect_url(redirect_to))
            else:
                return render_response(request, 'Disabled account')
        else:
            return render_response(request, 'Unknown user')
    elif openid_response.status == FAILURE:
        return render_response(
            request, 'OpenID authentication failed: %s' %
            openid_response.message)
    elif openid_response.status == CANCEL:
        return render_response(request, 'Authentication cancelled')
    else:
        assert False, (
            "Unknown OpenID response type: %r" % openid_response.status)


def logo(request):
    """ Serve the OpenId logo from this view. Allows quick embedding in forms"""
    return HttpResponse(
        OPENID_LOGO_BASE_64.decode('base64'), mimetype='image/gif'
    )



OPENID_LOGO_BASE_64 = """
R0lGODlhEAAQAMQAAO3t7eHh4srKyvz8/P5pDP9rENLS0v/28P/17tXV1dHEvPDw8M3Nzfn5+d3d
3f5jA97Syvnv6MfLzcfHx/1mCPx4Kc/S1Pf189C+tP+xgv/k1N3OxfHy9NLV1/39/f///yH5BAAA
AAAALAAAAAAQABAAAAVq4CeOZGme6KhlSDoexdO6H0IUR+otwUYRkMDCUwIYJhLFTyGZJACAwQcg
EAQ4kVuEE2AIGAOPQQAQwXCfS8KQGAwMjIYIUSi03B7iJ+AcnmclHg4TAh0QDzIpCw4WGBUZeikD
Fzk0lpcjIQA7
"""
