import os
import random
import string

os.environ['SENTRY_DSN'] = ''

from .settings import *  # noqa: F403,F401

ALLOWED_HOSTS = [
    '127.0.0.1',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
LOGGING = {}
SECRET_KEY = ''.join(
    random.SystemRandom().choice(string.ascii_letters) for _ in range(50)
)

# Test environment  # noqa: E402
from django.core.management import execute_from_command_line  # noqa: E402

execute_from_command_line(['', 'makemigrations'])
execute_from_command_line(['', 'migrate'])
