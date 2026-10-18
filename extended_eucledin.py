
def extended_gcd(a, b):
    if a == 0 and b == 0:
        raise ValueError("GCD(0, 0) is undefined.")

    # Work with absolute values first
    A, B = abs(a), abs(b)

    # Remainder values
    r0, r1 = A, B

    # Coefficients of A
    x0, x1 = 1, 0

    # Coefficients of B
    y0, y1 = 0, 1

    print("\nEXTENDED EUCLIDEAN ALGORITHM")
    print("=" * 65)
    print(f"Finding GCD of {a} and {b}\n")

    print("Step-by-step division:")
    step = 1

    while r1 != 0:
        q = r0 // r1
        r2 = r0 - q * r1

        # Calculate coefficients for the new remainder
        x2 = x0 - q * x1
        y2 = y0 - q * y1

        print(
            f"Step {step}: {r0} = {q} * {r1} + {r2}"
        )
        print(
            f"         {r2} = ({x2}) * {A} "
            f"+ ({y2}) * {B}"
        )

        # Update the values
        r0, r1 = r1, r2
        x0, x1 = x1, x2
        y0, y1 = y1, y2

        step += 1

    # Restore signs for the original inputs
    x = x0 if a >= 0 else -x0
    y = y0 if b >= 0 else -y0
    gcd = r0

    print("\nFINAL RESULTS")
    print("=" * 65)
    print(f"First number (a)  = {a}")
    print(f"Second number (b) = {b}")
    print(f"GCD(a, b)         = {gcd}")
    print(f"Coefficient x     = {x}")
    print(f"Coefficient y     = {y}")
    print(f"Bézout identity   = ({a})({x}) + ({b})({y}) = {gcd}")

    return gcd, x, y


# Take input from the user
a = int(input("Enter the first integer: "))
b = int(input("Enter the second integer: "))

extended_gcd(a, b)
