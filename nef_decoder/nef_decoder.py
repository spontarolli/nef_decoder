#!/usr/bin/env python
"""
NEF Decoder

Decode a NEF file and turn it into a TIFF or JPEG, depending on user-specified 
output file extension. If no output file is specified, the input NEF is 
converted to TIFF and simply printed to STDOUT.


Usage
    nef_decoder.py [options] <NEF file name>


Options
    -v          verbose (default not vcerbose)
    -o FILE     write the output to FILE. Output type is inferred from file 
                extension.


Example
    nef_decoder.py -o bar.jpg foo.nef
"""
import os
import struct

import pixelutils

import numpy

from huffman_tables import huff as NIKON_TREE

# File format resources:
# Nikon tags: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/Nikon.html
# EXIF tags: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/EXIF.html
# NEF format: http://lclevy.free.fr/nef/
# "": http://www.tidalwave.it/infoglueDeliverLive/ViewPage.action?siteNodeId=186



# Constants
EXIF_TAGS = dict([(1,    'Firmware'),
                  (2,    'ISO'),
                  (3,    'Color Mode'),
                  (4,    'Quality'),
                  (5,    'White Balance'),
                  (6,    'Sharpening'),
                  (7,    'Focus Mode'),
                  (8,    'Flash Setting'),
                  (9,    'Auto Flash Mode'),
                  (11,   'White Balance Fine'),
                  (12,   'White Balance RB Coefficients'),
                  (14,   'Exposure Difference'),
                  (15,   'ISO Selection'),
                  (16,   'Data Dump'),
                  (17,   'Thumbnail Offset'),
                  (18,   'Flash Compensation'),
                  (19,   'ISO Requested'),
                  (22,   'NDF Image Boundary'),
                  (24,   'Flash Bracket Compensation'),
                  (25,   'AE Bracket Compensation'),
                  (27,   'Sensor Size'),
                  (29,   'D2X Serial Number'),
                  
                  (128,  'Image Adjustment'),
                  (129,  'Tone Compensation'),
                  (130,  'Lens Adapter'),
                  (131,  'Lens Type'),
                  (132,  'Lens Range'),
                  (133,  'Focus Distance'),
                  (134,  'Digital Zoom'),
                  (135,  'Flash Type'),
                  (136,  'AF Focus Position'),
                  (137,  'Bracketing'),
                  (139,  'Lens F Stop'),
                  (140,  'Curve'),
                  (141,  'Color Mode'),
                  (142,  'Lighting Type'),
                  (143,  'Scene Mode'),
                  (144,  'Light Type'),
                  (146,  'Hue'),
                  (147,  'Flash'),
                  (148,  'Saturation'),
                  (149,  'Noise Reduction'),
                  (150,  'Compression Data'),
                  (152,  'Lens Info'),
                  (153,  'Bayer Unit Count'),
                  (154,  'Sensor Pixel Size'),
                  (160,  'Camera Serial Number'),
                  (162,  'NDF Length'),
                  (167,  'Shutter Count'),
                  (169,  'Image Optimization'),
                  (170,  'Saturation'),
                  (171,  'Vari Program'),
                  
                  (254,  'Image Type'),
                  (256,  'Image Width'),
                  (257,  'Image Height'),
                  (258,  'Image Bits Per Sample'),
                  (259,  'Image Compression'),
                  (262,  'Image Pixel Array Type'),
                  
                  (271,  'Camera Make'),
                  (272,  'Camera Model'),
                  (273,  'Image Offset'),
                  (274,  'Image Orientation'),
                  
                  (277,  'Image Samples Per Pixel'),
                  (278,  'Image Rows Per Strip'),
                  (279,  'Image Bytes Per Strip'),
                  
                  (282,  'Image X-Axis Resolution'),
                  (283,  'Image Y-Axis Resolution'),
                  (284,  'Image Planar Configuration'),
                  
                  (296,  'Image Resolution Units'),
                  
                  (305,  'Software String'),
                  (306,  'Modification Date'),
                  
                  (330,  'Child IFD Offsets'),
                  
                  (532,  'Black/White Pixel Values'),
                  
                  (3584, 'Print IM'),
                  (3585, 'Capture Editor Data'),
                  (3598, 'Capture Offsets'),
                  
                  (34665, 'EXIF IFD Offset'),
                  
                  (36867, 'Original Date'),
                  
                  (37398, 'TIFF-EP Standard ID'),
                  
                  (33434, 'Exposure Time'),
                  
                  (33437, 'f Stop'),
                  (34850, 'Exposure Program'),
                  (36868, 'Exposure Date'),
                  (37380, 'Exposure Compensation'),
                  (37381, 'Maximum Aperture'),
                  (37383, 'Metering Mode'),
                  (37384, 'White Balance Preset'),
                  (37385, 'Flash'),
                  (37386, 'Focal Length'),
                  
                  (37500, 'Makernote'),
                  
                  (37510, 'User Comments'),        
                  (37520, 'Sub-Second Time'),
                  (37521, 'Sub-Second Time Original'),
                  (37522, 'Sub-Second Time Exposure'),
                  (41495, 'Sensing Method'),
                  (41728, 'File Source'),
                  (41729, 'Scene Type'),
                  (41730, 'CFA Pattern'),
                  (41985, 'Custom Rendered'),
                  (41986, 'Exposure Mode'),
                  (41987, 'White Balance Auto/Manual'),
                  (41988, 'Digital Zoom'),
                  (41989, 'Focal Length (35mm Equivalent)'),
                  (41990, 'Orientation'),
                  (41991, 'Gain Control'),
                  (41992, 'Contrast Setting'),
                  (41993, 'Saturation Setting'),
                  (41994, 'Sharpness Setting'),
                  (41996, 'Subject Distance Range'),
                  (33421, 'CFA Repeat Pattern Dimension'),
                  (33422, 'CFA Pattern 2'),
                  (37399, 'Sensing Method'),
                  (513,   'Thumbnail Offset'),
                  (514,   'Thumbnail Data Length'),
                  (531,   'YCbCr Positioning'),
                 ])
