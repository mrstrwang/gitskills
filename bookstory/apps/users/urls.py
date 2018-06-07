"""bookstory URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url

from users import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.login, name='login'),
    url(r'^login_check/$', views.login_check, name='login_check'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^user/$', views.user, name='user'),
    url(r'^user_center_order/(?P<page>\d+)?/?$',views.user_center_order,name='user_center_order'),
    url(r'^user_center_site/$',views.user_center_site,name='user_center_site'),
    url(r'^verifycode/$',views.verifycode,name='verifycode'),
    url(r'^active/(?P<token>.*)/$',views.register_active,name='active')
]
