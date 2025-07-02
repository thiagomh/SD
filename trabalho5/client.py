import grpc
import replicacao_pb2
import replicacao_pb2_grpc
from replicacao_pb2_grpc import ClienteServiceStub

def enviar_dado(stub: ClienteServiceStub):
    conteudo = input("Digite os dados para envio: ")
    dado = replicacao_pb2.Dado(conteudo=conteudo)
    resposta = stub.EnviarDado(dado)
    print(f"Resposta do líder: {resposta.mensagem}")

def consultar_dado(stub: ClienteServiceStub):
    chave = input("Digite a chave de consulta: ")
    consulta = replicacao_pb2.Consulta(chave=chave)
    resposta = stub.Consultar(consulta)
    print(f"Mensagem: {resposta.mensagem}")
    if resposta.conteudo:
        print(f"Conteudo encontrado: {resposta.conteudo}")
    else:
        print(f"Conteúdo não encontrado.")

def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = ClienteServiceStub(channel)

        while True:
            print("1. Enviar dado")
            print("2. Consultar dado")
            print("0. Sair")

            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                enviar_dado(stub)
            elif opcao == "2":
                consultar_dado(stub)
            elif opcao == "0":
                print("Saindo do cliente.")
                break
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == '__main__':
    main()