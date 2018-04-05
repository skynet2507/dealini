from django.conf.urls import url

import views

urlpatterns = [
    url(r'create', views.generate_short_url, name='generate_url'),
    url(r'(?P<pk>\d+)/visits', views.get_url_visits, name='url_visits'),
    url(r'(?P<pk>\d+)/visitors', views.get_url_visitors, name='url_visitors'),
    url(r'(?P<url>\w{5})$', views.get_url, name="retrieve_url"),
    url(r'all', views.urls_list, name="urls_list"),

]