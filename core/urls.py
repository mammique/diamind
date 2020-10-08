from django.urls import path, re_path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    re_path('^$',                             views.home,                                                            name='home'),
    re_path('^nav/(?P<path>[\/0-9].*)$',      views.nav,                                                             name='nav'),
    re_path('^slide/(?P<path>[\/0-9].*)$',    views.nav,                                            {'slide': True}, name='slide',),
    re_path('^entry/create/$',                views.entry_create,                                                    name='entry_create'),
    re_path('^entry/update/(?P<pk>[0-9]+)/$', views.entry_update,                                                    name='entry_update'),
    re_path('^entry/delete/(?P<pk>[0-9]+)/$', views.entry_delete,                                                    name='entry_delete'),
	re_path('^entry/autocomplete/$',          views.EntryAutocomplete.as_view(create_field='name'),                  name='entry_autocomplete'),

]