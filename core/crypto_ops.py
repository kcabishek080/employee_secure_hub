import os
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from core.auth import log_event
from cryptography import x509

PKI_DIR = "pki"
USERS_DIR = f"{PKI_DIR}/users"
INBOX_DIR = "inbox"


# ---------------- UTIL ----------------
def load_private_key(username):
    with open(f"{USERS_DIR}/{username}/private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_cert(username):
    with open(f"{USERS_DIR}/{username}/cert.pem", "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


def load_ca_cert():
    with open(f"{PKI_DIR}/ca/ca_cert.pem", "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


# ---------------- ENCRYPT + SIGN ----------------
def encrypt_and_sign_file(sender, recipient, file_path):
    os.makedirs(INBOX_DIR, exist_ok=True)
    log_event(sender, "SEND_FILE", recipient)

    sender_key = load_private_key(sender)
    sender_cert = load_cert(sender)
    recipient_cert = load_cert(recipient)

    with open(file_path, "rb") as f:
        data = f.read()

    # AES-GCM encryption
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)

    # Wrap AES key using recipient public key (RSA-OAEP)
    wrapped_key = recipient_cert.public_key().encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Sign ciphertext (RSA-PSS)
    signature = sender_key.sign(
        ciphertext,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    package = {
        "sender": sender,
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "wrapped_key": base64.b64encode(wrapped_key).decode(),
        "signature": base64.b64encode(signature).decode()
    }

    out_file = f"{INBOX_DIR}/{recipient}_{sender}.pkg"
    with open(out_file, "w") as f:
        json.dump(package, f, indent=2)


# ---------------- LIST INBOX ----------------
def list_inbox(username):
    if not os.path.exists(INBOX_DIR):
        return []

    return [
        f for f in os.listdir(INBOX_DIR)
        if f.startswith(username + "_")
    ]


# ---------------- VERIFY + DECRYPT ----------------
def verify_and_decrypt(recipient, package_file):
    package_path = f"{INBOX_DIR}/{package_file}"

    with open(package_path, "r") as f:
        package = json.load(f)

    sender = package["sender"]
    log_event(recipient, "VERIFY_AND_DECRYPT", sender)

    sender_cert = load_cert(sender)
    recipient_key = load_private_key(recipient)

    nonce = base64.b64decode(package["nonce"])
    ciphertext = base64.b64decode(package["ciphertext"])
    wrapped_key = base64.b64decode(package["wrapped_key"])
    signature = base64.b64decode(package["signature"])

    # Verify signature
    sender_cert.public_key().verify(
        signature,
        ciphertext,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Unwrap AES key
    aes_key = recipient_key.decrypt(
        wrapped_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt file
    aesgcm = AESGCM(aes_key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    output_path = f"decrypted_{package_file}.bin"
    with open(output_path, "wb") as f:
        f.write(plaintext)

    return output_path
