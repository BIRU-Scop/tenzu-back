# Use the official Python image from the Docker Hub
FROM python:3.12 AS base-image

# Set environment variables
#ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update &&\
  apt-get install -y --no-install-recommends\
     # python-ldap dependencies
     build-essential=12.9 &&\
  apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
RUN pip install uv



####
# Production part
####

FROM base-image AS production-image
WORKDIR /tenzu
COPY ./src/ /tenzu/
COPY ./buildrun/docker/tenzu/requirements/prod.txt /tenzu/prod.txt
RUN uv pip sync --system /tenzu/prod.txt && rm /tenzu/prod.txt
RUN python ./__main__.py i18n compile-catalog

####
# Testing part TODO to do
####

FROM base-image AS base-test-image
WORKDIR /tenzu
RUN echo "must be implemented"

####
# DEVELLOPEMENT part
####

FROM base-image AS dev-image
WORKDIR /tenzu
RUN apt-get update && apt-get install -y --no-install-recommends gettext && apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
COPY ./buildrun/docker/tenzu/requirements/devel.txt /tenzu/devel.txt
RUN uv pip sync --system /tenzu/devel.txt && rm /tenzu/devel.txt



# Install dependencies



# Expose port 8000 to the host
EXPOSE 8000

# Run the Django development server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
