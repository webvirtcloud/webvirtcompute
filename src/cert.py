import os
import secrets
from OpenSSL import crypto


TMPDIR = os.getenv("TMPDIR", "/tmp")


def gen_self_signed_cert(validity_days=3650):
    """
    Generate self-signed certificate and private key and save them to files. Default validity is 10 years.
    """
    generated_hex = secrets.token_hex(8)
    tmp_cert_folder = os.path.join(TMPDIR, generated_hex)
    key_file_path = os.path.join(tmp_cert_folder, "key.pem")
    cert_file_path = os.path.join(tmp_cert_folder, "cert.pem")

    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "California"
    cert.get_subject().L = "San Francisco"
    cert.get_subject().O = "WebVirtCloud"
    cert.get_subject().CN = "localhost"
    cert.get_subject().emailAddress = "admin@webvirt.cloud"
    cert.set_serial_number(0)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(validity_days * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha512")

    os.mkdir(tmp_cert_folder)

    with open(cert_file_path, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

    with open(key_file_path, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))

    return key_file_path, cert_file_path
