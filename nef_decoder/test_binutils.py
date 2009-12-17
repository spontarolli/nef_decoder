import struct
import sys
import time

import binutils




N = int(1e5)
def int2bin(n, count=36):
    """returns the binary of integer n, using count number of digits"""
    return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])



dt = 0
for i in range(-N, N, 1):
    t0 = time.time()
    bin_str = binutils.int2bin(i, 32)
    dt += time.time() - t0
    
    if(i >= 0):
        assert(binutils.bin2int(bin_str) == i)
    else:
        assert(int(bin_str, 2) - 2**32 == i)
print('binutils: %d int -> bin: %.02fs' % (2*N, dt))
print('binutils: %.02f int -> bin/s' % (float(2*N) / dt))


# dt = 0
# for i in range(-N, N, 1):
#     t0 = time.time()
#     bin_str = int2bin(i, 36)
#     dt += time.time() - t0
#     assert(int(bin_str, 2) == i)
# print('slow: %d iterations: %.02fs' % (N, dt))
# print('slow: %.02f iterations/s' % (float(N) / dt))


test_data2bin = True
try:
    data = open(sys.argv[1], 'rb').read()
except:
    print('Specify an input file to test data2bin.')
    test_data2bin = False
if(test_data2bin):
    barray = ''.join([binutils.int2bin(i, 32)[24:] 
                      for i in struct.unpack('%dB' % (len(data)), data)])
    
    t0 = time.time()
    mine = binutils.data2bin(data)
    dt = time.time() - t0
    print('binutils: str[%d] -> bin: %.02fs' % (len(data), dt))
    print('binutils: %.02f ch -> bin/s' % (float(len(data)) / dt))
    assert(len(mine) == 8 * len(data))
    assert(mine == barray)


























