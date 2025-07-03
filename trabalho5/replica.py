import grpc
from concurrent import futures
import replicacao_pb2, replicacao_pb2_grpc
import argparse

class Replica(replicacao_pb2_grpc.ServidorServiceServicer):
    def __init__(self, porta) -> None:
        self.epoca = 1
        self.offset = 0
        self.log = []
        self.arquivo_banco = f"banco_replica_{porta}.txt"
        self.arquivo_log = f"log_replica_{porta}.txt"
        self.path = f"trabalho5/dados/{self.arquivo_banco}"
        self.banco = {}

        self.carrega_banco()


    def ReplicarEntrada(self, request, context):
        print()
        print(f"[Replica] Entrada recebida epoca={request.epoca} - offset={request.offset} - conteudo='{request.conteudo}'")

        if request.epoca < self.epoca or (request.epoca == self.epoca and request.offset != self.offset + 1):
            print(f"[Replica] Inconsistencia detectada. Esperava offset {self.offset + 1} e recebeu {request.offset}")
            self.truncar_log(request.offset)
            return replicacao_pb2.Ack(
                sucesso=False,
                mensagem="Inconsistencia no log. Estado da replica desatualizado."
            )

        self.log.append(request)
        self.salvar_em_log(request)
        print(f"[Replica] Entrada armazenada no log intermediario.")
        return replicacao_pb2.Ack(sucesso=True, mensagem="Entrada replicada com sucesso.")
    
    def CommitEntrada(self, request, context):
        print(f"[Replica] Ordem de commit recebida para epoca={request.epoca}, offset={request.offset}")
        if request.epoca != self.epoca:
            return replicacao_pb2.Ack(sucesso=False, mensagem="Epoca invalida para commit.")
        
        for entrada in self.log:
            if entrada.offset == request.offset:
                chave = f"entrada_{entrada.offset}"
                self.banco[chave] = {
                    'epoca': entrada.epoca,
                    'offset': entrada.offset,
                    'conteudo': entrada.conteudo
                }
                self.salvar_em_arquivo(entrada)
                self.offset += 1
                print(f"[Replica] Entrada offset={entrada.offset} committed com sucesso.")
                return replicacao_pb2.Ack(sucesso=True, mensagem="Commit efetuado.")
        
        return replicacao_pb2.Ack(sucesso=False, mensagem="Offset não encontrado no log intermediario.")
    
    def truncar_log(self, offset):
        pass

    def salvar_em_arquivo(self, entrada):
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                linha = f"{entrada.epoca},{entrada.offset},{entrada.conteudo}\n"
                f.write(linha)
        except Exception as e:
            print(f"[Replica] Erro ao salvar em arquivo: {e}")

    def salvar_em_log(self, entrada):
        try:
            path = f"trabalho5/logs/{self.arquivo_log}"
            with open(path, "a", encoding="utf-8") as f:
                linha = f"{entrada.epoca},{entrada.offset},{entrada.conteudo}\n"
                f.write(linha)
        except Exception as e:
            print(f"[Replica] Erro ao salvar log intermediário: {e}")

    def carrega_banco(self):
        with open(self.path, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                epoca_str, offset_str, conteudo = linha.split(",", 2)
                epoca = int(epoca_str)
                offset = int(offset_str)
                chave = f"entrada_{offset}"
                self.banco[chave] = {
                    'epoca': epoca,
                    'offset': offset,
                    'conteudo': conteudo
                }
                if offset > self.offset:
                    self.offset = offset

                if epoca > self.epoca:
                    self.epoca = epoca


def main():
    parser = argparse.ArgumentParser(description="replica server")
    parser.add_argument("--porta", type=int, required=True)
    args = parser.parse_args()

    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replicacao_pb2_grpc.add_ServidorServiceServicer_to_server(Replica(args.porta), servidor)
    servidor.add_insecure_port(f"[::]:{args.porta}")
    print(f"Réplica rodando na porta {args.porta}...")
    servidor.start()
    servidor.wait_for_termination()

if __name__ == '__main__':
    main()