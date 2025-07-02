import grpc
from concurrent import futures
import replicacao_pb2
import replicacao_pb2_grpc

PORTA = 50051

class Lider(replicacao_pb2_grpc.ClienteServiceServicer):
    def __init__(self, enderecos_replicas) -> None:
        self.banco = {}
        self.epoca = 1
        self.offset = 0
        self.enderecos_replicas = enderecos_replicas
        self.stubs = []
        for endereco in enderecos_replicas:
            canal = grpc.insecure_channel(endereco)
            stub = replicacao_pb2_grpc.ServidorServiceStub(canal)
            self.stubs.append(stub)

    def replicar_para_replica(self, log_entry):
        for stub in self.stubs:
            try:
                ack = stub.ReplicarEntrada(log_entry)
                if ack.sucesso:
                    print(f"Replica aceitou entrada: offset={log_entry.offset}")
                else:
                    print(f"Replica recusou entrada: {ack.mensagem}")
            except Exception as e:
                print(f"Erro ao replicar para uma réplica: {e}")

    def EnviarDado(self, request, context):
        self.offset += 1 
        chave = f"entrada_{self.offset}"
        self.banco[chave] = {
            'epoca': self.epoca,
            'offset': self.offset,
            'conteudo': request.conteudo
        }

        # Replicação
        log_entry = replicacao_pb2.LogEntry(
            epoca=self.epoca,
            offset=self.offset,
            conteudo=request.conteudo
        )

        self.replicar_para_replica(log_entry)

        print(f"Dado recebido epoca={self.epoca}:  registro nº {self.offset} → {request.conteudo}")
        return replicacao_pb2.Resposta(
            mensagem=f"Dado armazenado com sucesso na chave '{chave}'",
            conteudo=request.conteudo
        )
    
    def Consultar(self, request, context):
        entrada = self.banco.get(request.chave)
        if entrada:
            return replicacao_pb2.Resposta(
                mensagem=f"Dado encontrado na época {entrada['epoca']} com offset {entrada['offset']}.",
                conteudo=entrada['conteudo']
            )
        else:
            return replicacao_pb2.Resposta(
                mensagem="Chave não encontrada.",
                conteudo=""
            )
        
def main():
    replicas = ["localhost:50052", "localhost:50053", "localhost:50054"]
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lider = Lider(replicas)
    replicacao_pb2_grpc.add_ClienteServiceServicer_to_server(lider, servidor)
    servidor.add_insecure_port(f"[::]:{PORTA}")
    print(f"Líder rodando na porta {PORTA}...")
    servidor.start()
    servidor.wait_for_termination()

if __name__ == '__main__':
    main()