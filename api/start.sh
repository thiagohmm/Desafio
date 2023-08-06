#!/bin/bash


# Wait for Service 1
 /usr/bin/wait-for elasticsearch:9200 -t 15

# Wait for Service 2
 /usr/bin/wait-for rabbitmq:5672 -t 15


cd /usr/src/app/ && node app.js