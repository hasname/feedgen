# feedgen [![CircleCI](https://circleci.com/gh/hasname/feedgen.svg?style=svg)](https://circleci.com/gh/hasname/feedgen)

Generate Atom feeds for sites which do not support feeds, mostly in Taiwan.

## Install

You need to set up `.env` first.  The sample environment file is in `.env.sample`.

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

Then you can use `make deploy` to update the service.  Scripts in `GNUmakefile` will call `rsync` to update code via SSH and re-run `uwsgi` services via userland systemd.

## Supporting platforms

Recruting platform search systems (求職平台):
* https://meet.jobs/
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
* https://feedgen.hasname.com/meetjobs/test
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
