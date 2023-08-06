import pika
import redis
import json
import requests
from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
import threading
import queue
import time

# RabbitMQ configuration
RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_QUEUE = 'cpf_queue'

# Redis configuration
REDIS_HOST = 'cache'
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
        decoded_value = value.decode('utf-8') if value else None

        # Condição para trazer apenas os registros com valor igual a 0
        if decoded_value == '0':
            all_data[key] = decoded_value

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


def remove_cpf_from_redis(cpf):
  
    # Remove o CPF do Redis
    redis_client.delete(cpf)

def save_json_to_elasticsearch(json_data, index_name, document_id=None):

    es_host = 'elasticsearch'
    es_port = 9200
    es_scheme = 'http'
    
   

    try:
        # Conecta-se ao Elasticsearch
        es = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': es_scheme}])
        # Grava o documento JSON no índice especificado
        response = es.index(index=index_name, body=json_data, id=document_id)
        if response['result'] == 'created':
            print("Documento gravado com sucesso!")
        elif response['result'] == 'updated':
            print("Documento atualizado com sucesso!")
        else:
            print("Falha ao gravar o documento no Elasticsearch.")
    except Exception as e:
        print(f"Erro ao gravar o documento no Elasticsearch: {e}")

def process_data_from_redis(token, data_chunk, result_queue):
    cpfok = []
    for data in data_chunk:
        cpfToConsult = data.decode('utf-8')
        result = make_get_request(cpfToConsult, token)
        save_json_to_elasticsearch(result[0], cpfToConsult)
        nb = result[0]['nb']
        if nb != "Matrícula não encontrada!":
            remove_cpf_from_redis(cpfToConsult)
            dicionarioOK = {"CPF": cpfToConsult, "NB": result[0]['nb']}
            cpfok.append(dicionarioOK)
    result_queue.put(cpfok)


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
        dataRedis = get_all_data_from_redis()
        dataRedis = list(dataRedis)   # Converta para uma lista para torná-lo iterável

         # Calcule o número de threads que você deseja usar (por exemplo, 4 threads)
        num_threads = 4
        chunk_size = len(dataRedis) // num_threads

        # Crie uma fila segura para threads e coloque os pacotes de dados nela
        data_queue = queue.Queue()
        for i in range(num_threads):
            start_index = i * chunk_size
            end_index = start_index + chunk_size if i < num_threads - 1 else len(dataRedis)
            thread_data = dataRedis[start_index:end_index]
            data_queue.put(thread_data)

         # Crie e inicie as threads
        threads = []
        result_queue = queue.Queue()
        for i in range(num_threads):
            thread_data = data_queue.get()
            thread = threading.Thread(target=process_data_from_redis, args=(token, thread_data, result_queue))
            thread.start()
            threads.append(thread)

        # Aguarde todas as threads concluírem
        for thread in threads:
            thread.join()

         # Reúne os resultados da fila de resultados
        cpfok = []
        while not result_queue.empty():
            cpfok.extend(result_queue.get())

         # Se a estrutura não estiver vazia, atualize o Redis
        if cpfok:
            record_redis(cpfok)

        print("Tarefas concluidas com sucesso") 

def start_consumer():
    print("Serviço Iniciado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)

    print('Esperando por mensagens. para, sair pressione CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    print("Iniciando Serviço")
    time.sleep(30)
    #Cria um cliente redis
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,  password=REDIS_AUTH)

    # Starta o consumidor
    start_consumer()