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

COPY --from=build /usr/lib/postgresql/18/lib/age.so /usr/lib/postgresql/18/lib/
COPY --from=build /usr/share/postgresql/18/extension/age* /usr/share/postgresql/18/extension/

COPY /docker-entrypoint-initdb.d/00-create-extension.sql /docker-entrypoint-initdb.d/00-create-extension.sql

CMD ["postgres", "-c", "shared_preload_libraries=timescaledb,age"]
