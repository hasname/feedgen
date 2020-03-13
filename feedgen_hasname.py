#!/usr/bin/env python3

import feedgen_hasname


app = feedgen_hasname.FeedgenHasname()

if __name__ == '__main__':
    app.main()
else:
    # uWSGI
    app.init_sentry()
    application = app.app
