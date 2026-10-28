import math
import re

# Read the RSA values
with open("output.txt", "r") as f:
    data = f.read()

values = {
    key: int(value)
    for key, value in re.findall(r"([nec])\s*=\s*(\d+)", data)
}

n = values["n"]
e = values["e"]
c = values["c"]

# Step 1: Fermat factorization
a = math.isqrt(n)

if a * a < n:
    a += 1

while True:
    b_squared = a * a - n
    b = math.isqrt(b_squared)

    if b * b == b_squared:
        p = a - b
        q = a + b
        break

    a += 1

print("[+] Factors recovered!")
print(f"p = {p}")
print(f"q = {q}")
print(f"Verified: {p * q == n}")

# Step 2: Calculate the private exponent
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)

# Step 3: Decrypt the ciphertext
m = pow(c, d, n)

# Step 4: Convert the integer into bytes
flag = m.to_bytes((m.bit_length() + 7) // 8, "big")

print(f"\n[+] Flag: {flag.decode()}")