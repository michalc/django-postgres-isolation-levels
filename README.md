# django-postgres-isolation-levels [![CircleCI](https://circleci.com/gh/michalc/django-postgres-isolation-levels.svg?style=svg)](https://circleci.com/gh/michalc/django-postgres-isolation-levels)

A set of tests exploring PostgreSQL transactions and Django

Database access in usually from separate threads so it's not in the transaction that pytest-django starts.


## Running tests

In one session run

```bash
docker run --rm -it -p 5432:5432 postgres:10.1
```

and then another

```bash
pip install -r ./requirements.txt
./test.sh
```
