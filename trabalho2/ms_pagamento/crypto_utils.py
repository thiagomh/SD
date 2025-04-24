from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import base64

def gerar_chaves():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open("chaves/private.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("chaves/public.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def assinar_mensagem(mensagem_json: str) -> str:
    with open("chaves/private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None
        )
        assinatura = private_key.sign(
            mensagem_json.encode()

        )
        return base64.b64encode(assinatura).decode()