ARG POSTGRES_VERSION
FROM postgres:${POSTGRES_VERSION}

# Copy the SQL file into the container
RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./images/init-run-db.sql /docker-entrypoint-initdb.d/init.sql