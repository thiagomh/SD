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


def gerar_bilhete(id_reserva):
      pass


def publicar_bilhete(bilhete):
      pass

# processar pagamento
def callback(ch, method, properties, body):
      pass

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
