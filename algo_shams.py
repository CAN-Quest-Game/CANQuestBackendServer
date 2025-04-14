seed = [0x81, 0x6B, 0x11]
key = [hex(seed_val ^ 0xFF) for seed_val in seed]
print("stored key: ", key)