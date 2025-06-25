from OpenSSL import crypto
import os

def generate_self_signed_cert():
    # Créer le dossier certs s'il n'existe pas
    if not os.path.exists('certs'):
        os.makedirs('certs')

    # Générer la clé
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)

    # Générer le certificat
    cert = crypto.X509()
    cert.get_subject().CN = "TIKTOK-API"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valide pour un an
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    # Sauvegarder le certificat et la clé
    with open("certs/cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open("certs/key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    print("Certificat SSL auto-signé généré avec succès dans le dossier 'certs'")

if __name__ == '__main__':
    generate_self_signed_cert() 