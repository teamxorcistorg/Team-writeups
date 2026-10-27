import base64

xor_key = "0x1337"

obfuscated_key = bytes.fromhex(
    "cdabcfa1a505e5ea5cb297f476efb09f69e05a84ac361ed38b04dc01586c11bb"
)

chacha_key = bytes(
    b ^ ord(xor_key[i % len(xor_key)])
    for i, b in enumerate(obfuscated_key)
)

print("Original ChaCha20 key (hex):", chacha_key.hex())
print("Original ChaCha20 key (Base64):", base64.b64encode(chacha_key).decode())
