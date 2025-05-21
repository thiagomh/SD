from peer import Peer
import Pyro5.api

def menu(peer: Peer):
    while True:
        arquivo = input("\nDigite o nome do arquivo para baixar (ou 'sair'): ").strip()
        if arquivo.lower() == "sair":
            print("Encerrando menu de download.")
            break

        donos = peer.consultar_arquivo(arquivo)
        if not donos:
            print(f"Arquivo {arquivo} não encontrado")
            continue

        print(f"{arquivo} está disponivel nos seguintes peers: {donos}")

        peer_escolhido = None
        while peer_escolhido not in donos:
            peer_escolhido = input(f"Escolha o peer de onde baixar ({', '.join(donos)}): ").strip()
            if peer_escolhido not in donos:
                print("Peer inválido. Tente novamente")

        if peer_escolhido == peer.nome:
            print("Você já possui esse arquivo")
            continue

        try:
            ns = Pyro5.api.locate_ns()
            uri_peer = ns.lookup(peer_escolhido)
            peer.baixar_arquivo(arquivo, uri_peer)
        except Exception as e:
            print(f"Erro ao baixar arquivo de {peer_escolhido}: {e}")