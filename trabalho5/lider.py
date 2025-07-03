import grpc
from concurrent import futures
import replicacao_pb2
import replicacao_pb2_grpc

PORTA = 50051

class Lider(replicacao_pb2_grpc.ClienteServiceServicer):
    def __init__(self, enderecos_replicas) -> None:
        self.banco = {}
        self.log = []
        self.epoca = 1
        self.offset = 0
        self.enderecos_replicas = enderecos_replicas
        self.stubs: list[replicacao_pb2_grpc.ServidorServiceStub] = []
        self.arquivo_log = "log_lider.txt"
        self.arquivo_banco = "banco_lider.txt"

        with open(f"trabalho5/logs/{self.arquivo_log}", "w", encoding="utf-8") as f:
            f.write("")
            
        self.carrega_banco()

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
                print(f"Erro ao replicar para uma replica: {e}")

    def EnviarDado(self, request, context):
        self.offset += 1 
        entrada = replicacao_pb2.LogEntry(
            epoca=self.epoca,
            offset=self.offset,
            conteudo=request.conteudo
        )

        entrada_dict = {
            'epoca': self.epoca,
            'offset': self.offset,
            'conteudo': request.conteudo
        }
        self.log.append(entrada_dict)
        self.salvar_em_log(entrada_dict)

        acks = 0
        acked_stubs: list[replicacao_pb2_grpc.ServidorServiceStub] = []
        for stub in self.stubs:
            try:
                resposta = stub.ReplicarEntrada(entrada)
                if resposta.sucesso:
                    acks += 1
                    acked_stubs.append(stub)
            except grpc.RpcError as e:
                print(f"Erro ao replicar dado: {e}")
        
        quorum = len(self.enderecos_replicas) // 2 + 1
        if acks >= quorum:
            commit_req = replicacao_pb2.CommitRequest(
                epoca=self.epoca,
                offset=self.offset
            )
            for stub in acked_stubs:
                try:
                    stub.CommitEntrada(commit_req)
                except grpc.RpcError as e:
                    print(f"Erro ao enviar commit: {e}")
                
            chave = f"entrada_{self.offset}"
            self.banco[chave] = {
                'epoca': self.epoca,
                'offset': self.offset,
                'conteudo': request.conteudo
            }
            self.salvar_em_banco(self.banco[chave])

            print(f"[Líder] Entrada committed: {chave} → {request.conteudo}")
            return replicacao_pb2.Resposta(
                mensagem="Entrada replicada e confirmada com sucesso",
                conteudo=chave
            )
        else:
            print(f"[Líder] Falha no quorum. Apenas {acks} acks recebidos.")
            return replicacao_pb2.Resposta(
                mensagem="Erro: nao foi possível confirmar a entrada (quorum nao atingido).",
                conteudo=""
            )
    
    def Consultar(self, request, context):
        entrada = self.banco.get(request.chave)
        if entrada:
            return replicacao_pb2.Resposta(
                mensagem=f"Dado encontrado na epoca {entrada['epoca']} com offset {entrada['offset']}.",
                conteudo=entrada['conteudo']
            )
        else:
            return replicacao_pb2.Resposta(
                mensagem="Chave não encontrada.",
                conteudo=""
            )
    
    def salvar_em_log(self, entrada):
        try:
            path = f"trabalho5/logs/{self.arquivo_log}"
            with open(path, "a", encoding="utf-8") as f:
                linha = f"{entrada['epoca']},{entrada['offset']},{entrada['conteudo']}\n"
                f.write(linha)
        except Exception as e:
            print(f"[Líder] Erro ao salvar log: {e}")

    def salvar_em_banco(self, entrada):
        try:
            path = f"trabalho5/dados/{self.arquivo_banco}"
            with open(path, "a", encoding="utf-8") as f:
                linha = f"{entrada['epoca']},{entrada['offset']},{entrada['conteudo']}\n"
                f.write(linha)
        except Exception as e:
            print(f"[Líder] Erro ao salvar banco: {e}")
    
    def carrega_banco(self):
        with open(f"trabalho5/dados/{self.arquivo_banco}", "r", encoding="utf-8") as f:
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
    replicas = ["localhost:50052", "localhost:50053", "localhost:50054"]
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lider = Lider(replicas)
    replicacao_pb2_grpc.add_ClienteServiceServicer_to_server(lider, servidor)
    servidor.add_insecure_port(f"[::]:{PORTA}")
    print(f"Lider rodando na porta {PORTA}...")
    servidor.start()
    servidor.wait_for_termination()

if __name__ == '__main__':
    main()