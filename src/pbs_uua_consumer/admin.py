from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy, ugettext as _
from django import http, template
from django.shortcuts import render_to_response
from pbs_uua_consumer.models import Nonce, Association, UserOpenID
from pbs_uua_consumer.store import DjangoOpenIDStore


class NonceAdmin(admin.ModelAdmin):
    list_display = ('server_url', 'timestamp')
    actions = ['cleanup_nonces']

    def cleanup_nonces(self, request, queryset):
        store = DjangoOpenIDStore()
        count = store.cleanupNonces()
        self.message_user(request, "%d expired nonces removed" % count)
    cleanup_nonces.short_description = "Clean up expired nonces"

admin.site.register(Nonce, NonceAdmin)


class AssociationAdmin(admin.ModelAdmin):
    list_display = ('server_url', 'assoc_type')
    list_filter = ('assoc_type',)
    search_fields = ('server_url',)
    actions = ['cleanup_associations']

    def cleanup_associations(self, request, queryset):
        store = DjangoOpenIDStore()
        count = store.cleanupAssociations()
        self.message_user(request, "%d expired associations removed" % count)
    cleanup_associations.short_description = "Clean up expired associations"

admin.site.register(Association, AssociationAdmin)


class UserOpenIDAdmin(admin.ModelAdmin):
    list_display = ('user', 'claimed_id')
    search_fields = ('claimed_id',)

admin.site.register(UserOpenID, UserOpenIDAdmin)


# Support for allowing openid authentication for /admin (django.contrib.admin)
if getattr(settings, 'OPENID_USE_AS_ADMIN_LOGIN', False):
    from django.http import HttpResponseRedirect
    from pbs_uua_consumer import views

    def _openid_login(self, request, error_message='', extra_context=None):
        if request.user.is_authenticated():
            if not request.user.is_staff:
                return views.render_failure(
                    request, "User %s does not have admin access."
                    % request.user.username)
            return views.render_failure(
                request, "Unknown Error: %s" % error_message)
        else:
            request.session.set_test_cookie()
            context = {
                'title': _('Log in'),
                'app_path': request.get_full_path(),
                'error_message': error_message,
                'root_path': self.root_path,
                'sso_js_url': settings.OPENID_SSO_SERVER_JS_URL,
                'sso_url': "%s?next=%s" % (settings.LOGIN_URL,request.get_full_path()),
                'popup_mode': settings.OPENID_USE_POPUP_MODE,
            }
            context.update(extra_context or {})
            context_instance = template.RequestContext(request, current_app=self.name)
            return render_to_response(admin.sites.AdminSite.login_template or 'admin/login.html', context,
                context_instance=context_instance
            )
            # Redirect to openid login path,
            #return HttpResponseRedirect(
                #settings.LOGIN_URL + "?next=" + request.get_full_path())

    # Overide the standard admin login form.
    admin.sites.AdminSite.login_template = '/home/notroot/projects/merlin/src/merlin/apps/src/pbs_uua_consumer/templates/admin/login.html'
    admin.sites.AdminSite.display_login_form = _openid_login
