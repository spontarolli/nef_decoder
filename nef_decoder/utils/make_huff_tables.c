/*
Extracted form dcraw.c by Dave Coffin.
dcraw.c Copyright 1997-2009 by Dave Coffin, dcoffin a cybercom o net

Compile with:
    gcc -o make_huff_tables make_huff_tables.c
*/
#include <stdio.h>
#include <stdlib.h>




void make_decoder_ref (const unsigned char **source)
{
  int max, len, h, i, j;
  const unsigned char *count;
  unsigned short *huff;
  unsigned short val=0;

  count = (*source += 16) - 17;
  for (max=16; max && !count[max]; max--);
  huff = (unsigned short *) calloc (1 + (1 << max), sizeof *huff);
  if(! huff) {
    printf("Error creating the tree!\n");
    return;
  }
  huff[0] = max;
  
  printf("huf = [%d,", max);
  
  for (h=len=1; len <= max; len++)
    for (i=0; i < count[len]; i++, ++*source)
      for (j=0; j < 1 << (max-len); j++)
	    if (h <= 1 << max) {
	      val = len << 8 | **source;
	      printf("%d,", val);
	      huff[h++] = val;
	    }
  printf("]\n");
  return;
}


void make_decoder (const unsigned char *source)
{
  return make_decoder_ref (&source);
}


int main(void) {
  const unsigned char tree[][32] = {
    { 0,1,5,1,1,1,1,1,1,2,0,0,0,0,0,0,	/* 12-bit lossy */
      5,4,3,6,2,7,1,0,8,9,11,10,12 },
    { 0,1,5,1,1,1,1,1,1,2,0,0,0,0,0,0,	/* 12-bit lossy after split */
      0x39,0x5a,0x38,0x27,0x16,5,4,3,2,1,0,11,12,12 },
    { 0,1,4,2,3,1,2,0,0,0,0,0,0,0,0,0,  /* 12-bit lossless */
      5,4,6,3,7,2,8,1,9,0,10,11,12 },
    { 0,1,4,3,1,1,1,1,1,2,0,0,0,0,0,0,	/* 14-bit lossy */
      5,6,4,7,8,3,9,2,1,0,10,11,12,13,14 },
    { 0,1,5,1,1,1,1,1,1,1,2,0,0,0,0,0,	/* 14-bit lossy after split */
      8,0x5c,0x4b,0x3a,0x29,7,6,5,4,3,2,1,0,13,14 },
    { 0,1,4,2,2,3,1,2,0,0,0,0,0,0,0,0,	/* 14-bit lossless */
      7,6,8,5,9,4,10,3,11,12,2,0,1,13,14 } };
  
  int tree_idx;
    
    
  for(tree_idx=0; tree_idx<6; tree_idx++) {
    make_decoder(tree[tree_idx]);
  }
  return 0;
}
