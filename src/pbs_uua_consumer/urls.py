from django.conf.urls.defaults import *
"""
The consumer defines several views that need to be mapped
for communication with an OpenId endpoint.

login - openid request creation method. begins an openid flow
complete - handles an openid response
logo.gif - serves the openid logo for frontend
"""
urlpatterns = patterns('pbs_uua_consumer.views',
    url(r'^login/$', 'login_begin', name='login_begin'),
    url(r'^logo.gif$', 'logo', name='openid-logo'),
    (r'^complete/$', 'login_complete'),
)
