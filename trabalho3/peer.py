import os, sys
import random, time
from threading import Thread
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
        self.temporizador = random.uniform(0.15, 0.3)
        self.tempo_de_vida = random.randint(30, 150)

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
    def heartbeat(self):
        self.ultimo_heartbeat = time.time()
        return "vivo"

    def enviar_heartbeats(self):
        inicio = time.time()
        print(f"tempo de vida: {self.tempo_de_vida}")
        print(time.time() - inicio)
        while self.is_tracker and (time.time() - inicio < self.tempo_de_vida):
            print("passei aqui")
            time.sleep(0.1)
            ns = Pyro5.api.locate_ns()
            for nome, uri in ns.list().items():
                if nome.startswith("peer") and nome != self.nome:
                    try:
                        with Pyro5.api.Proxy(uri) as proxy:
                            proxy.heartbeat()
                    except Exception as e:
                        print(f"Falha no heartbeat: {e}")

    # Funções de transferencia
    def consultar_arquivo(self, arquivo):
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
                return f.read()
        return None
    
    def baixar_arquivo(self, arquivo, peer_uri):
        try:
            with Pyro5.api.Proxy(peer_uri) as proxy:
                dados = proxy.enviar_arquivo(arquivo)
                if dados:
                    with open(os.path.join(self.pasta, arquivo), "wb") as f:
                        f.write(dados)
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
        peer.anuncia_resultado(ns)
        peer.eleicao = False
        return True
    else:
        print(f"{peer.nome} perdeu a eleição")
        peer.eleicao = False
        return False
    

def monitorar_tracker(peer: Peer):
    while True:
        if peer.is_tracker:
            break

        ns = Pyro5.api.locate_ns()
        tempo_desde_ultimo_hb = time.time() - peer.ultimo_heartbeat

        if tempo_desde_ultimo_hb < peer.temporizador:
            peer.temporizador = random.uniform(0.15, 0.3)
            time.sleep(0.05)
            continue

        print(f"Tracker inativo. {peer.nome} iniciando eleição...")

        peer.epoca += 1
        eleito = iniciar_eleicao(peer, ns)
        if eleito:
            print(f"{peer.nome} Eleito como novo tracker")
            peer.temporizador = random.uniform(0.15, 0.3)
            Thread(target=peer.enviar_heartbeats, daemon=True).start()

def monitorar_lista_arquivos(peer: Peer):
    arquivos_atuais = set(peer.list_local_files())
    while True:
        time.sleep(2)
        novos_arquivos = set(peer.list_local_files())
        if novos_arquivos != arquivos_atuais:
            peer.files = list(novos_arquivos)
            arquivos_atuais = novos_arquivos
            if peer.tracker_uri:
                # com a referência do tracker os nós devem
                # cadastrar no tracker o arquivos
                peer.registrar_no_tracker(peer.tracker_uri)

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
    # informando referencia
    ns.register(nome, uri)

    # busca referencia do tracker atual
    monitor_tracker = Thread(target=monitorar_tracker, args=(peer,), daemon=True)
    monitor_tracker.start()

    Thread(target=monitorar_lista_arquivos, args=(peer,), daemon=True).start()

    daemon.requestLoop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python peer.py <nome_peer>")
        sys.exit()
    main(sys.argv[1])