NIKON_TAGS = dict([(1,    'Makernote Version'),
                   (2,    'ISO'),
                   (4,    'Quality'),
                   (5,    'White Balance'),
                   (6,    'Sharpness'),
                   (7,    'Focus Mode'),
                   (8,    'Flash Setting'),
                   (9,    'Flash Type'),
                   (11,   'White Balance Fine Tune'),
                   (13,   'Program Shift'),
                   (14,   'Exposure Difference'),
                   (17,   'Nikon Preview Offset'),
                   (18,   'Flash Exposure Comp'),
                   (19,   'ISO Setting'),
                   (23,   'EV Value?'),
                   (24,   'Flash Exposure Bracket Value'),
                   (25,   'Exposure Bracket Value'),
                   (29,   'Serial Number (Encryption Key)'),
                   (129,  'Tone Compensation'),
                   (131,  'Lens Type'),
                   (132,  'Lens'),
                   (135,  'Flash Mode'),
                   (136,  'AF Info'),
                   (137,  'Shooting Mode'),
                   (139,  'Lens F/Stops'),
                   (140,  'Contrast Curve'),
                   (141,  'Color Hue'),
                   (144,  'Light Source'),
                   (145,  'Shot Info Block'),
                   (146,  'Hue Adjustment'),
                   (147,  'NEF Compression'),
                   (149,  'Noise Reduction'),
                   (150,  'Linearization Table'),
                   (151,  'Color Balance'),
                   (152,  'Lens Data'),
                   (153,  'Raw Image Center'),
                   (154,  'Sensor Pixel Size'),
                   (160,  'Serial Number'),
                   (164,  'Image Version Number?'),
                   (167,  'Shutter Count (Encryption Key)'),
                   (168,  'Flash Info Block'),
                   (169,  'Image Optimization'),
                   (170,  'Saturation'),
                   (171,  'Vari Program'),
                  ])

MAKERNOTE_TAG_ID = 37500
NIKON_LINCURVE_TAG_ID = 150

