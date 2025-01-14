# Dev setup

> [!IMPORTANT]
> These instructions were made for internal use, for example it assumes
> that you own the `biru.ovh` domain name and have access to an OVH endpoint
> for the configuration of the reverse proxy TLS.
> We will soon make the instruction generic to be run by anyone without
> those kind of heavy requirements.

## Host config
Edit your `/etc/hosts` file manually or do the following command:
```bash
echo "127.0.0.1 local-tenzu.biru.ovh" >> /etc/hosts
```

## dependencies
### Docker
You'll need to install [Docker](https://docs.docker.com/desktop/).

### Tasks

All the tasks must be executed within `buildrun/docker/docker-compose/dev-env` directory.

Before using any of the tasks, [install go-task](https://taskfile.dev/installation/)

This tools allows you to run sets of commands contained in the [Taskfile.yml](buildrun/docker/docker-compose/dev-env/Taskfile.yml).

### Brew
We use [brew](https://brew.sh/) to install some of our dependencies, which is available for Mac, 
Linux and WSL. If you don't use brew, please look at the
`install-deps` task and install those by your preferred method.

### Dependencies bundle

You can install the rest of the dependencies by simply running:
```shell
# Installs pre-commit and ruff packages and installs pre-commit hooks.
task install-deps
```

## Local files

Some unversionned files containing some secrets are mandatory, you can create them with:

```shell
cd buildrun/docker
# these files should be updated with the correct credentials after being copied
cp tenzu/secrets_sample.env tenzu/secrets.env
cp caddy/caddy_sample.env caddy/caddy.env
```

> [!TIP]
> Ask your local raccoon for the secret tokens that are expected in those files.


Use [dev.env](buildrun/docker/tenzu/dev.env) to override environment values that 
should be versioned and [secrets.env](buildrun/docker/tenzu/secrets.env) for
those that shouldn't (like API key and such).

All the variables present in environment can be modified.
But in case in modification of sensible variables like HOST parameters, we cannot guarantee that the project will run.

## Run

To run the project for the first time, you can initialize the app with:
```shell
# don't forget to go to task folder
cd buildrun/docker/docker-compose/dev-env
# build the project with db and fixtures ready
task init-app
```

# After setup
## Useful tasks
 
```shell
# don't forget to go to task folder
cd buildrun/docker/docker-compose/dev-env

# launch the project (with all services)
task up

# open a bash in tenzu-back services
task bash

# launch logs on all the services 
task logs
# specify which logs to track
task logs -- tenzu-back

# launch a django-shell on tenzu-back container
task shell

# launch tests
task test
```

## Dependencies management

TODO: add explanation about pip-tools and commands to handle dependencies

