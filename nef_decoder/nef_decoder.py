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
                  
                  (37500, 'Marker Note'),
                  
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
NIKON_TAGS = dict([(1,    'Marker Note Version'),
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
                   (17,   'Nikon Preview'),
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

# Type ID: (Data type format, size in bytes)
# Type formats that start with '_' are custom.
TYPES = {1:   ('B',         1),
         2:   ('_str',      1),                           # Simple string.
         3:   ('H',         2),
         4:   ('L',         4),
         5:   ('_urational',8),                           # rational?
         6:   ('b',         1),
         7:   ('B',         1),                           # undefined.
         8:   ('h',         2),
         9:   ('l',         4),
         10:  ('_rational', 8),                           # signed rational?
         11:  ('f',         4),
         12:  ('d',         8)}

DEF_TYPE =    ('B',    1)
CHILD_IFD_TAGS = (330, 34665)





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
    elif((fmt == '_urational' or fmt == '_rational') and len(buffer) % 4 == 0):
        if(fmt == '_urational'):
            fmt = prefix + 'L'
        else:
            fmt = prefix + 'l'
        
        i = 4
        n = len(buffer)
        i_max = n - 4
        res = []
        while(i <= i_max):
            a = float(''.join([str(x) for x in 
                               struct.unpack(fmt, buffer[i-4:i])]))
            b = float(''.join([str(x) for x in 
                               struct.unpack(fmt, buffer[i:i+4])]))
            res.append(a / b)
            
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
    # Make sure that the file is big-endian. If not, then we have a problem 
    # since NEFs are always supposed to be big-endian...
    if(data.read(2) != 'MM'):
        data.close()
        raise(Exception('File is little-endian. Are you sure it is a NEF?'))
    if(verbose):
        print('The file is big-endian.')
    
    # Now get the version and the offset to the first directory. Version should
    # be 42.
    version = unpack('H', data.read(2))[0]
    offset = unpack('I', data.read(4))[0]
    if(version != 42):
        data.close()
        raise(Exception('File version != 42. Are you sure it is a NEF?'))
    if(verbose):
        print('Version:                                         %d' % (version))
        print('Offet to first IFD:                              %d' % (offset))
    
    # Now decode each IFD (Image File Directory) iteratively.
    ifds = decode_ifd(data, initial_offset=offset, verbose=verbose)
    
    # Now decode the thumbnail.
    
    # Now decode the pixel data.
    
    return('')


def decode_ifd(data, 
               initial_offset, 
               exif_tags=EXIF_TAGS,
               nikon_tags=NIKON_TAGS,
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
    
    # Seek to offset (relative to the beginning of the data). An offset of 0 
    # means that we are done.
    dirs = []
    
    # We usually have 3 child IFDs: EXIF, Preview, Raw.
    offsets = [initial_offset, ]
    
    in_marker_note = False
    while(offsets):
        offset = offsets.pop()
        if(verbose):
            print('Offset:                                      %d' %(offset))
        if(not offset):
            continue
        
        # Start parsing a new IFD.
        dir = []
        data.seek(offset, os.SEEK_SET)
        
        # Reset the Marker Note flag and decide which tags we are going to use.
        tags = exif_tags
        if(in_marker_note):
            tags = nikon_tags
            in_marker_note = False
        
        # Parse the directory content.
        n = unpack('H', data.read(2))[0]
        if(verbose):
            print('N:                                           %d' %(n))

        while(n):
            if(verbose):
                print('We are at %d' % (data.tell()))
            
            tag_id = unpack('H', data.read(2))[0]
            tag = tags.get(tag_id, 'Unknown Tag')
            typ_fmt, typ_size = TYPES.get(unpack('H', data.read(2))[0], 
                                          DEF_TYPE)
            len = unpack('I', data.read(4))[0]
            
            unpack_fmt = typ_fmt
            if(typ_fmt != None and not typ_fmt[0] == '_'):
                unpack_fmt = len * typ_fmt
            
            unpack_bytes = []
            val_size = typ_size * len
            if(val_size > 4):
                new_offset = unpack('I', data.read(4))[0]
                
                # Special handling for the Marker Note.
                if(tag == 'Marker Note'):
                    offsets.append(new_offset + 18)
                    in_marker_note = True
                    n -= 1
                    continue
                
                # Go there...
                here = data.tell()
                data.seek(new_offset, os.SEEK_SET)
                if(verbose):
                    print('Jump to %d' % (new_offset))
                
                unpack_bytes = data.read(val_size)
                
                # ...and back.
                data.seek(here, os.SEEK_SET)
                if(verbose):
                    print('Jump back')
            else:
                unpack_bytes = data.read(4)
                if(val_size < 4 and 
                   typ_fmt != None and 
                   not typ_fmt[0] == '_'):
                    pad = 'x' * (4 - val_size)
                    unpack_fmt += pad
            
            # Decode the tag value.
            val = unpack(unpack_fmt, unpack_bytes)
            
            # Did we get one of the child offsets?
            if(tag_id in CHILD_IFD_TAGS):
                offsets += val
            
            # Add the tag to the current directory.
            dir.append((tag, tag_id, typ_fmt, len, val))
            
            # Decrement the number of entries.
            n -= 1
            if(verbose):
                print('Tag:                                     %s' %(tag))
                print('Tag ID (dec):                            %d' %(tag_id))
                print('Tag ID (hex):                            0x%04x' %(tag_id))
                print('Type:                                    %s' %(typ_fmt))
                print('Length:                                  %d' %(len))
                print('Value:                                   %s' %(str(val)[:20]))
        
        # Add the current directory to the list of directories.
        dirs.append(dir)
        
        # Get a new offset and start over.
        new_offset = unpack('I', data.read(4))[0]
        if(new_offset != 0):
            offsets.append(new_offset)
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