IMAGE_TYPE_TAG_ID = 0x00fe
IMAGE_WIDTH_TAG_ID = 256
IMAGE_HEIGHT_TAG_ID = 257
IMAGE_BPS_TAG_ID = 258
IMAGE_COMPRESSION_TAG_ID = 0x0103
IMAGE_ARRAY_TYPE_TAG_ID = 0x0106
IMAGE_OFFSET_TAG_ID = 0x0111
IMAGE_ORIENTATION_TAG_ID = 0x0112
IMAGE_SPP_TAG_ID = 0x0115
IMAGE_ROWS_PER_STRIP_TAG_ID = 0x0116
IMAGE_BYTES_PER_STRIP_TAG_ID = 0x0117
IMAGE_PLANAR_CONFIG_TAG_ID = 0x011c
IMAGE_CFA_PATT_REPEAT_TAG_ID = 0x828d
IMAGE_CFA_PATT_TAG_ID = 0x828e
IMAGE_SENSING_TAG_ID = 0x9217

RAW_IMAGE_TYPE = 0
NEF_COMPRESSION_TAG_ID = 147


# Type ID: (Data type format, size in bytes)
# Type formats that start with '_' are custom.
TYPES = {1:   ('B',         1),
         2:   ('_str',      1),                           # Simple string.
         3:   ('H',         2),
         4:   ('L',         4),
         5:   ('_urational',8),                           # rational
         6:   ('b',         1),
         7:   ('B',         1),                           # undefined.
         8:   ('h',         2),
         9:   ('l',         4),
         10:  ('_rational', 8),                           # signed rational
         11:  ('f',         4),
         12:  ('d',         8)}

DEF_TYPE =    ('B',    1)
CHILD_IFD_TAGS = (330, 34665)

VERBOSE_TAG_FMT = '0x%04x  %s  %s  %02d  %s'




def get_raw_image_info(ifds, 
                       img_type_tag_id=IMAGE_TYPE_TAG_ID,
                       img_width_tag_id=IMAGE_WIDTH_TAG_ID,
                       img_height_tag_id=IMAGE_HEIGHT_TAG_ID,
                       img_bps_tag_id=IMAGE_BPS_TAG_ID,
                       img_compression_tag_id=IMAGE_COMPRESSION_TAG_ID,
                       img_array_type_tag_id=IMAGE_ARRAY_TYPE_TAG_ID,
                       img_offset_tag_id=IMAGE_OFFSET_TAG_ID,
                       img_orientation_tag_id=IMAGE_ORIENTATION_TAG_ID,
                       img_spp_tag_id=IMAGE_SPP_TAG_ID,
                       img_rpstrip_tag_id=IMAGE_ROWS_PER_STRIP_TAG_ID,
                       img_bpstrip_tag_id=IMAGE_BYTES_PER_STRIP_TAG_ID,
                       img_planar_config_tag_id=IMAGE_PLANAR_CONFIG_TAG_ID,
                       img_cfa_repeat_size_tag_id=IMAGE_CFA_PATT_REPEAT_TAG_ID,
                       img_cfa_pattern_tag_id=IMAGE_CFA_PATT_TAG_ID,
                       img_sensing_tag_id=IMAGE_SENSING_TAG_ID,
                       raw_image_type=RAW_IMAGE_TYPE,
                       verbose=False):
    info = {}
    for ifd in ifds:
        img_type = ifd.get(img_type_tag_id, [None, ])[-1]
        # TODO: Shall we just return the relevant IDF?
        if(img_type == raw_image_type):
            info['img_width'] = ifd[img_width_tag_id][-1]
            info['img_height'] = ifd[img_height_tag_id][-1]
            info['img_bps'] = ifd[img_bps_tag_id][-1]
            info['img_compression'] = ifd[img_compression_tag_id][-1]
            info['img_array_type'] = ifd[img_array_type_tag_id][-1]
            info['img_offset'] = ifd[img_offset_tag_id][-1]
            info['img_orientation'] = ifd[img_orientation_tag_id][-1]
            info['img_spp'] = ifd[img_spp_tag_id][-1]
            info['img_rpstrip'] = ifd[img_rpstrip_tag_id][-1]
            info['img_bpstrip'] = ifd[img_bpstrip_tag_id][-1]
            info['img_planar_config'] = ifd[img_planar_config_tag_id][-1]
            info['img_cfa_repeat_size'] = ifd[img_cfa_repeat_size_tag_id][-1]
            info['img_cfa_pattern'] = ifd[img_cfa_pattern_tag_id][-1]
            info['img_sensing'] = ifd[img_sensing_tag_id][-1]
    if(not info):
        raise(Exception('Unable to find raw image info.'))
    if(verbose == 2):
        print(info)
    return(info)




