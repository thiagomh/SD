# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Pagamento (publisher/subscriber)
# ========================================================================
import pika 
import json
import time
import sys, os
from random import choice
from crypto_utils import assinar_mensagem

def callback(ch, method, properties, body):
      reserva = json.loads(body)
      print(reserva)
      id_reserva = reserva["id_reserva"]

      print(f"\n Pagamento recebido para {id_reserva}")

      aprovado = choice([True, False])

      mensagem = {
            "id_reserva": id_reserva,
            "status": "aprovado" if aprovado else "recusado"
      }
      assinatura = assinar_mensagem(json.dumps(mensagem))
      mensagem["assinatura"] = assinatura

      connection = pika.BlockingConnection(pika.ConnectionParameters("localhost")) 
      channel = connection.channel()

      exchange = "sistema_exchange"
      routing_key = "pagamento-aprovado" if aprovado else "pagamento-recusado"

      channel.exchange_declare(exchange=exchange,
                               exchange_type="direct",
                               durable=True) 
      channel.queue_declare(queue=routing_key, durable=True)
      channel.queue_bind(exchange=exchange,
                         queue=routing_key,
                         routing_key=routing_key) 

      channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(delivery_mode=2)
      )   

      connection.close()

      print(f"Mensagem '{routing_key}' publicada com assinatura")

def main():
      print("MS Pagamento aguardando reservas...")

      connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
      channel = connection.channel()

      exchange_name = 'sistema_exchange'
      routing_key = 'reserva-criada'

      result = channel.queue_declare(queue='', durable=True)
      queue_name = result.method.queue

      channel.queue_bind(exchange=exchange_name,
                         queue=queue_name,
                         routing_key=routing_key)
      
      channel.basic_consume(queue=routing_key, 
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