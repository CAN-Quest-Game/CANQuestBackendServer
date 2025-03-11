seed = [0x20, 0x04, 0xAC]
key = [hex(seed_val ^ 0xFF) for seed_val in seed]
print("stored key: ", key)