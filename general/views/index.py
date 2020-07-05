from django.shortcuts import redirect
from django.views.generic import View

class IndexView(View):
    def get(self, *args, **kwargs):
        return redirect('https://github.com/hasname/feedgen')
