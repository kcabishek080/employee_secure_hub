import os
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature

# ---------------- PATHS ----------------
BASE_DIR = "pki"
CA_DIR = os.path.join(BASE_DIR, "ca")
USERS_DIR = os.path.join(BASE_DIR, "users")
CRL_FILE = os.path.join(BASE_DIR, "revoked.txt")

CA_KEY_PATH = os.path.join(CA_DIR, "ca.key")
CA_CERT_PATH = os.path.join(CA_DIR, "ca.crt")

# ---------------- CA INIT ----------------
def init_ca():
    if os.path.exists(CA_CERT_PATH):
        return  # already initialized

    os.makedirs(CA_DIR, exist_ok=True)

    ca_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    with open(CA_KEY_PATH, "wb") as f:
        f.write(
            ca_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            )
        )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Employee Secure Hub Root CA")
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    with open(CA_CERT_PATH, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


# ---------------- CERT ISSUE ----------------
def issue_user_certificate(username):
    if not os.path.exists(CA_CERT_PATH):
        raise Exception("CA not initialized")

    user_dir = os.path.join(USERS_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    # Generate user key
    user_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    with open(os.path.join(user_dir, "private_key.pem"), "wb") as f:
        f.write(
            user_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            )
        )

    # Load CA
    with open(CA_KEY_PATH, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(CA_CERT_PATH, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, username)
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(user_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )

    with open(os.path.join(user_dir, "cert.pem"), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


# ---------------- CERT CHECK ----------------
def has_valid_cert(username):
    cert_path = os.path.join(USERS_DIR, username, "cert.pem")
    if not os.path.exists(cert_path):
        return False

    if is_revoked(username):
        return False

    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    now = datetime.datetime.utcnow()
    return cert.not_valid_before <= now <= cert.not_valid_after


# ---------------- NONCE AUTH ----------------
def nonce_authenticate(username):
    if not has_valid_cert(username):
        return False

    user_dir = os.path.join(USERS_DIR, username)

    with open(os.path.join(user_dir, "private_key.pem"), "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(os.path.join(user_dir, "cert.pem"), "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    nonce = os.urandom(32)

    signature = private_key.sign(
        nonce,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    try:
        cert.public_key().verify(
            signature,
            nonce,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False


# ---------------- ENCRYPT + SIGN ----------------
def encrypt_and_sign(data: bytes, sender: str, recipient: str):
    if not has_valid_cert(sender):
        raise Exception("Sender certificate invalid")

    if not has_valid_cert(recipient):
        raise Exception("Recipient certificate invalid")

    # AES
    aes_key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(aes_key)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, data, None)

    # Load recipient public key
    with open(os.path.join(USERS_DIR, recipient, "cert.pem"), "rb") as f:
        rec_cert = x509.load_pem_x509_certificate(f.read())

    wrapped_key = rec_cert.public_key().encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Sign ciphertext
    with open(os.path.join(USERS_DIR, sender, "private_key.pem"), "rb") as f:
        sender_key = serialization.load_pem_private_key(f.read(), password=None)

    signature = sender_key.sign(
        ciphertext,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return nonce, ciphertext, wrapped_key, signature


# ---------------- VERIFY + DECRYPT ----------------
def verify_and_decrypt(package, sender, recipient):
    nonce, ciphertext, wrapped_key, signature = package

    if not has_valid_cert(sender):
        raise Exception("Sender certificate invalid")

    # Verify signature
    with open(os.path.join(USERS_DIR, sender, "cert.pem"), "rb") as f:
        sender_cert = x509.load_pem_x509_certificate(f.read())

    sender_cert.public_key().verify(
        signature,
        ciphertext,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Decrypt AES key
    with open(os.path.join(USERS_DIR, recipient, "private_key.pem"), "rb") as f:
        rec_key = serialization.load_pem_private_key(f.read(), password=None)

    aes_key = rec_key.decrypt(
        wrapped_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    aes = AESGCM(aes_key)
    return aes.decrypt(nonce, ciphertext, None)


# ---------------- REVOCATION ----------------
def revoke_user(username):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(CRL_FILE, "a") as f:
        f.write(username + "\n")

def is_revoked(username):
    if not os.path.exists(CRL_FILE):
        return False
    with open(CRL_FILE) as f:
        return username in f.read().splitlines()
