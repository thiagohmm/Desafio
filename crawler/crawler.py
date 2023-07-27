import pika
import redis
import json

# RabbitMQ configuration
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'cpf_queue'

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

def callback(ch, method, properties, body):
    cpflist = []
    message = body.decode('utf-8')
    print(f"Received message: {message}")
    cpfUniqValues = list(set(json.loads(message)['cpfList']))

    #cpfDict = { 'CPF': cpf for cpf in cpfUniqValues }  
    #print("formated", cpfDict, type(cpfUniqValues))
    for cpf in cpfUniqValues:
         dicionario = {"CPF": cpf, "NB": 0}
         cpflist.append(dicionario)
    
        
    print("formated", cpflist)

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit, press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    # Create a Redis client
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    # Start the consumer
    start_consumer()