def get_tag_value(ifds, tag_id, tag_name=None):
    """
    Given a list of IFDs, a IFD tag ID and optionally its corresponding tag name
    (as an extra check), return the tag value. Raise an exception if the tag is
    not found. This assumes that tag values CANNOT be None.
    """
    if(isinstance(ifds, dict)):
        # We just have a single IFD! Create a temp list with just this element.
        ifds = [ifds, ]
    
    # FIXME: use a random number/string instead of None.
    val = None
    for ifd in ifds:
        # Each IFD is a dictionary of the form:
        #  {tag_id: [val_abs_offset, tag, typ_fmt, len, val]}
        if(not ifd.has_key(tag_id) or
           (tag_name != None and ifd[tag_id][1] != tag_name)):
            continue
        
        val = ifd[tag_id][-1]
    if(val == None and tag_name == None):
        raise(Exception('Tag ID %d not found.' % (tag_id)))
    elif(val == None):
        raise(Exception('Tag ID %d/Tag Name %s not found.' \
                        % (tag_id, tag_name)))
    # Else: just return the value.
    return(val)


def unpack(fmt, buffer, big_endian=True):
    """
    Simple wrapper around struct.unpack(). The input `fmt` and `buffer` have the
    same meaning that in the struct.unpack case, with a few exceptions:
        fmt = '_str':       do not unpack `buffer` and just return it as string.
        fmt = '_rational'   unpack `buffer` as 2 4-byte integer (a / b).
    """
    if(big_endian):
        prefix = '>'
    else:
        prefix = '<'
    
    if(not fmt or fmt == '_str'):
        return(str(buffer))
    elif((fmt == '_urational' or fmt == '_rational') and len(buffer) % 8 == 0):
        if(fmt == '_urational'):
            fmt = prefix + 'L'
        else:
            fmt = prefix + 'l'
        
        i = 4
        n = len(buffer)
        i_max = n - 4
        res = []
        while(i <= i_max):
            a = int(''.join([str(x) for x in 
                             struct.unpack(fmt, buffer[i-4:i])]))
            b = int(''.join([str(x) for x in 
                             struct.unpack(fmt, buffer[i:i+4])]))
            res.append('%d / %d' % (a, b))
            
            i += 8
        return(res)
    elif(fmt == '_rational' and len(buffer) != 8):
        print(struct.unpack('>%dB' % (len(buffer)), buffer))
        raise(NotImplementedError('Rationals in sizes %d are not supported.' \
                                  % (len(buffer))))
    else:
        try:
            return(struct.unpack(prefix + fmt, buffer))
        except:
            raise(Exception('Failed to unpack "%s" as %s' % (buffer, fmt)))
    raise(NotImplementedError('Unsupported format/data type'))


