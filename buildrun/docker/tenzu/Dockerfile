# Use the official Python image from the Docker Hub
FROM python:3.12-slim-bookworm AS base-image

# Set environment variables
ENV PYTHONUNBUFFERED=1
RUN pip install uv


####
# Production
####

FROM base-image AS production-image
WORKDIR /tenzu
COPY ./src/ /tenzu/
COPY ./buildrun/docker/tenzu/requirements/prod.txt /tenzu/prod.txt
RUN  apt-get update && apt-get install -y --no-install-recommends gettext build-essential libpq-dev &&\
     uv pip sync --system /tenzu/prod.txt && rm /tenzu/prod.txt&& \
     apt-get purge -y --auto-remove build-essential &&\
     apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
# pass required env var so it does not crash validation, they will not be used
RUN TENZU_SECRET_KEY=secret TENZU_TOKENS__SIGNING_KEY=secret2 python ./__main__.py i18n compile-catalog

####
# Testing TODO to do
####

FROM base-image AS base-test-image
WORKDIR /tenzu
RUN echo "must be implemented"

####
# DEVELOPMENT
####

FROM base-image AS dev-image
WORKDIR /tenzu
COPY ./buildrun/docker/tenzu/requirements/devel.txt /tenzu/devel.txt
# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gettext build-essential libpq-dev &&\
    uv pip sync --system /tenzu/devel.txt && rm /tenzu/devel.txt && \
    pip uninstall -y uv && pip cache purge &&\
    apt-get purge -y --auto-remove build-essential &&\
    apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

# Expose port 8000 to the host
EXPOSE 8000

# Run the Django development server
 CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=configurations.dev"]
