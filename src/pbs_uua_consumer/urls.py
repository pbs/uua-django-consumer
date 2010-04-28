from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
urlpatterns = patterns('pbs_uua_consumer.views',
    url(r'^login/$', 'login_begin', name='login_begin'),
    url(r'^logo.gif$', 'logo', name='openid-logo'),
    (r'^complete/$', 'login_complete'),
)
