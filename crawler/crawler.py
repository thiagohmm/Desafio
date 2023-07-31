import pika
import redis
import json
import requests
import os
from dotenv import load_dotenv

# RabbitMQ configuration
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'cpf_queue'

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_AUTH = 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81'

load_dotenv()

def record_redis(lista):
  
   # Grava a lista no Redis.
  for item in lista:
    redis_client.setnx(item['CPF'], item['NB'])

  # Fecha a conexão com o Redis.
  redis_client.close()
  print("gravado no REDIS")


def get_all_data_from_redis():
   
    # Obtém todas as chaves presentes no Redis
    all_keys = redis_client.keys('*')

    # Recupera os valores associados a cada chave
    all_data = {}
    for key in all_keys:
        value = redis_client.get(key)
        all_data[key] = value.decode('utf-8') if value else None

    return all_data

def make_login_request():
    url = os.getenv('API_URL')
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'login': os.getenv('LOGIN'),
        'senha': os.getenv('SENHA'),
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.headers  # Decodifica a resposta JSON
        authorization_token = response_data.get('authorization')
        cleaned_token = authorization_token.replace("Bearer ", "")
        return cleaned_token
    except requests.exceptions.RequestException as error:
        print('Erro na requisição de login:', error)
        return None

def make_get_request(cpf, bearer_token):
    url_base = "http://extratoblubeapp-env.eba-mvegshhd.sa-east-1.elasticbeanstalk.com/offline/listagem/"
    url_consult = url_base + str(cpf).strip()
    
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }

    try:
        response = requests.get(url_consult, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                nb_value = data.get("beneficios")
                return nb_value
            except ValueError:
                print(f"Invalid JSON in response: {response.text}")
                return None
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as error:
        print('Erro na requisição:', error)
        return None


def callback(ch, method, properties, body):
    cpflist = []
    message = body.decode('utf-8')
    print(f"Received message: {message}")
    cpfUniqValues = list(set(json.loads(message)['cpfList']))

    for cpf in cpfUniqValues:
         dicionario = {"CPF": cpf, "NB": 0}
         cpflist.append(dicionario)
    
        
    
    record_redis(cpflist)
    token = make_login_request()
    if token:
        cpfok = []
        print('Authorization Token:', token)
        dataRedis = get_all_data_from_redis()

        for data in dataRedis:
          cpfToConsult = data.decode('utf-8')
          result = make_get_request(cpfToConsult, token)
          if result !=  "Matrícula não encontrada!":
            dicionarioOK = {"CPF": cpf, "NB": result[0]['nb']}
            cpfok.append(dicionarioOK)
        print(cpfok)


def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit, press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    # Create a Redis client
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,  password=REDIS_AUTH)

    # Start the consumer
    start_consumer()