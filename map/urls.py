from django.conf.urls import url

from . import views

urlpatterns = [
            url(r'^$', views.index, name='index'),
            url(r'^kspace_gen/$', views.kspace_gen, name='kspace_gen'),
            url(r'^req/$', views.rootAndDepth, name='root_and_depth'),
            url(r'^path/$', views.getPath, name='getPath'),
            ]
