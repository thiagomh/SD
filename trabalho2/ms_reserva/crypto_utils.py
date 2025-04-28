from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
from os import path

def carregar_chave_publica():
    base_dir = path.dirname(__file__)
    chave_caminho = path.join(base_dir, "chave", "public-key.pem")
    with open(chave_caminho, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read()
        )
    return public_key

def verificar_assinatura(public_key, mensagem: bytes, assinatura):
    try:
        public_key.verify(
            assinatura,
            mensagem, 
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Assinatura inválida: {e}")
        return False