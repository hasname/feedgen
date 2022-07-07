import os
import random
import string

os.environ['SENTRY_DSN'] = ''

from .settings import *

ALLOWED_HOSTS = [ '127.0.0.1', ]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
LOGGING = {}
SECRET_KEY = ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(50))

# Test environment
import os
from django.core.management import execute_from_command_line

execute_from_command_line(['', 'makemigrations'])
execute_from_command_line(['', 'migrate'])
