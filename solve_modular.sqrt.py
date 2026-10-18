    if checker is None:
        raise RuntimeError(
            "This MathForge installation does not expose is_probable_prime(). "
            "Update/reinstall MathForge, then try again."
        )
    return bool(checker(p))


def tonelli_shanks(a: int, p: int) -> int:
    """Return the smaller square root r such that r² ≡ a (mod p).

    p must be an odd prime, except that p=2 is handled directly.
    """
    if p < 2:
        raise ValueError("Modulus p must be a prime greater than or equal to 2.")

    a %= p

    if p == 2:
        return a
    if p % 2 == 0:
        raise ValueError("Tonelli-Shanks requires an odd prime modulus.")

    # MathForge's is_prime() intentionally has a deterministic size bound.
    # The challenge's 2048-bit p is beyond that bound, so use its probable-prime API.
    if not probable_prime_check(p):
        raise ValueError("The modulus p did not pass MathForge's probable-prime test.")

    if a == 0:
        return 0

    # Euler's criterion: a is a quadratic residue iff a^((p-1)/2) ≡ 1 mod p,
    # for nonzero a and prime p.
    legendre = mf.pow_mod(a, (p - 1) // 2, p)
    if legendre != 1:
        raise ValueError("a is not a quadratic residue modulo p; no square root exists.")

    # Write p - 1 = q * 2**s, with q odd.
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    # Find a quadratic non-residue z, for which z^((p-1)/2) ≡ -1 mod p.
    z = 2
    while mf.pow_mod(z, (p - 1) // 2, p) != p - 1:
        z += 1

    m = s
    c = mf.pow_mod(z, q, p)
    t = mf.pow_mod(a, q, p)
    r = mf.pow_mod(a, (q + 1) // 2, p)

    while t != 1:
        # Find the smallest i > 0 such that t^(2**i) ≡ 1 mod p.
        i = 1
        t2 = mf.pow_mod(t, 2, p)
        while i < m and t2 != 1:
            t2 = mf.pow_mod(t2, 2, p)
            i += 1

        if i >= m:
            raise ArithmeticError("Tonelli-Shanks could not find the required exponent.")

        b = mf.pow_mod(c, 1 << (m - i - 1), p)
        r = (r * b) % p
        t = (t * b * b) % p
        c = (b * b) % p
        m = i

    # Always verify the result before returning it.
    if (r * r) % p != a:
        raise ArithmeticError("Root verification failed; check the input and implementation.")

    # For nonzero a, the two roots are r and p-r. Return the smaller one.
    return min(r, p - r)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find the smaller modular square root for a CryptoHack challenge."
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default=DEFAULT_OUTPUT,
        help=f"path to challenge output file (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    try:
        p, a = read_challenge_values(Path(args.output_file))
        root = tonelli_shanks(a, p)
    except (OSError, ValueError, RuntimeError, ArithmeticError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"p = {p}")
    print(f"a = {a}")
    print(f"smaller root = {root}")
    print(f"verification = {(root * root) % p == a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
