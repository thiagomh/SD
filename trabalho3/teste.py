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
        self.uri = None
        self.pasta = pasta
        self.files = self.list_local_files()
        self.uri = None

        self.epoca = 0
        self.eleicao = False
        
        self.is_tracker = False
        self.traker_uri = None

        self.registros = {}


    def list_local_files(self):
        return os.listdir(self.pasta)
    
    @Pyro5.api.expose
    def get_is_tracker(self):
        return self.is_tracker

    def buscar_traker(self, ns):
        if self.is_tracker:
            return self.nome, self.uri
        
        registros = ns.list()
        for nome, uri in registros.items():
            if nome != "Pyro.NameServer" and nome != self.nome:
                print(nome, uri)
                try:
                    with Pyro5.api.Proxy(uri) as proxy:
                        print("oii")
                        is_tracker = proxy.get_is_tracker()
                        print(is_tracker)
                        if is_tracker:
                            print(f"{nome} é o tracker")
                            return nome, uri
                except Exception as e:
                    import traceback
                    print(f"Erro ao acessar {e}")
                    traceback.print_exc()
        
        print("Tracker não encontrado")
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
    
    def votar_em_candidato(self, nome_candidato):
        print(f"{self.nome} votando em {nome_candidato}")
        return True

def iniciar_eleicao(peer, ns):
    print(f"{peer.nome} iniciando eleição")
    votos = 1
    total_peers = 1

    registros = ns.list()
    for nome, uri in registros.items():
        if nome.startswith("peer") and nome != peer.nome:
            total_peers += 1
            try:
                with Pyro5.api.Proxy(uri) as proxy:
                    if proxy.votar_em_candidato(peer.nome):
                        votos += 1
            except Exception as e:
                print(f"Erro ao solicitar voto em {nome}: {e}")

    if votos > total_peers // 2:
        print(f"{peer.nome} recebeu {votos}/{total_peers} votos e se tornou o novo tracker")
        return True
    else:
        print(f"{peer.nome} perdeu a eleição")
        return False       
        
def monitorar_tracker(peer: Peer):
    while True:
        ns = Pyro5.api.locate_ns()
        time.sleep(5)

        if peer.is_tracker:
            print("Sou o tracker")
            continue

        nome_tracker, uri_tracker = peer.buscar_traker(ns)

        if uri_tracker is None:
            print(f"Tracker inativo. {peer.nome} iniciando eleição...")
            eleito = iniciar_eleicao(peer, ns)
            if eleito:
                peer.is_tracker = True
                tracker_name = f"Tracker_Epoca_{peer.epoca}"
                ns.register(tracker_name, peer.uri)
                print(f"{peer.nome} Eleito como novo tracker")

def main(nome):
    pasta = os.path.join("trabalho3/arquivos/", nome)
    os.makedirs(pasta, exist_ok=True)

    peer = Peer(nome, pasta)

    daemon = Pyro5.api.Daemon()
    uri = daemon.register(peer)
    peer.uri = uri
    print(f"{nome} URI registrada: {uri}")

    # Ao iniciar, os nós devem interagir com o serviço de nomes 
    ns = Pyro5.api.locate_ns(host="localhost")

    # i. informar sua referencia
    ns.register(nome, uri)
    # ii. buscar a referência (URI) do tracker atual
    tracker_nome, tracker_uri = peer.buscar_traker(ns)

    monitor_tracker = Thread(target=monitorar_tracker, args=(peer,), daemon=True)
    monitor_tracker.start()

    # (0,2) Com a referência do tracker, os nós devem cadastrar no tracker o 
    # nome dos arquivos que possuem.

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