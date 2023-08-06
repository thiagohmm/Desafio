FROM node:18-alpine 

# couchbase sdk requirements
RUN apk update && rm -rf /var/cache/apk/*

WORKDIR /usr/src/app

COPY package.json package-lock.json ./

# install dependencies
RUN npm install

COPY app.js ./

RUN apk add wget netcat-openbsd \
  && wget -q -O /usr/bin/wait-for https://raw.githubusercontent.com/eficode/wait-for/v2.2.3/wait-for && \
  chmod +x /usr/bin/wait-for