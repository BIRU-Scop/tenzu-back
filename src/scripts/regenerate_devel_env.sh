#!/bin/bash



export DJANGO_SETTINGS_MODULE=base.django.settings

show_answer="false"
load_demo="true"
load_test="true"

while getopts 'ydt' opt; do
    case $opt in
        y)
            show_answer="false"
        ;;
        d)
            load_demo="true"
            load_test="false"
            shift
        ;;
        t)
            load_demo="false"
            load_test="true"
            shift
        ;;
    esac
done

if $show_answer == "true" ; then
    echo "WARNING!! This script will REMOVE your Tenzu's database and you'll LOSE all the data."
    read -p "Are you sure you want to proceed? (Press Y to continue): " -n 1 -r
    echo    # (optional) move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
        exit 1
    fi
    echo
fi

read -p 'Specify a Postgres user [default: postgres]: ' dbuser
read -p 'Specify database name [default: tenzu]: ' dbname
read -p 'Specify host [default: localhost]: ' dbhost
read -p 'Specify port [default: 5432]: ' dbport
dbuser=${dbuser:-postgres}
dbname=${dbname:-tenzu}
dbhost=${dbhost:-localhost}
dbport=${dbport:-5432}

echo "-> Remove '${dbname}' DB"
dropdb -U $dbuser -h $dbhost -p $dbport $dbname
echo "-> Create '${dbname}' DB"
createdb -U $dbuser -h $dbhost -p $dbport $dbname

if [ "$?" -ne "0" ]; then
  echo && echo "Error accessing the database, aborting."
else
  echo "-> Load migrations"
  python -m tenzu db migrate --syncdb
  echo "-> Initialize taskqueue"
  python -m tenzu tasksqueue init
  echo "-> Load initial user (admin/123123)"
  python -m tenzu db load-fixtures initial_user
  echo "-> Load initial project_templates (kanban)"
  python -m tenzu db load-fixtures initial_project_templates

  if [[ "$load_test" == "true" && "$load_demo" == "true" ]] ; then
    echo "-> Generate test and demo data"
    python -m tenzu sampledata
  fi

  if [[ "$load_test" == "true"  && "$load_demo" == "false" ]] ; then
    echo "-> Generate test data"
    python -m tenzu sampledata --no-demo
  fi

  if [[ "$load_test" == "false" && "$load_demo" == "true" ]] ; then
    echo "-> Generate demo data"
    python -m tenzu sampledata --no-test
  fi

  echo "-> Compile translations"
  python -m tenzu i18n compile-catalog
fi
