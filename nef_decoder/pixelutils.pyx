# cython: profile=False
import numpy
cimport numpy
# cimport cython



# Utility routines.
cdef inline int int_boxit_fast(int x, int low, int high):
    if(x < low):
        return(low)
    elif(x > high):
        return(high)
    return(x)


cdef inline int bintoint(char* bin, int f, int l):
    # Convert the binary string `bin` of length `len` into an integer.
    # We assume that bin is a string composed of '1's and '0's only but we do 
    # not check (for performance reasons).
    cdef Py_ssize_t  k
    cdef int  sum = 0
    cdef unsigned short i
    
    for k from f <= k < f+l:
        i = <unsigned int>bin[k]
        sum = sum + i * (1 << (l-k-1+f))
    return(sum)


# @cython.boundscheck(False)
def compute_pixel_values(numpy.ndarray[numpy.int16_t, ndim=2] deltas, 
                         list horiz_preds, 
                         list vert_preds, 
                         tuple curve, 
                         int left_margin=0):
    """
    First take the first column and, starting from the bottom (actally the 
    second to last pixel) and going up, add to each delta the value immediately 
    before it.
    
    Then, for every row, starting from the left (again, from the second item) 
    and going right, add to each delta the value immediately to its left.
    
    What you get are the linearity corrected pixel values. You should really do 
    it color by color.
    """
    # TODO: This has to computed from the CFA Pattern 2 tag value!
    filters = 0x1e1e1e1e
    
    cdef Py_ssize_t h = deltas.shape[0]
    cdef Py_ssize_t w = deltas.shape[1]
    cdef Py_ssize_t real_width = w - 1
    cdef Py_ssize_t row = 0
    cdef Py_ssize_t col = 0
    cdef Py_ssize_t c = 0
    cdef Py_ssize_t v = 0
    cdef int curve_len = len(curve) - 1
    cdef numpy.ndarray[numpy.uint8_t, ndim=3] pixels = numpy.zeros(shape=(h, w, 4), 
                                                                   dtype=numpy.uint8)
    cdef numpy.ndarray[numpy.int16_t, ndim=2] vpreds = numpy.array(vert_preds, 
                                                                   dtype=numpy.int16)
    cdef numpy.ndarray[numpy.int16_t, ndim=1] hpreds = numpy.array(horiz_preds, 
                                                                   dtype=numpy.int16)
    
    for row in range(h):
        for col in range(w):
            if(col < 2):
                vpreds[row & 1][col] += deltas[row, col]
                hpreds[col] = vpreds[row & 1][col]
            else:
                hpreds[col & 1] += deltas[row, col]
            
            if(col < real_width):
                c = (filters >> ((((row) << 1 & 14) + ((col-left_margin) & 1)) << 1) & 3)
                v = curve[int_boxit_fast(hpreds[col & 1], 0, 0x3fff)]
                pixels[row, col, c] = v
    return(pixels)


# @cython.boundscheck(False)
def decode_pixel_deltas(Py_ssize_t width, 
                        Py_ssize_t height, 
                        int tree_index, 
                        numpy.ndarray[numpy.uint8_t, ndim=1] bit_buffer, 
                        int split_row,
                        list NIKON_TREE):
    """
    Instead of encoding the raw pixel values, NEFs encode the difference between
    each pixel and the pixel to its left (row-wise). The sam ething happens for 
    pixels of the first column (each is subtracted to the pixel above). The
    differences, or deltas, are then turned into binary and the length of their 
    binary representation is huffman encoded. What we have in the NEF is the
    huffman encoded list of delta lengths. The nice thing about huffman encoding
    is that no leaf value (in binary) is a prefix of any other value.
    """
    # Decode the pixels, one by one. This is still very confusing to me.
    cdef int position = 0
    cdef Py_ssize_t num_bits = 0
    cdef list tree = []
    cdef int len_tree = len(tree)
    cdef int huff_idx = 0
    cdef int num_read = 0
    cdef int raw_len = 0
    cdef int corr = 0
    cdef int delta_len = 0
    cdef int x = 0
    cdef int delta = 0
    cdef Py_ssize_t row = 0
    cdef Py_ssize_t col = 0
    cdef numpy.ndarray[numpy.int16_t, ndim=2] deltas = numpy.zeros(shape=(height, width), 
                                                                   dtype=numpy.int16)
    cdef char* bit_buffer_ptr = <char*>bit_buffer.data
    
    
    num_bits, tree = NIKON_TREE[tree_index]
    if(split_row == -1):
        for row in range(height):
            for col in range(width):
                # Read num_bits bits from the file (or wherever the data is stored),
                # interpret them as a C unsigned char from which you can derive a
                # bunch of stuff (using the appropriate Huffman tree):
                #  - The length in bits of the acual data on the tree.
                #  - The length in bits of the pixel delta (in binary form).
                #  - Any correction to the length above.
                # Conveniently, the trees in huffman_tables.py already provide those
                # numbers in the right place:
                #  tree[i] = (bits_read, length, currection, length-corection)
                huff_idx = bintoint(bit_buffer_ptr, position, num_bits)
                
                (num_read, raw_len, corr, delta_len) = tree[huff_idx]
                position += num_read
                
                # Now read delta_len bits. That, pretty much, is the difference in 
                # value between adjacent pixel values: 
                #  delta = pixel - pixel_to_the_left
                # Beware that the same treatement is done vertically to the first 
                # column.
                if(not delta_len):
                    delta = 0
                else:
                    x = bintoint(bit_buffer_ptr, position, delta_len)
                    delta = ((x << 1) + 1) << corr >> 1
                    if((delta & (1 << (raw_len - 1))) == 0 and corr == 0):
                        # In C !0 = 1; in Python ~0 = -1...
                        delta -= (1 << raw_len) - 1
                    elif((delta & (1 << (raw_len - 1))) == 0 and corr != 0):
                        delta -= (1 << raw_len)
                
                deltas[row, col] = delta
                position += delta_len
    else:
        for row in range(height):
            if(row == split_row):
                num_bits, tree = NIKON_TREE[tree_index+1]
            
            for col in range(width):
                # Read num_bits bits from the file (or wherever the data is stored),
                # interpret them as a C unsigned char from which you can derive a
                # bunch of stuff (using the appropriate Huffman tree):
                #  - The length in bits of the acual data on the tree.
                #  - The length in bits of the pixel delta (in binary form).
                #  - Any correction to the length above.
                # Conveniently, the trees in huffman_tables.py already provide those
                # numbers in the right place:
                #  tree[i] = (bits_read, length, currection, length-corection)
                huff_idx = bintoint(bit_buffer_ptr, position, num_bits)
                
                (num_read, raw_len, corr, delta_len) = tree[huff_idx]
                position += num_read
                
                # Now read delta_len bits. That, pretty much, is the difference in 
                # value between adjacent pixel values: 
                #  delta = pixel - pixel_to_the_left
                # Beware that the same treatement is done vertically to the first 
                # column.
                if(not delta_len):
                    delta = 0
                else:
                    x = bintoint(bit_buffer_ptr, position, delta_len)
                    delta = ((x << 1) + 1) << corr >> 1
                    if((delta & (1 << (raw_len - 1))) == 0 and corr == 0):
                        # In C !0 = 1; in Python ~0 = -1...
                        delta -= (1 << raw_len) - 1
                    elif((delta & (1 << (raw_len - 1))) == 0 and corr != 0):
                        delta -= (1 << raw_len)
                
                deltas[row, col] = delta
                position += delta_len
    return(deltas)






