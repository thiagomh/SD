import os
from threading import Thread, Event
import Pyro5.api
import sys
import time, traceback
import random

@Pyro5.api.expose
class Peer:
    def __init__(self, nome, pasta):
        self.nome = nome
        self.pasta = pasta
        self.files = self.list_local_files()
        self.uri = None
        
        self.is_traker = False
        self.traker_uri = None

        self.registros = {}


    def list_local_files(self):
        return os.listdir(self.pasta)
    
    def get_is_tracker(self):
        return self.is_traker

    def buscar_traker(self, ns):
        if not self.is_traker:
            registros = ns.list()
            
            for nome, uri in registros.items():
                if nome == "Pyro.NameServer" or nome == self.nome:
                    continue
                try:
                    with Pyro5.api.Proxy(uri) as proxy:
                        is_tracker = proxy.get_is_tracker()
                        if is_tracker:
                            print(f"{nome} é o tracker")
                            return nome, uri
                except Exception as e:
                    print(f"Erro ao acessar {e}")

        print("nao encontrado")
        return None, None
        
    def registrar_no_tracker(self, tracker_uri):
        try:
            with Pyro5.api.Proxy(tracker_uri) as proxy:
                resultado = proxy.registrar_arquivos(self.nome, self.files)
                print(resultado)
        except Exception as e:
            print(f"Erro ao registrar arquivos no tracker: {e}")

    def registrar_arquivos(self, nome_peer, lista_arquivos):
        for arquivo in lista_arquivos:
            if arquivo not in self.registros:
                self.registros[arquivo] = []
            if nome_peer not in self.registros[arquivo]:
                self.registros[arquivo].append(nome_peer)
        return f"{nome_peer} cadastrou arquivos no tracker."
    
    def obter_registros(self):
        return self.registros


def main(nome):
    pasta = os.path.join("trabalho3/arquivos/", nome)
    os.makedirs(pasta, exist_ok=True)

    peer = Peer(nome, pasta)

    daemon = Pyro5.api.Daemon()
    uri = daemon.register(peer)
    print(f"{nome} URI registrada: {uri}")

    # Ao iniciar, os nós devem interagir com o serviço de nomes 
    ns = Pyro5.api.locate_ns()

    # i. informar sua referencia
    ns.register(nome, uri)
    # ii. buscar a referência (URI) do tracker atual
    tracker_nome, tracker_uri = peer.buscar_traker(ns)

    # (0,2) Com a referência do tracker, os nós devem cadastrar no tracker o 
    # nome dos arquivos que possuem. 
    print("oi")
    if tracker_nome is None:
        peer.is_traker = True
        ns.register("tracker", uri)
        print(f"{nome} virou o tracker")

    if tracker_uri:
        peer.registrar_no_tracker(tracker_uri)

        with Pyro5.api.Proxy(tracker_uri) as proxy:
            registros = proxy.obter_registros()
            print("Registros atuais do tracker:", registros)

    daemon.requestLoop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python peer.py <nome_peer>")
        sys.exit()
    main(sys.argv[1])