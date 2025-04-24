# ========================================================================
# UTFPR - Sistemas Distribuidos
# ========================================================================
# MS Reserva (publisher/subscriber)
# ========================================================================

import pika 
import json
import threading
import os, sys
from time import time
from crypto_utils import carregar_chave_publica, verifica_assinatura
from reserva_utils import carregar_itinerarios, listar_itinerarios, consultar_itinerarios

# ------------------------------------------------
# Publica reserva na fila 'reserva-criada'
# ------------------------------------------------
def publicar_reserva(itinerario, data_embarque, passageiros, cabines):
      id_reserva = f"reserva{itinerario}_{int(time())}"
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
      
      # Declara fila 'reserva-criada'
      channel.queue_declare(queue='reserva-criada', durable=True)
      channel.queue_bind(exchange=exchange_name,
                         queue=routing_key,
                         routing_key=routing_key)
      
      # Publica a reserva para o exchange
      channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(nova_reserva),
            properties=pika.BasicProperties(delivery_mode=2)
      )

      connection.close()

      print("\n Reserva criada com sucesso.")
      return id_reserva

# ------------------------------------------------
# Escuta as filas
# ------------------------------------------------
def escutar_filas():
      def callback(ch, method, properties, body):
            try:
                  mensagem = json.loads(body)
                  tipo = method.routing_key
                  id_reserva = mensagem.get("id_reserva")
                  
                  if tipo in ['pagamento-aprovado', 'pagamento-recusado']:
                        assinatura = mensagem.get("assinatura")
                        mensagem_original = json.dumps({
                              "id_reserva": mensagem["id_reserva"],
                              "status": mensagem["status"]
                        })

                        if not verifica_assinatura(chave_publica, mensagem_original, assinatura):
                              print("Assinatura Inválida. Reserva Cancelada.")
                              return 
                  
                  if tipo == 'pagamento-aprovado':
                        print("aprovado")
                  elif tipo == 'pagamento-recusado':
                        print("recusado")
                  elif tipo == 'bilhete-gerado':
                        print("bilhete")

            except Exception as e:
                  print(f"Erro no callback: {e}")

      chave_publica = carregar_chave_publica()

      connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
      channel = connection.channel()

      filas = ['pagamento-aprovado', 'pagamento-recusado', 'bilhete-gerado']
      for fila in filas:
            channel.queue_declare(queue=fila, durable=True)
            channel.basic_consume(queue=fila,
                                  on_message_callback=callback,
                                  auto_ack=True)

      print("Escutando atualizações da reserva...")
      channel.start_consuming()
            
# ------------------------------------------------
# Menu principal
# ------------------------------------------------
def main():
      itinerarios = carregar_itinerarios()

      threading.Thread(target=escutar_filas, daemon=True).start()

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