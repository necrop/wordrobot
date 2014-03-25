from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login
from django.contrib import admin

from apps.root.views import homepage

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wordrobot.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', homepage),
    url(r'^home/?$', homepage),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/', login),
    url(r'^apps/textmetrics/', include('apps.tm.urls', namespace='tm', app_name='tm')),
)
