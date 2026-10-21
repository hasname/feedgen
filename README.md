# feedgen [![CircleCI](https://circleci.com/gh/hasname/feedgen.svg?style=svg)](https://circleci.com/gh/hasname/feedgen)

Generate Atom feeds for sites which do not support feeds, mostly in Taiwan.

## Install

You need to set up `.env` first.  The sample environment file is in `.env.sample`.

### Proxies

Set proxies in `.env`, then restart the service:

```dotenv
# Optional default for all services.
FEEDGEN_HTTP_PROXY="socks5h://127.0.0.1:1080"

# Each service can use its own proxy.
FEEDGEN_DCARD_PROXY="socks5h://127.0.0.1:1081"
FEEDGEN_SHOPEE_PROXY="socks5h://user:password@proxy.example:1080"
```

`FEEDGEN_<SERVICE>_PROXY` takes precedence over `FEEDGEN_HTTP_PROXY` for both HTTP
and HTTPS requests. Missing or empty service values inherit the default. The
default now applies to all services, including those that previously did not use
`FEEDGEN_HTTP_PROXY`. If neither is set, Requests keeps its usual behavior,
including support for the standard `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and
`NO_PROXY` environment variables. Explicit Feedgen proxy settings take precedence
over those standard proxy variables.

Supported service names are `104`, `1111`, `518`, `BOOKWALKER`, `CAKERESUME`,
`DCARD`, `MOMOSHOP`, `PCHOME`, `PLURK`, `RENT591`, `SHOPEE`,
`TAIPEIMETROTIMETABLE`, `YOURATOR`, and `YOUTUBE`. All endpoints for the same
service share its proxy, such as Dcard's board and main feeds.

Use `socks5h://` to resolve destination hostnames through the proxy, or `socks5://`
to resolve them locally. SOCKS5 authentication uses `user:password@host:port`;
percent-encode special characters in credentials. HTTP proxies (`http://`) are
also supported. The existing PySocks dependency supplies SOCKS support; see the
[Requests proxy documentation](https://requests.readthedocs.io/en/latest/user/advanced/#proxies).

## Run

We use `uv` to manage the running environment along with `uwsgi` to run the uWSGI server, therefore you choose whatever you like to adopt these utilities.

## Development

There are two commands in `GNUmakefile` to help you develop:

    make rundev
    make test

## Update

For `GNUmakefile.local`, you can set something like this:

    #
    DEPLOY_HOST=    server.example.com
    DEPLOY_USER=    service-feedgen

Then you can use `make deploy` to update the service.  Scripts in `GNUmakefile` will call `rsync` to update code via SSH, run `uv sync` on the remote host, install `feedgen.service` into `~/.config/systemd/user/`, and then reload and restart the `uwsgi` service via userland systemd.

`feedgen.service` is a systemd user unit, therefore remember to use `systemctl --user` on the remote host.  Two things have to be set up once by hand before the first deploy:

* `uv` has to be reachable from a login shell of `DEPLOY_USER`, because `make deploy` installs the dependencies through `bash -lc`:

        ssh service-feedgen@server.example.com 'bash -lc "uv --version"'

* The account needs lingering, otherwise its systemd user manager stops along with the last session and the service does not come back after a reboot:

        sudo loginctl enable-linger service-feedgen

Please note that `.env` lives on the remote host only.  It is listed in `.gitignore`, which `rsync` uses for `--exclude-from`, so `make deploy` neither uploads nor deletes it.  The application loads it with `python-dotenv` from the current working directory, which is why the unit sets `WorkingDirectory=%h/feedgen`.

## Supporting platforms

Recruting platform search systems (求職平台):
* https://www.104.com.tw/
* https://www.1111.com.tw/
* https://www.518.com.tw/
* https://www.cakeresume.com/
* https://www.yourator.co/

EC search systems (電子商務平台):
* https://24h.pchome.com.tw/ (including other PChome's EC systems)
* https://shopee.tw/
* https://www.momoshop.com.tw/

Housing platform (租屋平台):
* https://rent.591.com.tw/

Social networks (社群平台):
* https://www.dcard.tw/ (main section)
* https://www.plurk.com/ (popular section)
* https://www.youtube.com/ (search system)

Others (其他):
* https://24h.pchome.com.tw/books/store/?fq=/R/DJAZ/new
* https://web.metro.taipei/img/ALL/timetables/079a.PDF (Taipei metro timetable)
* https://www.bookwalker.com.tw/more/fiction/1/3

## Endpoint

We have set up a public service since I use it and you can test it as well, but please set up your own service if you use it heavily.

* https://feedgen.hasname.com/

## Examples

* https://feedgen.hasname.com/104/devops
* https://feedgen.hasname.com/104company/devops
* https://feedgen.hasname.com/1111/devops
* https://feedgen.hasname.com/518/devops
* https://feedgen.hasname.com/bookwalker-lightnovel
* https://feedgen.hasname.com/bookwalker-manga
* https://feedgen.hasname.com/cakeresume/devops
* https://feedgen.hasname.com/dcard/board/mood
* https://feedgen.hasname.com/dcard/main
* https://feedgen.hasname.com/momoshop/測試
* https://feedgen.hasname.com/pchome-lightnovel
* https://feedgen.hasname.com/pchome/測試
* https://feedgen.hasname.com/plurk/search/test
* https://feedgen.hasname.com/plurk/top/zh
* https://feedgen.hasname.com/rent591/1/忠孝東路 (region = `1` means `台北市`, please check 591 site)
* https://feedgen.hasname.com/shopee/測試
* https://feedgen.hasname.com/taipeimetrotimetable/079a
* https://feedgen.hasname.com/yourator/測試
* https://feedgen.hasname.com/youtube/測試

## License

See [LICENSE](LICENSE).
