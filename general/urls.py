from django.urls import path

from .views import job104, robotstxt

urlpatterns = [
    path('robots.txt', robotstxt.RobotsTxtView.as_view(), name='robotstxt'),

    path('104/<str:keyword>', job104.Job104View.as_view(), name='job104'),
]
