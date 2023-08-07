#!/bin/bash

sleep 20

echo -n "Eviando os cpf(s) para o crawler"

curl --request POST \
  --url http://localhost:8080/send-cpfs \
  --header 'Content-Type: application/json' \
  --data '{
	"cpfList": ["033.355.888-00", "124.440.495-00", "067.510.675-34", 
"087.438.945-34",
"248.625.765-91",
"809.599.385-91",
"248.063.905-34",
"056.054.235-68",
"148.236.245-72",
"369.721.777-15"
]
}'

echo -e "\n"
echo -e "\n"
echo -n "Monitorando logs do Crawler"

echo -e "\n"
echo -e "\n"
sleep 5

docker logs --follow crawler

