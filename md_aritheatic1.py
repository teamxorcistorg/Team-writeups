a = int(input("Enter the first number: "))
m = int(input("Enter the first modulus: "))

b = int(input("Enter the second number: "))
n = int(input("Enter the second modulus: "))

x = a % m
y = b % n

print("x =", x)
print("y =", y)
print("Smaller value =", min(x, y))
