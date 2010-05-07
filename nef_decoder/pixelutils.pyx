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


cdef inline double double_boxit_fast(double x, double low, double high):
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


# @cython.boundscheck(True)
def compute_pixel_values(numpy.ndarray[numpy.double_t, ndim=2] deltas, 
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
    cdef numpy.ndarray[numpy.double_t, ndim=3] pixels = numpy.zeros(shape=(3, h, w), 
                                                                    dtype=numpy.double)
    cdef numpy.ndarray[numpy.double_t, ndim=2] vpreds = numpy.array(vert_preds, 
                                                                    dtype=numpy.double)
    cdef numpy.ndarray[numpy.double_t, ndim=1] hpreds = numpy.array(horiz_preds, 
                                                                    dtype=numpy.double)
    
    # Now, the algorithm above returns colors in RGBG instead of RGBA, so we 
    # have to add plane 3 to plane 1.
    for row in range(h):
        for col in range(w):
            if(col < 2):
                vpreds[row & 1][col] += deltas[row, col]
                hpreds[col] = vpreds[row & 1][col]
            else:
                hpreds[col & 1] += deltas[row, col]
            
            if(col < real_width):
                c = (filters >> ((((row) << 1 & 14) + ((col-left_margin) & 1)) << 1) & 3)
                v = curve[<int>double_boxit_fast(hpreds[col & 1], 0, 0x3fff)]
                if(c == 3):
                    c = 1
                pixels[c, row, col] = <double>v
    return(pixels)


# @cython.boundscheck(True)
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
    cdef numpy.ndarray[numpy.double_t, ndim=2] deltas = numpy.zeros(shape=(height, width), 
                                                                    dtype=numpy.double)
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


def demosaic(numpy.ndarray[numpy.double_t, ndim=3] pixels, 
             bool scale=True, 
             bool equalize=False,
             tuple wb_mult=(1., 1., 1.)):
    """
    We assume for now that the bayer pattern is 
    
        B G B G
        G R G R
    
    Image sizes are even. This means that the padded input image pattern is
        
        0 B G B G 0
        0 G R G R 0
    
    We modify the array in place.
    """
    cdef int i
    cdef int h = pixels.shape[1]
    cdef int w = pixels.shape[2]
    
    # In what follows, we take care of the fact that the pixels at the edges 
    # require special handlimng. The same thing could be achieved by expanding 
    # the input image with a 1 pixel black border all around.
    
    
    # R channel, one row at the time.
    # We determine the (interpolated) red value at green pixel locations by 
    # interpolating the two adjacent red values.
    # Horizontals.
    for i in range(1, h, 2):
        # First the border pixels.
        pixels[0, i, 0] = .5 * pixels[0, i, 1]
        # Then all the rest.
        pixels[0, i, 2:w:2] = .5 * (pixels[0, i, 1:w-2:2] + pixels[0, i, 3:w:2])
    # Verticals.
    # First the top row.
    pixels[0, 0, 1:w:2] = .5 * pixels[0, 1, 1:w:2]
    for i in range(2, h-1, 2):
        # Then everything else.
        pixels[0, i, 1:w:2] = .5 * (pixels[0, i-1, 1:w:2] + 
                                 pixels[0, i+1, 1:w:2])
    
    # We determine the (interpolated) red value at blue pixel locations by 
    # interpolating the four diagonal red values.
    # Top corner pixel.
    pixels[0, 0, 0] = .25 * pixels[0, 1, 1]
    # The rest of the top row.
    pixels[0, 0, 2:w:2] = .25 * (pixels[0, 1, 1:w-2:2] + pixels[0, 1, 3:w:2])
    for i in range(2, h, 2):
        # Edge pixel first.
        pixels[0, i, 0] = .25 * (pixels[0, i-1, 1] + pixels[0, i+1, 1])
        # All the rest.
        pixels[0, i, 2:w:2] = .25 * (pixels[0, i-1, 1:w-2:2] + 
                                  pixels[0, i-1, 3:w:2] + 
                                  pixels[0, i+1, 1:w-2:2] + 
                                  pixels[0, i+1, 3:w:2])
    
    # B channel, one row at the time (same thing as with R).
    # We determine the (interpolated) blue value at green pixel locations by 
    # interpolating the two adjacent blue values.
    # Horizontals.
    for i in range(0, h, 2):
        # The last column.
        pixels[2, i, -1] = .5 * pixels[2, i, -2]
        # The rest.
        pixels[2, i, 1:w-2:2] = .5 * (pixels[2, i, 0:w-3:2] + pixels[2, i, 2:w:2])
    # Verticals.
    # First the bottom row.
    pixels[2, -1, 0:w:2] = .5 * pixels[2, -2, 0:w:2]
    for i in range(1, h-2, 2):
        # Then all the rest.
        pixels[2, i, 0:w:2] = .5 * (pixels[2, i-1, 0:w:2] + 
                                 pixels[2, i+1, 0:w:2])
    
    # We determine the (interpolated) blue value at red pixel locations by 
    # interpolating the four diagonal blue values.
    # Bottom corner pixel.
    pixels[2, -1, -1] = .25 * pixels[2, -2, -2]
    # The rest of the bottom row.
    pixels[2, -1, 1:w-2:2] = .25 * (pixels[2, -2, 0:w-3:2] + pixels[2, -2, 2:w:2])
    for i in range(1, h-2, 2):
        # Edge pixel first.
        pixels[2, i, -1] = .25 * (pixels[2, i-1, -2] + pixels[2, i+1, -2])
        # All the rest.
        pixels[2, i, 1:w-2:2] = .25 * (pixels[2, i-1, 0:w-3:2] + 
                                    pixels[2, i-1, 2:w:2] + 
                                    pixels[2, i+1, 0:w-3:2] + 
                                    pixels[2, i+1, 2:w:2])
    
    # G channel, once row at the time.
    # We determine the (interpolated) green value at red pixel locations by 
    # interpolating the four cross green values.
    # Bottom corner pixel.
    pixels[1, -1, -1] = .25 * (pixels[1, -2, -1] + pixels[1, -1, -2])
    # The rest of the bottom row.
    pixels[1, -1, 1:w-2:2] = .25 * (pixels[1, -1, 0:w-3:2] + 
                                 pixels[1, -1, 2:w:2] + 
                                 pixels[1, -2, 1:w-2:2])
    for i in range(1, h-2, 2):
        # Edge pixel first.
        pixels[1, i, -1] = .25 * (pixels[1, i-1, -1] + 
                               pixels[1, i, -2] + 
                               pixels[1, i+1, -1])
        # All the rest.
        pixels[1, i, 1:w-2:2] = .25 * (pixels[1, i-1, 1:w-2:2] + 
                                    pixels[1, i, 0:w-3:2] + 
                                    pixels[1, i, 2:w:2] + 
                                    pixels[1, i+1, 1:w-2:2])
    
    # We determine the (interpolated) green value at blue pixel locations by 
    # interpolating the four cross green values.
    # Top corner pixel.
    pixels[1, 0, 0] = .25 * (pixels[1, 0, 1] + pixels[1, 1, 0])
    # The rest of the top row.
    pixels[1, 0, 2:w:2] = .25 * (pixels[1, 0, 1:w-2:2] + 
                              pixels[1, 0, 3:w:2] + 
                              pixels[1, 1, 2:w:2])
    for i in range(2, h, 2):
        # Edge pixel first.
        pixels[1, i, 0] = .25 * (pixels[1, i-1, 0] + 
                              pixels[1, i, 1] + 
                              pixels[1, i+1, 0])
        # All the rest.
        pixels[1, i, 2:w:2] = .25 * (pixels[1, i-1, 2:w:2] + 
                                  pixels[1, i, 1:w-2:2] + 
                                  pixels[1, i, 3:w:2] + 
                                  pixels[1, i+1, 2:w:2])
    
    # Correct for white balance.
    pixels[0] *= wb_mult[0]
    pixels[1] *= wb_mult[1]
    pixels[2] *= wb_mult[2]
    
    # Now scale it so that we cover the whole dynamic range.
    if(scale):
        pixels *= 65535. / pixels.max()
    
    # Do we want histogram equalization?
    if(equalize):
        return(histogram_equalize(pixels))
    return(pixels)


def histogram_equalize(numpy.ndarray[numpy.double_t, ndim=3] pixels):
    """
    Histogram equalization, color by color. See
        http://www.janeriksolem.net/2009/06/histogram-equalization-with-python-and.html
    """
    cdef int i
    cdef tuple shp = (pixels.shape[0], pixels.shape[1], pixels.shape[2])
    cdef numpy.ndarray[numpy.double_t, ndim=2] out = numpy.zeros(shape=(shp[0], shp[1]*shp[2]),
                                                                 dtype=numpy.double)
    cdef numpy.ndarray[numpy.double_t, ndim=1] flat = numpy.zeros(shape=(shp[1]*shp[2], ),
                                                                  dtype=numpy.double)
    
    
    for i in range(3):
        flat = pixels[i].flatten()
        
        hist, bins = numpy.histogram(flat, 65535, normed=True)
        cdf = hist.cumsum()
        cdf = 65535 * cdf / cdf[-1]
        out[i] = numpy.interp(flat, bins[:-1], cdf)
    return(out.reshape(shp))































