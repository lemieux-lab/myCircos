#!/bin/bash

# Build the docker image:
#
# sudo docker build -t iric/mycircos:v1 .

# Launch docker with run_app.sh as execution script
#
udocker run -p 8090:8090 --rm -d iric/mycircos:v1 /u/mycircos/mycircos/run_app.sh
