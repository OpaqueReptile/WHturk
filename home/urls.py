from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from . import views
from views import HomeView

urlpatterns = [
            url(r'^$', views.index, name='index'),
            url(r'^profile/$', login_required(HomeView.as_view(), redirect_field_name=None)),
            url(r'^login/$', views.login, name='user_login'),
            url(r'^logout/$', views.logout, name='user_logout'),
            url('', include("social.apps.django_app.urls", namespace='social')),
            ]