def decode_pixel_data(data, raw_info, makernote_ifd, makernote_abs_offset,
                      verbose=False):
    """
    The linearization table is stored inside the Nikon Marker Note and is >1000
    bytes in length.
    
    The format is as follows: (start=initial_offset+base_offset)
        1   byte    version0
        1   byte    version1
    (if version0==0x49 and version1==0x58: data.seek(2110, os.SEEK_CUR))
        4   short   vert_preds[2 x 2]
        1   short   curve length (n)
        n   short   curve values
    (if version0==0x44 and version1==0x20: 
        data.seek(start+562, os.SEEK_SET)
        1   short   split value)
        
    """
    # Get the NEF compression flag.
    compression = makernote_ifd[NEF_COMPRESSION_TAG_ID][-1]
    
    # Get the image bits per sample (either 12 or 14 ususally).
    image_bps = raw_info['img_bps']
    
    # Get the abs offset to the linearization curve.
    [abs_offset, tag, typ_fmt, l, val] = makernote_ifd[NIKON_LINCURVE_TAG_ID]
    
    # Remember that val is already a list of l elements of type typ_fmt.
    data.seek(abs_offset, os.SEEK_SET)
    
    # See is we have to do any reading from data.
    if(typ_fmt == 'B'):
        v0, v1 = val[:2]
        data.seek(2, os.SEEK_CUR)       # keep track of where we are in data.
    else:
        v0, v1 = unpack('BB', data.read(2))
    
    # Choose the appropriate NIKON Huffman tree index.
    tree_index = 0
    if(v0 == 0x46):
        tree_index = 2
    if(image_bps == 14):
        tree_index += 3
    
    # For some combination of v0 and v1 we need to seek ahead a fixed ammount.
    if(v0 == 0x49 or v1 == 0x58):
        # FIXME: is it correct? Do we need to add 2 (see dcraw.c:1137)?
        data.seek(abs_offset + 2 + 2110, os.SEEK_SET)
    
    # Read the vertical predictor 2x2 matrix.
    # TODO: simple optimization: use the bytes in val rather than reading data.
    horiz_preds = [0, 0]
    vert_preds = [[0, 0], [0, 0]]
    (vert_preds[0][0],
     vert_preds[0][1],
     vert_preds[1][0],
     vert_preds[1][1]) = unpack('HHHH', data.read(8))
    
    max = 1 << image_bps & 0x7fff
    num_points = unpack('H', data.read(2))[0]
    if(num_points > 1):
        step = int(float(max) / (num_points - 1))
    values = unpack('H'*num_points, data.read(num_points * 2))
    
    # Decode the curve.
    curve = None
    split_row = -1
    if(v0 == 0x44 and v1 == 0x20 and step > 0):
        curve_max_len = 1 << tiff_bps & 0x7fff
        
        # The curve has length `curve_max_len` but we only have a `num_points`
        # points, so we need to interpolate.
        step = int(float(curve_max_len) / float(curve_size - 1))
        curve = [0, ] * curve_max_len
        for i in xrange(num_points):
            curve[i*step] = values[i]
        
        # Now interpolate between those values.
        step = float(step)
        for i in xrange(curve_max_len):
            curve[i] = int(float(curve[i-i%step] * (step-i%step) +
                                 curve[i-i%step+step] * (i%step)) / step)
        
        # Finally, get the 'split value'. This is the row where we need to
        # re-init the Huffman tree.
        data.seek(abs_offset + 562, os.SEEK_SET)
        split_row = unpack('H', data.read(2))
    elif(v0 != 0x46 and num_points <= 16385):
        # Simple case: curve = values. Also, no split row here.
        curve = values
        curve_max_len = num_points
    else:
        raise(Exception('Unsupported Nikon linearization curve.'))
    
    # Sometimes curve elements are repeated at the end. Get the number of 
    # distinct elements.
    while(curve[curve_max_len-2] == curve[curve_max_len-1]):
        curve_max_len -= 1
    
    # Now decode the pixel values. This is a bit of a mess, but not too bad.
    pixel_abs_offset = raw_info['img_offset']
    data.seek(pixel_abs_offset, os.SEEK_SET)
    
    # Get the image size.
    width = raw_info['img_width']
    height = raw_info['img_height']
    
    # Cast data into a string of bits of length width * height * 8
    byte_buffer = numpy.fromfile(data, dtype=numpy.uint8)
    bit_buffer = numpy.ascontiguousarray(numpy.unpackbits(byte_buffer), 
                                         dtype=numpy.uint8)
    
    # Decode the actual pixel differences/deltas.
    deltas = pixelutils.decode_pixel_deltas(width, 
                                            height, 
                                            tree_index, 
                                            bit_buffer, 
                                            split_row,
                                            NIKON_TREE)
    
    # Now turn all those deltas in pixel values. The only raw pixel value is 
    # the one at top, left for each color. Differences are done color by color.
    # pixels = compute_pixel_values(deltas, horiz_preds, vert_preds, curve)
    pixels = pixelutils.compute_pixel_values(deltas, horiz_preds, vert_preds, curve)
    
    if(verbose):
        import Image
        
        img = Image.fromarray(pixels, 'RGBA')
        img.show()
    
    # These are rescaled pixel values. To get the real pixel values we need to
    # multiply their value by the linearization curve.
    return(curve)


