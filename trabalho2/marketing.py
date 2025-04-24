# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Marketing (publisher)
# ========================================================================
import pika 
import os, sys
import json

def publica_promocao(destino, promocao):
      exchange_name = "promocoes_exchange"
      routing_key = f"promocoes-{destino}"

      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      channel.exchange_declare(exchange=exchange_name,
                               exchange_type='direct',
                               durable=True)

      channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(promocao),
            properties=pika.BasicProperties(delivery_mode=2)
      )

      connection.close()
      print(f"Promoção para {destino} publicada!")

def main():
      while True:
            destino = input("Destino da promoção: ")

            titulo = input("Título da promoção: ")
            descricao = input("Descrição: ")
            
            promocao = {
                  "titulo": titulo,
                  "descricao": descricao,
                  "destino": destino
            }

            publica_promocao(destino, promocao)

if __name__ == '__main__':
      try:
            main()
      except KeyboardInterrupt:
            print("Interrupted")
            try:
                  sys.exit(0)
            except SystemExit:
                  os._exit(0)