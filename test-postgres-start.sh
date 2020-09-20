#!/bin/bash -xe

docker run --name postgres -e POSTGRES_PASSWORD=password --rm -d -p 5432:5432 postgres:9.5.21

