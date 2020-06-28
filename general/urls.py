from django.urls import path

from .views import job104, job1111, job518, pchome, plurk, robotstxt, shopee

urlpatterns = [
    path('robots.txt', robotstxt.RobotsTxtView.as_view(), name='robotstxt'),

    path('104/<str:keyword>', job104.Job104View.as_view(), name='job104'),
    path('1111/<str:keyword>', job1111.Job1111View.as_view(), name='job1111'),
    path('518/<str:keyword>', job518.Job518View.as_view(), name='job518'),
    path('pchome/<str:keyword>', pchome.PChomeView.as_view(), name='pchome'),
    path('plurk/top/<str:lang>', plurk.PlurkTopView.as_view(), name='plurk_top'),
    path('shopee/<str:keyword>', shopee.ShopeeView.as_view(), name='shopee'),
]