def decode_file(file_name, verbose=False):
    """
    Read `file_name` and pass its content to `decode_nef`. Return the decoded 
    image data.
    """
    # Read the NEF data.
    f = open(file_name, 'rb')
    output = decode_nef(f, verbose)
    f.close()
    return(output)


def decode_nef(data, verbose=False):
    """
    Decode the input NEF raw bytes `nef_data` and return the decoded byte 
    stream.
    """
    # Decode the metadata.
    ifds = decode_nef_header(data, verbose)
    
    # Now decode the thumbnail.
    
    # Now decode the pixel data.
    
    return('Not quite there yet.\n')


def decode_nef_header(data, verbose=False):
    """
    The NEF header is a TIFF header:
    
    2 bytes:    endianess. Usually "MM" (i.e. big-endian)
    2 bytes:    TIFF magic number 0x002a
    4 bytes:    TIFF offset
    n bytes:    the rest (meaning M IFDs, pixel data etc.)
    """
    # Make sure that the file is big-endian. If not, then we have a problem 
    # since NEFs are always supposed to be big-endian...
    if(data.read(2) != 'MM'):
        data.close()
        raise(Exception('File is little-endian. Are you sure it is a NEF?'))
    if(verbose == 2):
        print('The file is big-endian.')
    
    # Now get the version and the offset to the first directory. Version should
    # be 42.
    version = unpack('H', data.read(2))[0]
    offset = unpack('I', data.read(4))[0]
    if(version != 42):
        data.close()
        raise(Exception('File version != 42. Are you sure it is a NEF?'))
    if(verbose == 2):
        print('Version:                                         %d' % (version))
        print('Offet to first IFD:                              %d' % (offset))
    
    # Now decode each IFD (Image File Directory) iteratively. 
    ifds = decode_ifd(data, 
                      initial_offset=offset, 
                      tags=EXIF_TAGS, 
                      makernote_tag=EXIF_TAGS[MAKERNOTE_TAG_ID],
                      verbose=verbose)
    
    # Get the Makernote offset. If we do not have it, we are in trouble.
    makernote_abs_offset = get_tag_value(ifds, 
                                         tag_id=MAKERNOTE_TAG_ID, 
                                         tag_name=EXIF_TAGS[MAKERNOTE_TAG_ID])
    # Decode the Makernote.
    makernote_ifd = decode_makernote(data, 
                                     initial_offset=makernote_abs_offset, 
                                     verbose=verbose)
    
    # Get the RAW image bits per sample value, size etc.
    raw_info = get_raw_image_info(ifds, verbose=verbose)
    
    # Now decode the raw pixels.
    # TODO: put this somewhere else.
    raster = decode_pixel_data(data, 
                               raw_info, 
                               makernote_ifd, 
                               makernote_abs_offset,
                               verbose=verbose)
    
    return(ifds, makernote_ifd)


