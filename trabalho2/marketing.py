# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Marketing (publisher)
# ========================================================================
import pika 
import os, sys
import time
import random

def publica_promocao(destino):
      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      channel.exchange_declare(queue='promo_exchange',
                               exchange_type="direct",
                               durable=True)

      channel.basic_publish(exchange='',
                            routing_key='',
                            body='')
      
      print("Sent")

      connection.close()

def main():
      pass

if __name__ == '__main__':
      try:
            main()
      except KeyboardInterrupt:
            print("Interrupted")
            try:
                  sys.exit(0)
            except SystemExit:
                  os._exit(0)