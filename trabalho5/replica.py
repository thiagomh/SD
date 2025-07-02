import grpc
from concurrent import futures
import replicacao_pb2, replicacao_pb2_grpc
import argparse

class Replica(replicacao_pb2_grpc.ServidorServiceServicer):
    def __init__(self) -> None:
        self.banco: dict[str, dict] = {}

    def ReplicarEntrada(self, request, context):
        chave = f"entrada_{request.offset}"
        self.banco[chave] = {
            'epoca': request.epoca,
            'offset': request.offset,
            'conteudo': request.conteudo
        }

        print(f"Entrada replicada: {chave} = {request.conteudo}")
        return replicacao_pb2.Ack(sucesso=True, mensagem="Entrada replicada com sucesso.")
    
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