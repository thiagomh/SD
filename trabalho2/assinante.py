# ========================================================================
# Autor: Thiago Henrique 
# UTFPR - Sistemas Distribuidos
# ========================================================================
# Assinante (subscriber)
# ========================================================================
import os, sys, time
import pika

def menu():
      print("=============================")
      print("Escolha uma opcao")
      print("1 - Verificar destino")
      print("2 - Receber promocoes")
      print("=============================")

def main():
      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      channel.queue_declare(queue='', durable=True)

      def callback(ch, method, properties, body):
            print(f"Received ({body.decode()})")
            time.sleep(body.count(b'.'))
            print(" [x] Done")
            ch.basic_ack(delivery_tag = method.delivery_tag)

      channel.basic_qos(prefetch_count=1)
      channel.basic_consume(queue='', on_message_callback=callback)

      print("")
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