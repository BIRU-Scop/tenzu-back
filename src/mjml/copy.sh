#!/usr/bin/env zsh

mkdir -p ../emails/templates/ && mkdir -p ../emails/static/emails &&
  find ./templates/**/*.txt -type f -exec cp \{\} ../emails/templates/ \; &&
  find ./templates/static/emails/**/*.* -type f -exec cp \{\} ../emails/static/emails/ \;;
