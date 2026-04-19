FROM timescale/timescaledb-ha:pg18 AS build

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    bison \
    build-essential \
    flex \
    git \
    ca-certificates \
    postgresql-server-dev-18 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch master https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && make \
    && make OPTFLAGS="-O3" install \
    && rm -rf /tmp/age

FROM timescale/timescaledb-ha:pg18

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-18-postgis-3 \
    postgresql-18-cron \
    postgresql-18-pg-wait-sampling \
    postgresql-18-repack \
    postgresql-plpython3-18 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/lib/postgresql/18/lib/age.so /usr/lib/postgresql/18/lib/
COPY --from=build /usr/share/postgresql/18/extension/age* /usr/share/postgresql/18/extension/

COPY docker-entrypoint-initdb.d/* /docker-entrypoint-initdb.d/

USER postgres

CMD ["postgres", "-c", "shared_preload_libraries=timescaledb,age,pg_cron,pg_stat_statements,pg_wait_sampling"]
