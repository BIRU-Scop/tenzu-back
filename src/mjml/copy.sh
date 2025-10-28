#!/usr/bin/env zsh

mkdir -p ../emails/templates/ && mkdir -p ../emails/static/emails &&
  find ./templates/**/*.txt.jinja -type f -exec cp \{\} ../emails/templates/ \; &&
  find ./templates/**/*.subject.jinja -type f -exec cp \{\} ../emails/templates/ \; &&
  find ./templates/static/emails/**/*.* -type f -exec cp \{\} ../emails/static/emails/ \;;
