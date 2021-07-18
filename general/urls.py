from django.urls import path

from .views import bookwalker, cakeresume, dcard, index, job104, job1111, job518, momoshop, pchome, plurk, rent591, robotstxt, shopee, youtube

urlpatterns = [
    path('', index.IndexView.as_view(), name='index'),
    path('robots.txt', robotstxt.RobotsTxtView.as_view(), name='robotstxt'),

    path('104/<str:keyword>', job104.Job104View.as_view(), name='job104'),
    path('1111/<str:keyword>', job1111.Job1111View.as_view(), name='job1111'),
    path('518/<str:keyword>', job518.Job518View.as_view(), name='job518'),
    path('bookwalker-lightnovel', bookwalker.BookwalkerLightNovelView.as_view(), name='bookwalker_lightnovel'),
    path('cakeresume/<str:keyword>', cakeresume.CakeResumeView.as_view(), name='cakeresume'),
    path('dcard/board/<str:board>', dcard.DcardBoardView.as_view(), name='dcard_board'),
    path('dcard/main', dcard.DcardMainView.as_view(), name='dcard_main'),
    path('momoshop/<str:keyword>', momoshop.MomoshopView.as_view(), name='momoshop'),
    path('pchome/<str:keyword>', pchome.PChomeView.as_view(), name='pchome'),
    path('pchome-lightnovel', pchome.PChomeLightNovelView.as_view(), name='pchome_lightnovel'),
    path('plurk/search/<str:keyword>', plurk.PlurkSearchView.as_view(), name='plurk_search'),
    path('plurk/top/<str:lang>', plurk.PlurkTopView.as_view(), name='plurk_top'),
    path('rent591/<int:region>/<str:keyword>', rent591.Rent591View.as_view(), name='rent591'),
    path('shopee/<str:keyword>', shopee.ShopeeView.as_view(), name='shopee'),
    path('youtube/<str:keyword>', youtube.YouTubeView.as_view(), name='youtube'),
]
