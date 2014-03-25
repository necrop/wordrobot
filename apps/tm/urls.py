from django.conf.urls import patterns, url

urlpatterns = patterns('apps.tm.views',
    url(r'^$', 'homepage'),
    url(r'^home$', 'homepage', name='home'),
    url(r'^c/(?P<author>[a-z]+)-(?P<title>[a-z0-9]+)$', 'display_canned', name='display_canned'),
    url(r'^u/(?P<identifier>[a-z0-9]+)$', 'display_stored', name='display_stored'),
    url(r'^list$', 'list_canned', name='list_canned'),
    url(r'^potluck$', 'random_document', name='random_document'),
    url(r'^experiment$', 'submission_form', name='submission_form'),
    url(r'^results$', 'submit', name='submit'),
    url(r'^definition/(?P<id>[0-9]*)$', 'fetch_definition', name='definition'),
    url(r'^info/(?P<page>[a-z]+)$', 'info', name='info'),
    url(r'^save$', 'save_text', name='save_text'),
    url(r'^thesaurus/(?P<idstring>[0-9,]*)$', 'fetch_thesaurus_alternatives', name='thesaurus'),
)
