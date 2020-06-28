from django.http import HttpResponse
from django.views.generic import View

class RobotsTxtView(View):
    def get(self, *args, **kwargs):
        return HttpResponse("#\nUser-agent: *\nDisallow: *\n", content_type='text/plain')
