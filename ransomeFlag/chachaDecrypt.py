import base64
from chacha_key import chacha_key
from Crypto.Cipher import ChaCha20

encrypted_flag = "4HGJ/3Y6iekXR+FXdpdpa+ww4601QUtLGAzHO/8="
nonce = "nFE+9jfXTKM="

ciphertext = base64.b64decode(encrypted_flag)
nonce_bytes = base64.b64decode(nonce)

cipher = ChaCha20.new(
    key=chacha_key,
    nonce=nonce_bytes
)

plaintext = cipher.decrypt(ciphertext)

print("Decrypted bytes:", plaintext)
print("Flag:", plaintext.decode("utf-8"))
