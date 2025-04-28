from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64, os

def gerar_chaves():
    os.makedirs("chave-privada", exist_ok=True)
    os.makedirs("chave-publica", exist_ok=True)
    
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    
    with open("chave-privada/private-key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("./chave-publica/public-key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def assinar_mensagem(mensagem):
    base_dir = os.path.dirname(__file__)
    chave_caminho = os.path.join(base_dir, "chave-privada", "private-key.pem")
    with open(chave_caminho, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None
        )
        assinatura = private_key.sign(
            mensagem,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return assinatura
    