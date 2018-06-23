#!/usr/bin/env python3

from bottle import run
import os

if __name__ == '__main__':
    if os.environ.get('ON_HEROKU'):
        port = int(os.environ.get('PORT'))
    else:
        port = 8080

    run(host='localhost', port=port)
