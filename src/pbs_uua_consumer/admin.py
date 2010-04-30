from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy, ugettext as _
from django import http, template
from django.shortcuts import render_to_response
from pbs_uua_consumer.models import Nonce, Association, UserOpenID
from pbs_uua_consumer.store import DjangoOpenIDStore
from django.views.decorators.cache import never_cache

""" Integrates the application with the admin interface.
Registers admin models and the authentication backend with Django admin.
"""

class NonceAdmin(admin.ModelAdmin):
    """ OpenId Nonces admin form """

    list_display = ('server_url', 'timestamp')
    actions = ['cleanup_nonces']

    def cleanup_nonces(self, request, queryset):
        store = DjangoOpenIDStore()
        count = store.cleanupNonces()
        self.message_user(request, "%d expired nonces removed" % count)
    cleanup_nonces.short_description = "Clean up expired nonces"

admin.site.register(Nonce, NonceAdmin)


class AssociationAdmin(admin.ModelAdmin):
    """ OpenId Association admin form """
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
    """ OpenId user admin form """
    list_display = ('user', 'claimed_id')
    search_fields = ('claimed_id',)

admin.site.register(UserOpenID, UserOpenIDAdmin)


# Support for allowing openid authentication for /admin (django.contrib.admin)
if getattr(settings, 'OPENID_USE_AS_ADMIN_LOGIN', False):

    from django.http import HttpResponseRedirect
    from pbs_uua_consumer import views

    def _openid_login(self, request, error_message='', extra_context=None):
        context = {
                'title': _('Log in'),
                'app_path': request.get_full_path(),
                'error_message': error_message,
                'root_path': self.root_path,

            }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        if request.user.is_authenticated():
            if not request.user.is_staff:
                context['error_message']="User %s does not have admin access." % request.user.username
            else:
                context['error_message']="Unknown Error: %s" % error_message
        else:
            request.session.set_test_cookie()

        return render_to_response(admin.sites.AdminSite.login_template or 'admin/login.html', context,
                context_instance=context_instance)

    login_template = getattr(settings, 'OPENID_ADMIN_LOGIN_TEMPLATE', False)
    admin.sites.AdminSite.login_template = login_template or 'admin/openid.login.html'
    admin.sites.AdminSite.display_login_form = _openid_login
