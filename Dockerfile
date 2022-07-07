#
FROM python:3.9
ENV WORKDIR=/srv/feedgen.hasname.com
WORKDIR ${WORKDIR}
COPY . ${WORKDIR}
RUN pip install poetry && \
    poetry install
ENTRYPOINT ["./entrypoint.sh"]
