#!/bin/sh
docker compose --env-file ./dockerComposeEnv -f ./docker-compose.yaml stop
docker compose --env-file ./dockerComposeEnv -f ./docker-compose.yaml rm