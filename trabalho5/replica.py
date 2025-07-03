import grpc
from concurrent import futures
import replicacao_pb2, replicacao_pb2_grpc
import argparse

class Replica(replicacao_pb2_grpc.ServidorServiceServicer):
    def __init__(self) -> None:
        self.epoca = 1
        self.offset = 0 
        self.log = []
        self.banco: dict[str, dict] = {}

    def ReplicarEntrada(self, request, context):
        print(f"[Replica] Recebida entrada epoca={request.epoca}, offset={request.offset}, conteudo='{request.conteudo}'")

        if request.epoca < self.epoca or (request.epoca == self and request.offset != len(self.log) + 1):
            print(f"[Replica] Inconsistência detectada. Esperava offset {len(self.log)+1}, recebeu {request.offset}")
            self.truncar_log(request.offset)
            return replicacao_pb2.Ack(
                sucesso=False,
                mensagem="Inconsistência no log. Estado da réplica desatualizado."
            )

        self.log.append(request)
        print(f"[Replica] Entrada armazenada no log intermediário.")
        return replicacao_pb2.Ack(sucesso=True, mensagem="Entrada replicada com sucesso.")
    
    def CommitEntrada(self, request, context):
        print(f"[Replica] Ordem de commit recebida para epoca={request.epoca}, offset={request.offset}")
        if request.epoca != self.epoca:
            return replicacao_pb2.Ack(sucesso=False, mensagem="Época inválida para commit.")
        
        for entrada in self.log:
            if entrada.offset == request.offset:
                self.banco[entrada.offset] = entrada.conteudo
                print(f"[Replica] Entrada offset={entrada.offset} committed com sucesso.")
                return replicacao_pb2.Ack(sucesso=True, mensagem="Commit efetuado.")
        
        return replicacao_pb2.Ack(sucesso=False, mensagem="Offset não encontrado no log intermediário.")
    
    def truncar_log(self, offset):
        self.log = [entrada for entrada in self.log if entrada.offset < offset]
        print(f"[Replica] Log truncado a partir do offset {offset}")

def main():
    parser = argparse.ArgumentParser(description="replica server")
    parser.add_argument("--porta", type=int, required=True)
    args = parser.parse_args()

    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replicacao_pb2_grpc.add_ServidorServiceServicer_to_server(Replica(), servidor)
    servidor.add_insecure_port(f"[::]:{args.porta}")
    print(f"Réplica rodando na porta {args.porta}...")
    servidor.start()
    servidor.wait_for_termination()

if __name__ == '__main__':
    main()