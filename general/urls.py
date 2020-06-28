from django.urls import path

from .views import job104, job1111, job518, robotstxt

urlpatterns = [
    path('robots.txt', robotstxt.RobotsTxtView.as_view(), name='robotstxt'),

    path('104/<str:keyword>', job104.Job104View.as_view(), name='job104'),
    path('1111/<str:keyword>', job1111.Job1111View.as_view(), name='job1111'),
    path('518/<str:keyword>', job518.Job518View.as_view(), name='job518'),
]
