#!/bin/bash

create_sql=`mktemp`

if [ -z "${POSTGRESQL_CONF_DIR:-}" ]; then
	POSTGRESQL_CONF_DIR=${PGDATA}
fi

cat <<EOF >${create_sql}
CREATE EXTENSION IF NOT EXISTS age;
EOF

if [ -z "${POSTGRESQL_PASSWORD:-}" ]; then
	POSTGRESQL_PASSWORD=${POSTGRES_PASSWORD:-}
fi
export PGPASSWORD="$POSTGRESQL_PASSWORD"

psql -U "${POSTGRES_USER}" postgres -f ${create_sql}
psql -U "${POSTGRES_USER}" template1 -f ${create_sql}

if [ "${POSTGRES_DB:-postgres}" != 'postgres' ]; then
    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -f ${create_sql}
fi
