# feedgen [![CircleCI](https://circleci.com/gh/hasname/feedgen.svg?style=svg)](https://circleci.com/gh/hasname/feedgen)

Generate Atom feeds for sites which do not support feeds, mostly in Taiwan.

## Install

You need to set up `.env` first.  The sample environment file is in `.env.sample`.

### 104 job and company feeds

`/104/` and `/104company/` search the public 104 website anonymously.
Both feeds use `FEEDGEN_104_PROXY` when set and otherwise inherit `FEEDGEN_HTTP_PROXY`.
If 104 rejects a request, the feed returns HTTP 502. A successful search with
zero matches returns an empty Atom feed with HTTP 200.

### Dcard feeds and cfsolve

`/dcard/board/` and `/dcard/main` use curl_cffi and run
[cfsolve](https://github.com/chris124567/cfsolve) when Cloudflare returns a
challenge. Failed requests return HTTP 503 with `Cache-Control: no-store`.

`make deploy` builds cfsolve locally before uploading anything to the server.
It checks out the revision pinned in `scripts/install-cfsolve.sh` under the local
`.cfsolve/` directory, installs rustup for the local user if needed, and builds
the `challenge` binary with the upstream Rust toolchain and locked Cargo
dependencies. Later deployments reuse this checkout and build cache. Set
`CFSOLVE_SOURCE_DIR` in `GNUmakefile.local` to use a checkout outside the project.

The local build machine needs Git, curl, CMake, a C/C++ compiler, clang, libclang,
and CA certificates. On Debian/Ubuntu, install these build prerequisites once:

```sh
sudo apt-get install build-essential ca-certificates clang cmake curl git libclang-dev
```

Bindgen uses the `clang` executable to discover system header directories.
An error such as `fatal error: 'stddef.h' file not found` during binding
generation can mean that clang or its resource headers are missing. The installer
checks that clang can parse `stddef.h` and `stdint.h` before starting the Rust
build, then exports its absolute path as `CLANG_PATH` for bindgen. For a custom
LLVM installation, set `CLANG_PATH` to its clang executable and ensure that
`LIBCLANG_PATH`, if set, selects a matching libclang installation.

For local development, run `make cfsolve` to perform the same local build.
Rust and crate downloads require network access; the first build can take
several minutes. A failed build stops deployment before any upload.

Only the binary, Safari profile, its two answer files, and the upstream license
are uploaded to `~/feedgen/.cfsolve-upload/`. `scripts/activate-cfsolve.sh` checks
the uploaded binary with `--help` before copying these files into `.cfsolve/`.
Both directories are excluded from the general application rsync, so source and
build caches are not uploaded or deleted. Existing `.env` paths remain valid.

Build on the same OS and CPU architecture as the server. For Linux, use glibc
and libstdc++ versions no newer than those on the server; this is a native build,
not a cross-compilation setup. The remote `--help` check catches incompatible
binaries or missing shared libraries before replacing the existing solver,
uploading `.env`, or restarting Feedgen. The server does not need Rust, CMake,
clang, or libclang. It still needs runtime libraries, CA certificates, and time
zone data. On Debian/Ubuntu:

```sh
sudo apt-get install ca-certificates libc6 libgcc-s1 libstdc++6 tzdata
```

On Linux, the machine running cfsolve needs its IANA time zone for date probes.
Install time zone data and configure `/etc/timezone`, or make `/etc/localtime`
a symlink to the appropriate file under `/usr/share/zoneinfo/`. Setting `TZ`
alone does not supply the zone name to cfsolve.

Use these values in Feedgen's `.env`. Paths are relative to the project directory,
which is also the systemd service's working directory:

```dotenv
FEEDGEN_CFSOLVE_BINARY="./.cfsolve/target/release/challenge"
FEEDGEN_CFSOLVE_PROFILE="./.cfsolve/profiles/safari-26-ios.json"
FEEDGEN_DCARD_IMPERSONATE="safari260_ios"
FEEDGEN_CFSOLVE_ATTEMPTS="3"
FEEDGEN_CFSOLVE_TIMEOUT="300"
```

Keep the profile's referenced answer files beside it, as in the cfsolve checkout.
The profile supplies the exact User-Agent for all Dcard requests. The
`FEEDGEN_DCARD_IMPERSONATE` target must match that profile; the bundled Safari iOS
profile uses `safari260_ios`. Replace any previous comma-separated Chrome list.
Dcard ignores `FEEDGEN_IMPERSONATE` and rejects lists of targets because a
clearance must keep the same browser identity. Other services retain their
existing impersonation settings.

`FEEDGEN_CFSOLVE_ATTEMPTS` limits solver invocations per request, including
rejected clearances. `FEEDGEN_CFSOLVE_TIMEOUT` is the timeout in seconds for each
invocation. Successful requests skip the solver. Temporary solver artifacts are
removed after each attempt. A session reuses clearance cookies for subsequent
requests to the same host.

Both clients use the same proxy and exit IP. Set `FEEDGEN_DCARD_PROXY` or
`FEEDGEN_HTTP_PROXY` to a proxy with a stable exit IP. Standard proxy environment
variables and `NO_PROXY` are resolved once when neither Feedgen setting is set.
For `gw.dataimpulse.com`, Feedgen adds a
[session ID](https://docs.dataimpulse.com/proxies/parameters/session-id) to the
username if one is absent, keeping it for the session. Other proxy credentials
and existing session IDs are preserved. A direct connection also works if its
exit IP remains stable.

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

The deployment first runs `scripts/install-cfsolve.sh` locally, uploads the
runtime files, and runs `scripts/activate-cfsolve.sh` on the server before
`uv sync` and the systemd restart. No cfsolve compilation runs on the server.

`feedgen.service` is a systemd user unit, therefore remember to use `systemctl --user` on the remote host.  Two things have to be set up once by hand before the first deploy:

* `uv` has to be reachable from a login shell of `DEPLOY_USER`, because `make deploy` installs the dependencies through `bash -lc`:

        ssh service-feedgen@server.example.com 'bash -lc "uv --version"'

* The account needs lingering, otherwise its systemd user manager stops along with the last session and the service does not come back after a reboot:

        sudo loginctl enable-linger service-feedgen

Set deployment values in the project root's `.env`. When this file is present,
`make deploy` copies it to `~/feedgen/.env` on the host with mode `0600` before
restarting the service. If the local file is absent, the host keeps its existing
`.env`. Django loads the file at startup.

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
