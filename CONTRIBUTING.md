# How to contribute

First off, thank you for considering contributing to Tenzu.

As this project is in its early stage, we are not yet able to accept most forms of contribution,
be it features, documentation or bug reports. As such, we will not accept issues or pull 
requests through Github yet.

We are still fixing bugs and changing a lot of things every day so adding contribution
while the project is still this unstable would be too difficult.

We hope to have a more mature codebase to give you soon so we can fully embrace the 
collaboration spirit of opensource.

In the meantime, we would love to hear from you at our [community webstite](https://community.tenzu.net).
Whether it be about ideas that you have, how you have been using Tenzu or about your interest in
contributing in the future. We are very active there and you'll be able to receive news about our 
progress!

We try to keep our [ROADMAP](ROADMAP.md) up-to-date so that you know what to expect for 
the coming months.

# Community
We are very active at our [community webstite](https://community.tenzu.net) and always happy to get in 
touch with our users there.

# Guide

## Security Issues

See [SECURITY](SECURITY.md)

## App setup

See [INSTALL](INSTALL.md) to know how to set up your development environment, run the app,
launch the test, etc.

## Coding style

We use [precommit](https://pre-commit.com/) to check for and automatically fix
issues in coding style.
Run the following command to install pre-commit into your git hooks and have it run on every commit:
```shell
pre-commit install
```
For more information on how it works, see the [precommit configuration file](.pre-commit-config.yaml).

## Commit format

Commits should be done by small increments and commit messages must follow the 
[conventional commits format](https://www.conventionalcommits.org/en/v1.0.0/).
- fix: A change that fix an issue
- feat: A change that add or change to the current app behaviour
- build: A change in the project dependencies
- ci: A change in the pipeline configuration
- docs: A change in doc/comments
- style:A change in the coding style that is purely esthetical
- refactor:A change in code organisation that does not impact the application behaviour
- perf: A change that enhance the appllication performance without changing its behaviour
- test: A change to the application test
- chore: A change to any other DX file (precommit hook, IDE config, etc)

Any minor changes (typos, translations, delete comment, etc) can be integrated into other commits.

> [!NOTE]
> You can use commit scope (feat(scope_name):) if the scope will instantly make sense for everyone
> else not working on your task. Don't reference a specific page name or class name or anything 
> implementation specific as a scope; reference the impacted business process instead.