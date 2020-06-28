from django.urls import path

from .views import robotstxt

urlpatterns = [
    path('robots.txt', robotstxt.RobotsTxtView.as_view(), name='robotstxt'),
]
