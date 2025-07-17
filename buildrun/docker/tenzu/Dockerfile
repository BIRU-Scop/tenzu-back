# Use the official Python image from the Docker Hub
FROM python:3.12-slim-bookworm AS base-image

# Set environment variables
ENV PYTHONUNBUFFERED=1
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG EXTRA_PACKAGES=""


####
# Production
####

FROM base-image AS production-image
# creates a system user (-r), with no password, no home directory set, and no shell
RUN groupadd -r default-group && useradd -r -s /bin/false -g default-group default-user

COPY --chown=default-user:default-group ./src/ /tenzu/
# replace with --mount=type=bind in RUN once supported by our CI build
COPY --chown=default-user:default-group ./buildrun/docker/tenzu/requirements/prod.txt /tenzu/prod.txt
# prepare permission for future mounts
RUN mkdir -p /public/media /public/static && chown -R default-user:default-group /public

RUN  apt-get update && apt-get install -y --no-install-recommends gettext build-essential libpq-dev && \
     uv pip sync --system /tenzu/prod.txt && rm /tenzu/prod.txt && \
     (if [ -n "${EXTRA_PACKAGES}" ] ; then pip install ${EXTRA_PACKAGES}; fi) && \
     apt-get purge -y --auto-remove build-essential && \
     apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
USER default-user
WORKDIR /tenzu

# pass required env var so it does not crash validation, they will not be used
RUN TENZU_SECRET_KEY=secret TENZU_TOKENS__SIGNING_KEY=secret2 python ./__main__.py i18n compile-catalog
RUN TENZU_SECRET_KEY=secret TENZU_TOKENS__SIGNING_KEY=secret2 ./manage.py collectstatic --noinput

####
# DEVELOPMENT
####

FROM base-image AS dev-image
# replace with --mount=type=bind in RUN once supported by our CI build
COPY ./buildrun/docker/tenzu/requirements/devel.txt /tenzu/devel.txt
# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gettext build-essential libpq-dev && \
    uv pip sync --system /tenzu/devel.txt && rm /tenzu/devel.txt && \
    (if [ -n "${EXTRA_PACKAGES}" ] ; then pip install ${EXTRA_PACKAGES}; fi) && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
WORKDIR /tenzu

# Expose port 8000 to the host
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=configurations.dev"]
