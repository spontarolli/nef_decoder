import time

import binutils
import slow


N = int(1e5)


dt = 0
for i in range(N):
    t0 = time.time()
    bin_str = binutils.int2bin(i, 36)
    dt += time.time() - t0
    
    assert(binutils.bin2int(bin_str) == i)
print('binutils: %d iterations: %.02fs' % (N, dt))
print('binutils: %.02f iterations/s' % (float(N) / dt))


dt = 0
for i in range(N):
    t0 = time.time()
    bin_str = slow.int2bin(i, 36)
    dt += time.time() - t0
    assert(int(bin_str, 2) == i)
print('slow: %d iterations: %.02fs' % (N, dt))
print('slow: %.02f iterations/s' % (float(N) / dt))