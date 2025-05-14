ARG POSTGRES_VERSION="16.3"
FROM postgres:${POSTGRES_VERSION}

# Copy the SQL file into the container
RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./images/dagster-db/init.sql /docker-entrypoint-initdb.d/init.sql