def decode_makernote(data, initial_offset, tags=NIKON_TAGS, verbose=False):
    """
    The Nikon Makernote has a format wich is somewhat similar to that of the
    .NEF file itself:
    
    6 bytes:    "Nikon" string
    2 bytes:    version (short)? Usually 0x0210
    2 bytes:    unknown (short)? Usually 0x0000
    2 bytes:    endianess. Usually "MM" (i.e. big-endian)
    2 bytes:    TIFF magic number 0x002a
    4 bytes:    TIFF offset
    n bytes:    IFD
    
    So, apart from the first 10 bytes, the structure is identical to the .NEF 
    file itself. This also means that the offsets specified as tag value (when
    the type_length * tag_length > 4 bytes) are *relative* to the beginning of
    this 'fake' TIFF (i.e. initial_offset + 10).
    """
    base_offset = initial_offset + 10
    data.seek(base_offset)
    
    # Make sure that the file is big-endian. If not, then we have a problem 
    # since NEFs are always supposed to be big-endian...
    if(data.read(2) != 'MM'):
        data.close()
        raise(Exception('File is little-endian. Are you sure it is a NEF?'))
    if(verbose == 2):
        print('The file is big-endian.')
    
    # Now get the version and the offset to the first directory. Version should
    # be 42.
    version = unpack('H', data.read(2))[0]
    offset = unpack('I', data.read(4))[0]  # needs to be relative to base_offset
                                           # but decode_ifd will do that.
    if(version != 42):
        data.close()
        raise(Exception('File version != 42. Are you sure it is a NEF?'))
    if(verbose == 2):
        print('Version:                                         %d' % (version))
        print('Offet to Makernote IFD:                          %d' % (offset))
    
    [makernote_ifd, ] = decode_ifd(data, 
                                   initial_offset=offset,
                                   tags=NIKON_TAGS,
                                   makernote_tag=None,
                                   base_offset=base_offset,
                                   verbose=verbose)
    return(makernote_ifd)


def decode_ifd(data, 
               initial_offset, 
               tags=EXIF_TAGS, 
               makernote_tag=EXIF_TAGS[MAKERNOTE_TAG_ID], 
               base_offset=0,           # It is != 0 only for Nikon Makernote.
               verbose=False):
    # IFDs have the format:
    #   2 bytes     number of tags/entries in the IFD.
    #   12 bytes    for each IFD entry (times the number of tags).
    #   4 bytes     offset to the next IFD.
    # 
    # IFD entries have the format:
    #   2 bytes     tag id.
    #   2 bytes     tag type.
    #   4 bytes     tag value length.
    #   4 bytes     either tag value of offset to tag value (if length > 4).
    # 
    # Tag types:
    #   1   byte
    #   2   string
    #   3   short
    #   4   long
    #   5   rational
    #   6   signed byte
    #   7   undefined
    #   8   signed short
    #   9   signed long
    #   10  signed rational
    #   11  float
    #   12  double
    dirs = []
    
    # We usually have 4 child IFDs: EXIF, Preview, Raw and Makernote.
    relative_offsets = [initial_offset, ]
    
    # From here below all offsets are relative to base_offset. Of course 
    # base_offset is 0 for all IFDs *but* the Nikon Makernote.
    while(relative_offsets):
        relative_offset = relative_offsets.pop()
        abs_offset = relative_offset + base_offset
        
        if(verbose == 2):
            print('Abs Offset:                                  %d' \
                  %(base_offset + relative_offset))
        if(not relative_offset):
            continue
        
        # Start parsing a new IFD.
        dir = {}
        data.seek(abs_offset, os.SEEK_SET)
        
        # Parse the directory content.
        n = unpack('H', data.read(2))[0]
        if(verbose == 2):
            print('N:                                           %d' %(n))

        while(n):
            if(verbose == 2):
                print('We are at %d' % (data.tell()))
            
            tag_id = unpack('H', data.read(2))[0]
            tag = tags.get(tag_id, 'Unknown Tag')
            typ_id = unpack('H', data.read(2))[0]
            typ_fmt, typ_size = TYPES.get(typ_id, DEF_TYPE)
            len = unpack('I', data.read(4))[0]
            val_abs_offset = data.tell()
            
            unpack_fmt = typ_fmt
            if(typ_fmt != None and not typ_fmt[0] == '_'):
                unpack_fmt = len * typ_fmt
            
            unpack_bytes = []
            val_size = typ_size * len
            if(val_size > 4):
                new_relative_offset = unpack('I', data.read(4))[0]
                new_abs_offset = new_relative_offset + base_offset
                val_abs_offset = new_abs_offset
                
                # Special handling for the Marker Note: we do not store the 
                # value, but rather just the offset as value.
                if(makernote_tag and tag == makernote_tag):
                    dir[tag_id] = [new_abs_offset, tag, typ_fmt, len, 
                                   new_abs_offset]
                    # Decrement n and go to the next entry.
                    n -= 1
                    continue
                
                # Go there...
                here = data.tell()
                data.seek(new_abs_offset, os.SEEK_SET)
                if(verbose == 2):
                    print('Jump to %d' % (new_abs_offset))
                
                # Read the data to decode.
                unpack_bytes = data.read(val_size)
                
                # ...and back.
                data.seek(here, os.SEEK_SET)
                if(verbose == 2):
                    print('Jump back')
            else:
                # Read the data to decode (4 bytes in this case).
                unpack_bytes = data.read(4)
                
                # Do we need padding (only if the data size would be < 4 bytes)?
                if(val_size < 4 and 
                   typ_fmt != None and 
                   not typ_fmt[0] == '_'):
                    pad = 'x' * (4 - val_size)
                    unpack_fmt += pad
            
            # Decode the tag value. This is always a tuple/list.
            val = unpack(unpack_fmt, unpack_bytes)
            
            # Did we get one of the child offsets?
            if(tag_id in CHILD_IFD_TAGS):
                relative_offsets += val
            
            # Make sure that if len == 1, we only store the value, not a 
            # singleton.
            if(len == 1):
                val = val[0]
            
            # Add the tag to the current directory.
            dir[tag_id] = [val_abs_offset, tag, typ_fmt, len, val]
            
            # Decrement the number of entries.
            n -= 1
            if(verbose):
                print(VERBOSE_TAG_FMT % (tag_id, tag, typ_fmt, len, val))
        
        # Add the current directory to the list of directories.
        dirs.append(dir)
        
        # Get a new offset and start over.
        new_relative_offset = unpack('I', data.read(4))[0]
        if(new_relative_offset != 0):
            relative_offsets.append(new_offset)
    return(dirs)
    
    








