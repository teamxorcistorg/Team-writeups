import ast

M = 2**128
key = 17608713827523745640

# Read the encrypted output
with open("output.txt", "r") as f:
    ciphertext = ast.literal_eval(f.read())


def encrypt_char(previous_previous, previous, character):
    return (
        (key * previous)
        ^ (key + previous_previous * ord(character))
    ) % M


# The first two values are the initial values.
values = ciphertext[:2]
flag = ""

# Recover each plaintext character.
for i in range(2, len(ciphertext)):
    target = ciphertext[i]

    for code in range(32, 127):
        character = chr(code)

        result = encrypt_char(
            values[-2],
            values[-1],
            character
        )

        if result == target:
            flag += character
            values.append(result)
            break
    else:
        raise ValueError(
            f"No printable ASCII character found at position {i - 2}"
        )

print("[+] Recovered flag:", flag)

# Verify the entire recovered flag.
check = [2, 73]

for character in flag:
    check.append(
        (
            (key * check[-1])
            ^ (key + check[-2] * ord(character))
        ) % M
    )

assert check == ciphertext

print("[+] Ciphertext verification successful!")