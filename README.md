# django-postgres-isolation-levels [![CircleCI](https://circleci.com/gh/michalc/django-postgres-isolation-levels.svg?style=svg)](https://circleci.com/gh/michalc/django-postgres-isolation-levels)

A set of tests exploring PostgreSQL transactions and Django

Database access in usually from separate threads so it's not in the transaction that pytest-django starts.