if(__name__ == '__main__'):
    import optparse
    import sys
    
    
    # Constants
    USAGE = """NEF Decoder

Decode a NEF file and turn it into a TIFF or JPEG, depending on user-specified 
output file extension. If no output file is specified, the input NEF is 
converted to TIFF and simply printed to STDOUT.


Usage
    nef_decoder.py [options] <NEF file name>


Options
    -v          verbose (default not vcerbose)
    -o FILE     write the output to FILE. Output type is inferred from file 
                extension.


Example
    nef_decoder.py -o bar.jpg foo.nef
""" 
    # Get user input (tracks file) and make sure that it exists.
    parser = optparse.OptionParser(USAGE)
    parser.add_option('-o', '--output',
                      dest='output_name',
                      type='str',
                      default=None,
                      help='name of the output file.')
    # Verbose flag
    parser.add_option('-v',
                      action='store_true',
                      dest='verbose',
                      default=False)
    # Profiler flag
    parser.add_option('-p', '--profile',
                      action='store_true',
                      dest='profile',
                      default=False)

    
    # Get the command line options and also whatever is passed on STDIN.
    (options, args) = parser.parse_args()
    
    # We have to have an input file name!
    if(not args or not os.path.exists(args[0])):
        parser.error('Please specify an input file.')
    
    # Convert the input file.
    if(options.profile):
        import cProfile
        
        print('Profiler on')
        cmd = 'output_img = decode_file(args[0], verbose=options.verbose)'
        cProfile.runctx(cmd, globals(), locals(), filename="nef_decoder.prof" )
    else:
        print('Profiler off')
        output_img = decode_file(args[0], verbose=options.verbose)
    
    # If we do not have an output file name, just write to stdout.
    if(not options.output_name):
        sys.stdout.write(output_img)
        sys.stdout.flush()
    else:
        f = open(options.output_name, 'wb')
        f.write(output_img)
        f.close()
    sys.exit(0)

