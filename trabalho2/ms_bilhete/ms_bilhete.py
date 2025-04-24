# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Bilhete (publisher/subscriber)
# ========================================================================
import pika 
import os, sys
import json
import uuid
from crypto_utils import carregar_chave_publica, verificar_assinatura

PATH_PUBLIC_KEY = "chaves/public_pagamento.pem"

def gerar_bilhete(id_reserva):
      return {
            "id_bilhete": str(uuid.uuid4()),
            "id_reserva": id_reserva,
            "mensagem": "Seu bilhete foi gerado com sucesso"
      }

def publicar_bilhete(bilhete):
      connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
      channel = connection.channel()

      routing_key = "bilhete-gerado"
      channel.exchange_declare(exchange="bilhete_exchange",
                               exchange_type="direct", 
                               durable=True)
      channel.queue_declare(queue=routing_key, durable=True)
      channel.queue_bind(exchange="bilhete_exchange",
                         queue=routing_key,
                         routing_key=routing_key)
      
      channel.basic_publish(
            exchange="bilhete_exchange",
            routing_key=routing_key,
            body=json.dumps(bilhete),
            properties=pika.BasicProperties(delivery_mode=2)
      )
      connection.close()
      print(f"Bilhete publicado: {bilhete['id_bilhete']}")

# processar pagamento
def callback(ch, method, properties, body):
      dados = json.loads(body)
      assinatura = dados.get("assinatura")
      id_reserva = dados.get("id_reserva")

      mensagem_original = json.dumps({
            "id_reserva": id_reserva,
            "status": dados.get("status")
      })

      chave_publica = carregar_chave_publica(PATH_PUBLIC_KEY)
      if verificar_assinatura(chave_publica, mensagem_original, assinatura):
            print(f"Assinatura válida para reserva {id_reserva}")
            bilhete = gerar_bilhete(id_reserva)
            publicar_bilhete(bilhete)
      else:
            print(f"Assinatura inválida para {id_reserva}. Bilhete não gerado")

def main():
      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      channel.queue_declare(queue='pagamento-aprovado', durable=True)
      channel.basic_consume(queue='pagamento-aprovado', on_message_callback=callback, auto_ack=True)

      print("MS Bilhete aguardando confirmações de pagamento...")

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
