# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Pagamento (publisher/subscriber)
# ========================================================================
import pika 
import json
import random
import time
import sys, os
from crypto_utils import assinar_mensagem

def callback(ch, method, properties, body):
      reserva = json.loads(body)
      id_reserva = reserva["id_reserva"]

      print(f"\n Pagamento recebido para {id_reserva}")
      time.sleep(2)

      aprovado = random.choice([True, False])

      mensagem = {
            "id_reserva": id_reserva,
            "status": "aprovado" if aprovado else "recusado"
      }

      assinatura = assinar_mensagem(json.dumps(mensagem))
      mensagem["assinatura"] = assinatura

      connection = pika.BlockingConnection(pika.ConnectionParameters["localhost"]) 
      channel = connection.channel()

      channel.exchange_declare(exchange="pagamento-exchange",
                               exchange_type="direct",
                               durable=True) 

      routing_key = "pagamento-aprovado" if aprovado else "pagamento-recusado"
      channel.queue_declare(queue=routing_key, durable=True)
      channel.queue_bind(exchange="pagamento-exchange",
                         queue=routing_key,
                         routing_key=routing_key) 

      channel.basic_publish(
            exchange="pagamento-exchange",
            routing_key=routing_key,
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(delivery_mode=2)
      )   

      connection.close()

      print(f"Mensagem '{routing_key}' publicada com assinatura")

def main():
      print("MS Pagamento aguardando reservas...")

      connection = pika.BlockingConnection(pika.ConnectionParameters("lcoalhost"))
      channel = connection.channel()

      # Escuta fila de reservas criadas
      channel.queue_declare(queue='reserva-criada', durable=True)
      channel.basic_consume(queue='reserva-criada', 
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