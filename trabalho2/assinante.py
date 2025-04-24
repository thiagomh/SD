# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# Assinante (subscriber)
# ========================================================================
import os, sys, time
import pika
import json

def callback(ch, method, properties, body):
      promocao = json.loads(body)
      print("Promoção recebida: ")
      print(f"{promocao}")


def main():
      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      exchange_name = "promocoes_exchange"
      routing_key = "promocoes"

      channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='direct',
            durable=True
      )

      result = channel.queue_declare(queue='', exclusive=True)
      queue_name = result.method.queue

      destinos = input("Entre com os destinos: ").split(',')

      for destino in destinos:
            routing_key = f"promocoes-{destino}"
            channel.queue_bind(exchange=exchange_name, 
                               queue=queue_name,
                               routing_key=routing_key)

      channel.basic_consume(queue=queue_name,
                            on_message_callback=callback,
                            auto_ack=True)
      
      channel.start_consuming()

if __name__ == '__main__':
      try:
            main()
      except KeyboardInterrupt:
            print("Interrupted")
            try:
                  sys.exit(0)
            except SystemExit:
                  os._exit(0)