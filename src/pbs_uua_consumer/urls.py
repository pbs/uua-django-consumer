from django.conf.urls.defaults import *

urlpatterns = patterns('pbs_uua_consumer.views',
    (r'^login/$', 'login_begin'),
    (r'^complete/$', 'login_complete'),
)
