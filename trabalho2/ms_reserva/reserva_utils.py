import json 
import os
# ------------------------------------------------ 
# Carrega os itinerários de um arquivo .json
# ------------------------------------------------
def carregar_itinerarios():
      base_path = os.path.dirname(__file__)
      path = os.path.join(base_path, "itinerarios.json")
      print(path)
      with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

# ------------------------------------------------
# Lista todos os itinerários disponíveis 
# ------------------------------------------------
def listar_itinerarios(itinerarios):
      print("\n=== Itinerários Disponíveis ===")
      for i in itinerarios:
            print(f"ID: {i['id']}")
            print(f"Data de Partida Disponíveis: ")
            print(f"Navio: {i['navio']}")
            print(f"Porto de Embarque: {i['porto_embarque']}")
            print(f"Porto de Desembarque: ")
            print(f"Lugares visitados: {','.join(i['lugares_visitados'])}")
            print(f"Número de noites: {i['noites']}")
            print(f"Valor por pessoa: {i['valor_por_pessoa']}")

# ------------------------------------------------
# Consulta itinerários com os filtros do cliente
# ------------------------------------------------
def consultar_itinerarios(itinerarios):
      destino = input("Destino: ").strip()
      data_embarque = input("Data de embarque (YYYY-MM-DD): ").strip()
      porto = input("Porto de embarque: ").strip()

      resultados = [
            i for i in itinerarios
            if destino in i['destino'].strip()
            and data_embarque.strip() in [d.strip() for d in i['data_embarque']]
            and porto in i['porto_embarque'].strip()
      ]

      if not resultados:
            print("\n Nenhum itinerário encontrado com esses critérios.")
            return []
      
      print("\n=== Itinerários Encontrados ===")
      for i in resultados:
            print(f"ID: {i['id']}")
            print(f"Data de Partida Disponíveis: ")
            print(f"Navio: {i['navio']}")
            print(f"Porto de Embarque: {i['porto_embarque']}")
            print(f"Porto de Desembarque: ")
            print(f"Lugares visitados: {','.join(i['lugares_visitados'])}")
            print(f"Número de noites: {i['noites']}")
            print(f"Valor por pessoa: {i['valor_por_pessoa']}")

      return resultados