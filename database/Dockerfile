FROM postgres:18 AS build

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
    && make install \
    && rm -rf /tmp/age

RUN git clone --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make \
    && make install \
    && rm -rf /tmp/pgvector

RUN mkdir -p /init-scripts \
    && echo "CREATE EXTENSION IF NOT EXISTS age;" > /init-scripts/01_age.sql \
    && echo "CREATE EXTENSION IF NOT EXISTS vector;" > /init-scripts/02_vector.sql

FROM postgres:18

RUN apt-get update && apt-get install -y --no-install-recommends locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY --from=build /usr/lib/postgresql/18/lib/age.so /usr/lib/postgresql/18/lib/
COPY --from=build /usr/share/postgresql/18/extension/age* /usr/share/postgresql/18/extension/

COPY --from=build /usr/lib/postgresql/18/lib/vector.so /usr/lib/postgresql/18/lib/
COPY --from=build /usr/share/postgresql/18/extension/vector* /usr/share/postgresql/18/extension/

COPY --from=build /init-scripts/*.sql /docker-entrypoint-initdb.d/

CMD ["postgres", "-c", "shared_preload_libraries=age"]
