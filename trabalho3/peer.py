import os, sys
import random, time
from threading import Thread, Event
import Pyro5.api

class Peer:
    def __init__(self, nome, pasta):
        # Atributos de peer
        self.nome = nome
        self.uri = None
        self.pasta = pasta
        self.files = self.list_local_files()
        self.is_tracker = False
        self.tracker_uri = None
        self.ultimo_heartbeat = time.time()

        # Atributos eleicao
        self.eleicao = False
        self.epoca = 0
        self.votou_epoca = []

        # Atributos de tracker
        self.registros = {}
        self.ativo = False
        self.temporizador = random.uniform(30, 240)

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
                        if proxy.get_is_tracker() and proxy.get_ativo():
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
            self.epoca = epoca
            print(f"{self.nome} votou em {nome_candidato} na epoca {epoca}")
            return True
        return False
    
    @Pyro5.api.expose
    def heartbeat(self):
        self.ultimo_heartbeat = time.time()
        return "vivo"

    # Funções Tracker
    def enviar_heartbeats(self):
        inicio = time.time()
        print(f"tempo de vida: {self.temporizador}")
        while self.is_tracker and (time.time() - inicio < self.temporizador):
            time.sleep(0.1)
            ns = Pyro5.api.locate_ns()
            for nome, uri in ns.list().items():
                if nome.startswith("peer") and nome != self.nome:
                    try:
                        with Pyro5.api.Proxy(uri) as proxy:
                            proxy.heartbeat()
                    except Exception as e:
                        print(f"Falha no heartbeat: {e}")

def iniciar_eleicao(peer: Peer, ns):
    print(f"{peer.nome} iniciando eleição")
    votos = 1 
    total_peers = 1

    for nome, uri in ns.list().items():
        if nome.startswith("peer") and nome != peer.nome:
            total_peers += 1
            try:
                with Pyro5.api.Proxy(uri) as proxy:
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
        return True
    else:
        print(f"{peer.nome} perdeu a eleição")
        return False
    

def monitorar_tracker(peer: Peer):
    if peer.is_tracker:
        return 

    while True:
        ns = Pyro5.api.locate_ns()
        tempo_desde_ultimo_hb = time.time() - peer.ultimo_heartbeat

        if tempo_desde_ultimo_hb < 0.2:
            peer.temporizador = random.uniform(30, 240)
            continue

        print(f"Tracker inativo. {peer.nome} iniciando eleição...")

        time.sleep(random.uniform(0.15, 0.3))

        peer.epoca += 1
        eleito = iniciar_eleicao(peer, ns)
        if eleito:
            print(f"{peer.nome} Eleito como novo tracker")
            Thread(target=peer.enviar_heartbeats, daemon=True).start()

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
    tracker_nome, tracker_uri = peer.buscar_tracker(ns)

    monitor_tracker = Thread(target=monitorar_tracker, args=(peer,), daemon=True)
    monitor_tracker.start()

    if tracker_uri:
        peer.registrar_no_tracker(tracker_uri)

        with Pyro5.api.Proxy(tracker_uri) as proxy:
            registros = proxy.get_registros()
            print("Registros atuais do tracker:", registros)

    daemon.requestLoop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python peer.py <nome_peer>")
        sys.exit()
    main(sys.argv[1])