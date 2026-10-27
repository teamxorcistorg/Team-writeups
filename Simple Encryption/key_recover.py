import ast
from z3 import *

with open("output.txt", "r") as f:
    ct = ast.literal_eval(f.read())

key = BitVec("key", 128)
p0 = BitVec("p0", 128)
p1 = BitVec("p1", 128)

solver = Solver()

solver.add(ULT(key, BitVecVal(2**64, 128)))

solver.add(UGE(p0, 32), ULE(p0, 126))
solver.add(UGE(p1, 32), ULE(p1, 126))

solver.add(
    ((key * 73) ^ (key + 2 * p0)) == ct[2]
)

solver.add(
    ((key * ct[2]) ^ (key + 73 * p1)) == ct[3]
)

if solver.check() == sat:
    model = solver.model()

    recovered_key = model.eval(key).as_long()
    first_char = model.eval(p0).as_long()
    second_char = model.eval(p1).as_long()

    print("[+] Recovered key:", recovered_key)
    print("[+] First character:", chr(first_char))
    print("[+] Second character:", chr(second_char))
else:
    print("[-] No solution found")