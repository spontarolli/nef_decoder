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
import cStringIO
import os
import struct

from huffman_tables import huf as NIKON_TREE

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
NEF_COMPRESSION_TAG_ID = 147
NEF_BPS_TAG_ID = 258
NEF_WIDTH_TAG_ID = 256
NEF_HEIGHT_TAG_ID = 257


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


def unpack_linearization_table(data, tag_id, typ_fmt, len, val, compression,
                               image_bps, initial_offset, base_offset, 
                               verbose=False):
    """
    The linearization table is stored inside the Nikon Marker Note and is >1000
    bytes in length.
    
    The format is as follows: (start=initial_offset+base_offset)
        1   byte    version0
        1   byte    version1
    (if version0==0x49 and version1==0x58: data.seek(2110, os.SEEK_CUR))
        4   short   vpred[2, 2]
        1   short   curve length (n)
        n   short   curve values
    (if version0==0x44 and version1==0x20: 
        data.seek(start+562, os.SEEK_SET)
        1   short   split value)
        
    """
    # Remember that val is already a list of len elements of type typ_fmt.
    # Make the offset absolute and go there.
    abs_offset = initial_offset + base_offset
    data.seek(abs_offset, os.SEEK_SET)
    
    # See is we have to do any reading from data.
    if(typ_fmt == 'B'):
        v0, v1 = val[:2]
        data.seek(2, os.SEEK_CUR)       # keep track of where we are in data.
    else:
        v0, v1 = unpack('BB', data.read(2))
    
    # Choose the appropriate NIKON Huffman tree.
    tree_index = 0
    if(v0 == 0x46):
        tree_index = 2
    if(image_bps == 14):
        tree_index += 3
    
    
    # For some combination of v0 and v1 we need to seek ahead a fixed ammount.
    if(v0 == 0x49 or v1 == 0x58):
        data.seek(abs_offset + 2 + 2110, os.SEEK_SET)
    
    # Read the vertical predictor 2x2 matrix.
    # TODO: simple optimization: use the bytes in val rather than reading data.
    vert_preds = unpack('HHHH', data.read(8))
    num_points = unpack('H', data.read(2))[0]
    values = unpack('H'*num_points, data.read(num_points * 2))
    
    # Decode the curve.
    curve = None
    split_row = None
    if(v0 == 0x44 and v1 == 0x20 and step > 0):
        curve_max_len = 2 ** image_bps
        
        # The curve has length `curve_max_len` but we only have a `num_points`
        # points, so we need to interpolate.
        step = int(float(curve_max_len) / float(curve_size - 1))
        curve = [0, ] * curve_max_len
        for i in range(num_points):
            curve[i*step] = values[i]
        
        # Now interpolate between those values.
        step = float(step)
        for i in range(curve_max_len):
            curve[i] = int(float(curve[i-i%step] * (step-i%step) +
                                 curve[i-i%step+step] * (i%step)) / step)
        
        # Finally, get the 'split value'. This is the row where we need to
        # re-init the Huffman tree.
        data.seek(abs_offset + 562, os.SEEK_SET)
        split_row = unpack('H', data.read(2))
    elif(v0 != 0x46 and num_points <= 16385):
        # Simple case: curve = values. Also, no split row here.
        curve = values
    else:
        raise(Exception('Unsupported Nikon linearization curve.'))
    
    # Sometimes curve elements are repeated at the end. Get the number of 
    # distinct elements.
    while(curve[num_points-2] == curve[num_points-1]):
        num_points -= 1
    
    return(curve)


def decode_file(file_name, verbose=False):
    """
    Read `file_name` and pass its content to `decode_nef`. Return the decoded 
    image data.
    """
    # Read the NEF data.
    f = open(file_name, 'rb')
    nef_data = cStringIO.StringIO(f.read())
    f.close()
    
    # Return the decoded output.
    return(decode_nef(nef_data, verbose))


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
    return(ifds)


def decode_makernote(data, initial_offset, tags=NIKON_TAGS, image_bps=12,
                     verbose=False):
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
    
    # Fetch the data compression value.
    try:
        compr_flag = makernote_ifd[NEF_COMPRESSION_TAG_ID][4]
    except:
        raise(Exception('This Nikon Makernote doe not have a compression flag'))
    
    # Now decode the linearization curve (NIKON_LINCURVE_TAG_ID).
    # Each IFD is a dictionary of the form:
    #  {tag_id: [val_abs_offset, tag, typ_fmt, len, val]}
    # Where abs_offset is the absolute file offset of the corresponding IFD 
    # entry.
    # Update the entry value.
    entry = makernote_ifd.get(NIKON_LINCURVE_TAG_ID, None)
    if(not entry):
        raise(Exception('This Nikon Makernote does not have a lin curve!'))
    
    
    rel_offset = entry[0] - base_offset     # make the offset relative.
    entry[4] = unpack_linearization_table(data,
                                          tag_id=NIKON_LINCURVE_TAG_ID,
                                          typ_fmt=entry[2],
                                          len=entry[3],
                                          val=entry[4],
                                          compression=compr_flag,
                                          image_bps=image_bps,
                                          initial_offset=rel_offset,
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
    makernote_abs_offset = None
    
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
                
                # Special handling for the Marker Note.
                if(makernote_tag and tag == makernote_tag):
                    makernote_abs_offset = new_abs_offset
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
    
    
    # FIXME: I do not think what follows is quite good style.
    # Now parse the Makernote, if any. But before that get the image BPS out
    # of the other IFDs,
    if(makernote_abs_offset != None):
        bps = None
        for ifd in dirs:
            if(not ifd.has_key(NEF_BPS_TAG_ID)):
                continue
            
            if(ifd[NEF_WIDTH_TAG_ID] > 1000):       # Not a preview.
                bps = ifd[NEF_BPS_TAG_ID][-1]
        if(bps == None):
            raise(Exception('Unable to find image bits per sample value.'))
        
        dirs.append(decode_makernote(data, 
                                     initial_offset=makernote_abs_offset, 
                                     image_bps=bps,
                                     verbose=verbose))
    return(dirs)
    
    
















if(__name__ == '__main__'):
    import optparse
    import sys
    
    import cProfile
    

    
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

    
    # Get the command line options and also whatever is passed on STDIN.
    (options, args) = parser.parse_args()
    
    # We have to have an input file name!
    if(not args or not os.path.exists(args[0])):
        parser.error('Please specify an input file.')
    
    # Convert the input file.
    # output_img = decode_file(args[0], verbose=options.verbose)
    cmd = 'output_img = decode_file(args[0], verbose=options.verbose)'
    cProfile.runctx(cmd, globals(), locals(), filename="nef_decoder.prof" )
    
    # If we do not have an output file name, just write to stdout.
    if(not options.output_name):
        sys.stdout.write(output_img)
        sys.stdout.flush()
    else:
        f = open(options.output_name, 'wb')
        f.write(output_img)
        f.close()
    sys.exit(0)