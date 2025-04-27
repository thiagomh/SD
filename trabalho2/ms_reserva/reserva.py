# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Reserva (publisher/subscriber)
# ========================================================================
import pika 
import json
import threading
import os, sys
import time
from crypto_utils import carregar_chave_publica, verifica_assinatura
from reserva_utils import carregar_itinerarios, listar_itinerarios, consultar_itinerarios


def publicar_reserva(itinerario, data_embarque, passageiros, cabines):
      id_reserva = f"reserva{itinerario}_{int(time.time())}"
      nova_reserva = {
            "id_reserva": id_reserva,
            "id_itinerario": itinerario,
            "data_embarque": data_embarque,
            "passageiros": passageiros,
            "cabines": cabines
      }

      connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
      )
      channel = connection.channel()

      exchange_name = "sistema_exchange"
      routing_key = "reserva-criada"

      channel.exchange_declare(exchange=exchange_name,
                               exchange_type='direct',
                               durable=True)
      
      channel.queue_declare(queue='reserva-criada', durable=True)
      channel.queue_bind(exchange=exchange_name,
                         queue=routing_key,
                         routing_key=routing_key)
      
      channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(nova_reserva),
            properties=pika.BasicProperties(delivery_mode=2)
      )

      connection.close()

      print("\n Reserva criada com sucesso. Aguarde atualizações.")
      return id_reserva


def callback_aprovado(ch, method, properties, body):
      try:
            mensagem = json.loads(body)
            print(mensagem)

            print("Pagamento Aprovado. Gerando bilhete...")
            
      except Exception as e:
            print(f"Erro no callback-pagamento-aprovado. {e}")

def callback_recusado(ch, method, properties, body):
      try:
            mensagem = json.loads(body)
            print(mensagem)

            print("Pagamento Recusado. Reserva Cancelada.")
            
      except Exception as e:
            print(f"Erro no callback-pagamento-recusado. {e}")


def callback_bilhete(ch, method, properties, body):
      try:
            mensagem = json.loads(body)
            print(mensagem)

            print("Bilhete Gerado.")
            
      except Exception as e:
            print(f"Erro no callback-bilhete. {e}")


def escutar_fila(routing_key, callback):
      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      exchange_name = 'sistema_exchange'
      result = channel.queue_declare(queue='', durable=True)
      queue_name = result.method.queue

      channel.queue_bind(exchange=exchange_name,
                         queue=queue_name,
                         routing_key=routing_key)
      
      channel.basic_consume(queue=routing_key,
                            on_message_callback=callback,
                            auto_ack=True)
      
      channel.start_consuming()


def main():
      itinerarios = carregar_itinerarios()

      threading.Thread(target=escutar_fila, args=('pagamento-aprovado', callback_aprovado), daemon=True).start()
      threading.Thread(target=escutar_fila, args=('pagamento-recusado', callback_recusado), daemon=True).start()
      threading.Thread(target=escutar_fila, args=('bilhete-gerado', callback_bilhete), daemon=True).start()

      while True:
            print("\n=== Sistema de Reservas ===")
            print("1 - Listar todos itinerários")
            print("2 - Consultar itinerários")
            print("3 - Reservar cruzeiro")
            print("4 - Sair")
            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                  listar_itinerarios(itinerarios)
            elif opcao == "2":
                  consultar_itinerarios(itinerarios)
            elif opcao == "3":
                  try:  
                        id_itinerario = int(input("ID itinerário: "))
                        data_embarque = input("Data de Embarque: ")
                        passageiros = int(input("Número de passageiros: "))
                        cabines = int(input("Número de cabines: "))
                        id_reserva = publicar_reserva(id_itinerario, data_embarque, passageiros, cabines)


                  except ValueError:
                        print("Valor inválido.")

                  time.sleep(10)
            elif opcao == "4":
                  print("Saindo...")
                  break
            else:
                  print("Opção inválida.")

if __name__ == '__main__':
      try:
            main()
      except KeyboardInterrupt:
            print("Interrupted")
            try:
                  sys.exit(0)
            except SystemExit:
                  os._exit(0)