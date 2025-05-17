import os
from threading import Thread, Event
import Pyro5.api
import sys
import time
import random

class Peer:
    def __init__(self, nome, pasta):
        self.nome = nome
        self.pasta = pasta
        self.files = self.list_local_files()
        self.uri = None
        
        self.is_traker = False
        self.traker_uri = None

    def list_local_files(self):
        return os.listdir(self.pasta)
    
    @Pyro5.api.expose
    def get_is_tracker(self):
        return self.is_traker

    def buscar_traker(self, ns):
        if not self.is_traker:
            registros = ns.list()
            
            for nome, uri in registros.items():
                try:
                    with Pyro5.api.Proxy(uri) as proxy:
                        is_tracker = proxy.get_is_tracker()
                        if is_tracker:
                            print(f"{nome} é o tracker")
                            return nome, uri
                except Exception as e:
                    print(f"Erro ao acessar {e}")
        else:
            print(f"{self.nome} é o tracker")
            return self.nome, self.uri


def main(nome):
    pasta = os.path.join("trabalho3/arquivos", nome)
    os.makedirs(pasta, exist_ok=True)

    peer = Peer(nome, pasta)

    daemon = Pyro5.api.Daemon()
    uri = daemon.register(peer)

    # Ao iniciar, os nós devem interagir com o serviço de nomes 
    ns = Pyro5.api.locate_ns()

    # i. informar sua referencia
    ns.register(nome, uri)
    # ii. buscar a referência (URI) do tracker atual
    peer.buscar_traker(ns)

    print(f"{nome} URI registrada: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python peer.py <nome_peer>")
        sys.exit()
    main(sys.argv[1])