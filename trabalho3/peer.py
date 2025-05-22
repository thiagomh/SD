import os, sys
import random, time
from threading import Thread
import Pyro5.api
import logging
import json

class Peer:
    def __init__(self, nome, pasta):
        # Atributos de peer
        self.nome = nome
        self.uri = None
        self.pasta = pasta
        self.files = self.list_local_files()
        self.is_tracker = False
        self.tracker_uri = None
        self.temporizador = random.uniform(0.15, 0.3)
        self.recebeu_heartbeat = False

        # Atributos eleicao
        self.eleicao = False
        self.epoca = 0
        self.votou_epoca = []

        # Atributos de tracker
        self.registros = {}
        self.ativo = False

    def list_local_files(self):
        return os.listdir(self.pasta)
    
    @Pyro5.api.expose
    def get_is_tracker(self):
        return self.is_tracker
    
    @Pyro5.api.expose
    def get_ativo(self):
        return self.ativo
    
    @Pyro5.api.expose
    def get_registros(self):
        return self.registros
    
    @Pyro5.api.expose
    def set_tracker_uri(self, uri):
        self.tracker_uri = uri

    @Pyro5.api.expose
    def set_recebeu_heartbeat(self, heart):
        self.recebeu_heartbeat = heart

    @Pyro5.api.expose
    def ping(self):
        return True
    
    @Pyro5.api.expose
    def registrar_no_tracker(self, tracker_uri):
        try:
            with Pyro5.api.Proxy(tracker_uri) as proxy:
                resultado = proxy.registrar_arquivos(self.nome, self.files)
                print(resultado)
        except Exception as e:
            print(f"Erro ao registrar arquivos no tracker: {e}")

    @Pyro5.api.expose
    def registrar_arquivos(self, nome_peer, lista_arquivos):
        for arquivo in lista_arquivos:
            if arquivo not in self.registros:
                self.registros[arquivo] = []
            if nome_peer not in self.registros[arquivo]:
                self.registros[arquivo].append(nome_peer)
        return f"{nome_peer} cadastrou arquivos no tracker."
    
    def buscar_tracker(self, ns):
        ns_list = ns.list()
        for nome, uri in ns_list.items():
            if nome.startswith("Tracker_Epoca_"):
                try:
                    with Pyro5.api.Proxy(uri) as proxy:
                        if proxy.get_is_tracker():
                            self.tracker_uri = uri
                            return nome, uri
                except Exception as e:
                    print(f"Erro ao buscar tracker: {e}")
        print("Tracker não encontrado.")
        return None, None
    
    # Funções de eleição
    @Pyro5.api.expose
    def votar_em_candidato(self, nome_candidato, epoca):
        if epoca not in self.votou_epoca:
            self.votou_epoca.append(epoca)
            print(f"{self.nome} votou em {nome_candidato} na epoca {epoca}")
            return True
        return False
    
    def anuncia_resultado(self, ns):
        for nome, uri in ns.list().items():
            if nome.startswith("peer") and nome != self.nome:
                try:
                    with Pyro5.api.Proxy(uri) as proxy:
                        proxy.set_tracker_uri(self.uri)
                        proxy.registrar_no_tracker(self.uri)
                except Exception as e:
                    print(f"Erro no anuncio de resultado {e}")

    # Funções Tracker
    @Pyro5.api.expose
    def recebe_heartbeat(self, epoca, ns):
        self.recebeu_heartbeat = True
        if self.epoca < epoca:
            self.epoca = epoca
            print(f"estou procurando o tracker numero {epoca-1}")
            uri_tracker = ns.lookup(f"Tracker_Epoca_{epoca-1}")
            if uri_tracker:
                print("achei")
            with Pyro5.api.Proxy(uri_tracker) as proxy:
                proxy.set_tracker_uri(uri_tracker)
                proxy.registrar_no_tracker(uri_tracker)
            

    def enviar_heartbeats(self):
        while self.is_tracker:
            time.sleep(0.1)
            ns = Pyro5.api.locate_ns()
            for nome, uri in ns.list().items():
                if nome.startswith("peer") and nome != self.nome:
                    try:
                        with Pyro5.api.Proxy(uri) as proxy:
                            if proxy.ping():
                                proxy.recebe_heartbeat(self.epoca, ns)
                    except (ConnectionError, Pyro5.errors.CommunicationError):
                        continue
        self.is_tracker = False

    # Funções de transferencia
    def consultar_arquivo(self, arquivo):
        if self.is_tracker == True:
            return self.registros.get(arquivo, [])
        
        if self.tracker_uri:
            try:
                with Pyro5.api.Proxy(self.tracker_uri) as proxy:
                    registros = proxy.get_registros()
                    return registros.get(arquivo, [])
            except Exception as e:
                print(f"Erro ao consultar tracker: {e}")
        return []
    
    @Pyro5.api.expose
    def enviar_arquivo(self, arquivo):
        caminho = os.path.join(self.pasta, arquivo)
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                conteudo = f.read()
                return conteudo
    
    def baixar_arquivo(self, arquivo, peer_uri):
        try:
            with Pyro5.api.Proxy(peer_uri) as proxy:
                dados = proxy.enviar_arquivo(arquivo)
                if dados:
                    try:
                        with open(os.path.join(self.pasta, arquivo), "wb") as f:
                            f.write(dados)
                    except Exception as e:
                        print(f"Erro na escrita do arquivo {e}")

                    print(f"{self.nome} baixou '{arquivo}' de {peer_uri}")
                    self.files = self.list_local_files()
                    if self.tracker_uri:
                        self.registrar_no_tracker(self.tracker_uri)
        except Exception as e:
            print(f"Erro ao abrir arquivo: {e}")


