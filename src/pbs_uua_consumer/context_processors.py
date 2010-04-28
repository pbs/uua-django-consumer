from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

def openid_config(request):
    if hasattr(settings, 'OPENID_USE_POPUP_MODE'):
        popup_mode = settings.OPENID_USE_POPUP_MODE
    else:
        popup_mode = False

    sso_url = mark_safe(u"%s?next=%s" % (reverse('login_begin'), request.get_full_path()),)

    if hasattr(settings, 'OPENID_SSO_SERVER_JS_URL'):
        sso_js_url = settings.OPENID_SSO_SERVER_JS_URL
    else:
        sso_js_url = ''


    if settings.OPENID_USE_POPUP_MODE:
        href = u'javascript:void(null)" onClick="javascript:loadPopup();'
    else:
        href = u'%s?next=%s' % (reverse('login_begin'), request.get_full_path())

    openid_login_link = mark_safe(u'<a id="uua_login" href="%s">Login with your PBS account</a>' % href)

    return {'popup_mode': popup_mode,
            'sso_url': sso_url,
            'sso_js_url': sso_js_url,
            'openid_login_link': openid_login_link
            }