def iniciar_eleicao(peer: Peer, ns):
    print(f"{peer.nome} se declarou como candidato na epoca {peer.epoca}")
    peer.eleicao = True
    votos = 1 
    total_peers = 1

    for nome, uri in ns.list().items():
        if nome.startswith("peer") and nome != peer.nome:
            try:
                with Pyro5.api.Proxy(uri) as proxy:
                    proxy._pyroTimeout = 2
                    if proxy.ping():
                        total_peers += 1
                        if proxy.votar_em_candidato(peer.nome, peer.epoca):
                            votos += 1
            except Exception as e:
                print(f"Erro ao solicitar voto em {nome}: {e}")

    if votos > total_peers // 2:
        print(f"{peer.nome} recebeu {votos}/{total_peers} votos e se tornou o tracker")
        peer.is_tracker = True
        tracker_name = f"Tracker_Epoca_{peer.epoca}"
        peer.epoca += 1
        ns.register(tracker_name, peer.uri)
        print(f"Tracker registrado como: {tracker_name}")
        # peer.anuncia_resultado(ns)
        peer.eleicao = False
        return True
    else:
        print(f"{peer.nome} perdeu a eleição")
        peer.eleicao = False
        peer.is_tracker = False
        return False
    

def monitorar_tracker(peer: Peer):
    while True:
        if peer.is_tracker:
            return
    
        ns = Pyro5.api.locate_ns()            
        time.sleep(peer.temporizador)


        print(peer.recebeu_heartbeat)
        if peer.recebeu_heartbeat:
            peer.recebeu_heartbeat = False
            continue

        print(f"Tracker inativo. {peer.nome} iniciando eleição...")

        eleito = iniciar_eleicao(peer, ns)
        if eleito:
            print(f"{peer.nome} Eleito como novo tracker na epoca {peer.epoca - 1}")
            print()
            peer.temporizador = random.uniform(0.15, 0.3)
            Thread(target=peer.enviar_heartbeats, daemon=True).start()


def main(nome):
    pasta = os.path.join("trabalho3/arquivos/", nome)
    os.makedirs(pasta, exist_ok=True)

    Pyro5.api.config.SERPENT_BYTES_REPR = True

    peer = Peer(nome, pasta)

    daemon = Pyro5.api.Daemon()
    uri = daemon.register(peer)
    peer.uri = uri
    print(f"{nome} URI registrada: {uri}")

    # Ao iniciar, os nós devem interagir com o serviço de nomes 
    ns = Pyro5.api.locate_ns(host="localhost")
    # informando referencia
    ns.register(nome, uri)

    # busca referencia do tracker atual
    time.sleep(1)
    monitor_tracker = Thread(target=monitorar_tracker, args=(peer,), daemon=True)
    monitor_tracker.start()

    daemon.requestLoop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python peer.py <nome_peer>")
        sys.exit()
    main(sys.argv[1])