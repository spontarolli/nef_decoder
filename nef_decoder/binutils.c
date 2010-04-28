/*
                        binary <-> decimal utilities

Credits: c_bin2dec dilip.mathews: http://www.daniweb.com/code/snippet216372.html
*/
#include "binutils.h"



const char* positive_inttobin32(int num) {
    // Convert `num` into its binary representation.
    static char bin[32 + 1] = { 0 };
    int i = 0;
    
    // Make sure bin is terminated.
    bin[32] = '\0';
    
    memset(bin, '0', 32);
    while (num > 0) {
        bin[32 - 1 - i++] = '0' + num % 2;
        num >>= 1;
    }
    return bin;
}



const char* negative_inttobin32(int num) {
    // Convert `num` into its binary representation.
    static char bin[32 + 1] = { 0 };
    int i = 0;
    
    // Make sure bin is terminated.
    bin[32] = '\0';
    
    memset(bin, '1', 32);
    
    // flip the sign of num to turn it into a positive integer and subtract one.
    // the rest is identical to positive_inttobin32 only with 0s and 1s flipped.
    num = (-num) - 1;
    while (num > 0) {
        bin[32 - 1 - i++] = '1' - (num % 2);
        num >>= 1;
    }
    return bin;
}



const char* inttobin32(int num) {
    if(num == 0)
        return("00000000000000000000000000000000\0");
    else if(num > 0)
        return(positive_inttobin32(num));
    else
        return(negative_inttobin32(num));
}



const char* positive_inttobin8(int num) {
    // Convert `num` into its binary representation.
    static char bin[8 + 1] = { 0 };
    int i = 0;
    
    // Make sure bin is terminated.
    bin[8] = '\0';
    
    memset(bin, '0', 8);
    while (num > 0) {
        bin[8 - 1 - i++] = '0' + num % 2;
        num >>= 1;
    }
    return bin;
}



const char* negative_inttobin8(int num) {
    // Convert `num` into its binary representation.
    static char bin[8 + 1] = { 0 };
    int i = 0;
    
    // Make sure bin is terminated.
    bin[8] = '\0';
    
    memset(bin, '1', 8);
    
    // flip the sign of num to turn it into a positive integer and subtract one.
    // the rest is identical to positive_inttobin8 only with 0s and 1s flipped.
    num = (-num) - 1;
    while (num > 0) {
        bin[8 - 1 - i++] = '1' - (num % 2);
        num >>= 1;
    }
    return bin;
}



const char* inttobin8(int num) {
    if(num == 0)
        return("00000000\0");
    else if(num > 0)
        return(positive_inttobin8(num));
    else
        return(negative_inttobin8(num));
}



void positive_inttobin_var(int num, int count, char* bin) {
    // Convert `num` into its binary representation.
    // bin is already allocated and of length count.
    int i = 0;
    
    // Make sure that bin is null terminated.
    bin[count] = '\0';
    
    memset(bin, '0', count);
    while (num > 0) {
        bin[count - 1 - i++] = '0' + num % 2;
        num >>= 1;
    }
    return;
}



void negative_inttobin_var(int num, int count, char* bin) {
    // Convert `num` into its binary representation.
    // bin is already allocated and of length count.
    int i = 0;
    
    // Make sure that bin is null terminated.
    bin[count] = '\0';
    
    memset(bin, '1', count);
    
    // flip the sign of num to turn it into a positive integer and subtract one.
    // the rest is identical to positive_inttobin32 only with 0s and 1s flipped.
    num = (-num) -1;
    while (num > 0) {
        bin[count - 1 - i++] = '1' - num % 2;
        num >>= 1;
    }
    return;
}



void inttobin_var(int num, int count, char* bin) {
    // Convert `num` into its binary representation.
    // bin is already allocated and of length count.
    if(num >= 0)
        return(positive_inttobin_var(num, count, bin));
    return(negative_inttobin_var(num, count, bin));
}



int bintoint(const char *bin, int len) {
    // Convert the binary string `bin` of length `len` into an integer.
    int  b , k, n;
    int  sum = 0; 
 
    len -= 1;
    for(k = 0; k <= len; k++) {
        b = 1;
        n = (bin[k] - '0'); // char to numeric value
        b = b<<(len-k);
        // sum it up
        sum = sum + n * b;
    }
    return(sum);
}



void strtobin(const char* data, const int len, char* bin) {
    // Convert the binary data `data` (coming from a file, presumably) into a 
    // string of 1s and 0s. 8 bits per `data` character.
    // We assume that bin is already allocated and is of size len*8+1
    long i;
    long j;
    char temp[8];
    
        
    // Make sure bin is nicely terminated.
    bin[len*8] = '\0';
    
    for(j=i=0; i<len; i++) {
        inttobin_var((unsigned)data[i], 8, temp);
        
        bin[j++] = temp[0];
        bin[j++] = temp[1];
        bin[j++] = temp[2];
        bin[j++] = temp[3];
        bin[j++] = temp[4];
        bin[j++] = temp[5];
        bin[j++] = temp[6];
        bin[j++] = temp[7];
    }
    return;
}



PyDoc_STRVAR(doc_int2bin, 
        "int-> (ascii). Encode an integer into a string of 1s and 0s.");
static PyObject * int2bin(PyObject *self, PyObject *args) {
    int n;
    const int count;
    char* bin=NULL;

    
    // Parse input arguments.
    if (!PyArg_ParseTuple(args, "ii", &n, &count))
        return(NULL);
    
    // Use specialized functions if possible.
    switch(count) {
        case 32:
            return(Py_BuildValue("s", inttobin32(n)));
        case 8:
            return(Py_BuildValue("s", inttobin8(n)));
        default:
            // Allocate memory for the return string.
            bin = (char*)malloc((count+1) * sizeof(char));
            if(bin == NULL) {
                PyErr_SetString(PyExc_MemoryError, "Memory allocation error.\n");
                return(NULL);
            }
            inttobin_var(n, count, bin);
            return(Py_BuildValue("s", bin));
    }
}



PyDoc_STRVAR(doc_data2bin, 
        "data-> (ascii). Encode a stream of bytes into a string of 1s and 0s.");
static PyObject * data2bin(PyObject *self, PyObject *args) {
    char* data;
    const int len;
    char* bin=NULL;
    
    
    // Parse input arguments.
    if (!PyArg_ParseTuple(args, "s#", &data, &len))
        return(NULL);
    
    if(len <= 0)
        Py_RETURN_NONE;
    
    // Allocate memory for the return string.
    bin = (char*)malloc((len*8 + 1) * sizeof(char));
    if(bin == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Memory allocation error.\n");
        return(NULL);
    }
    
    strtobin(data, len, bin);
    return(Py_BuildValue("s", bin));
}



PyDoc_STRVAR(doc_bin2int, 
        "(ascii) -> int. Decode a string of 1s and 0s into an integer.");
static PyObject * bin2int(PyObject *self, PyObject *args, PyObject *keywds) {
    const char* s;
    PyObject* unsafe=Py_False;
    const int len;
    int i;

    
    // These are the input keywords:
    static char *kwlist[] = {"bin_str", "unsafe", NULL};
    
    // Parse the input string.
    if (!PyArg_ParseTupleAndKeywords(args, 
                                     keywds, 
                                     "s#|O", 
                                     kwlist, 
                                     &s, 
                                     &len, 
                                     &unsafe))
        return(NULL);
    
    // Make sure that we have a string of size > 0, otherwise return None.
    if(len <= 0)
        Py_RETURN_NONE;
    
    // Simple sanity check: make sure that s contains only 0s and 1s.
    if(PyObject_Not(unsafe) != 0) {
        for(i=0; i<len; i++) {
            if(s[i] != '0' && s[i] != '1') {
                PyErr_SetString(PyExc_TypeError, "binary strings only have 1 and 0\n");
                return(NULL);
            }
        }
    }
    
    // Convert the binary string into an integer and return it as Python int.
    return(Py_BuildValue("i", bintoint(s, len)));
}



PyDoc_STRVAR(doc_boxit_fast, 
        "int, int, int-> int. Make sure that the input integer is between the two boundaries. No safety checks.");
static PyObject * boxit_fast(PyObject *self, PyObject *args) {
    int x;
    const int low, high;

    
    // Parse input arguments.
    if (!PyArg_ParseTuple(args, "iii", &x, &low, &high))
        return(NULL);
    
    // Make sure that x is between low and high. If not, return the closest 
    // boundary. For performance sake, we do not do any safety check.
    if(x < low)
        return(Py_BuildValue("i", low));
    else if(x > high)
        return(Py_BuildValue("i", high));
    return(Py_BuildValue("i", x));
}



PyDoc_STRVAR(doc_boxit, 
        "int, int, int-> int. Make sure that the input integer is between the two boundaries.");
static PyObject * boxit(PyObject *self, PyObject *args) {
    int x;
    const int low, high;
    int l, h;

    
    // Parse input arguments.
    if (!PyArg_ParseTuple(args, "iii", &x, &low, &high))
        return(NULL);
    
    // Make sure that low is < high.
    if(low == high) {
        return(Py_BuildValue("i", low));
    } else if(low < high) {
        l = low;
        h = high;
    } else {
        l = high;
        h = low;
    }
    
    // Make sure that x is between low and high. If not, return the closest 
    // boundary. For performance sake, we do not do any safety check.
    if(x < l)
        return(Py_BuildValue("i", l));
    else if(x > h)
        return(Py_BuildValue("i", h));
    return(Py_BuildValue("i", x));
}



static PyMethodDef binutils_methods[] = {
    {"int2bin",  int2bin, METH_VARARGS, doc_int2bin},
    {"data2bin",  data2bin, METH_VARARGS, doc_data2bin},
    {"bin2int",  (PyCFunction)bin2int, METH_VARARGS|METH_KEYWORDS, doc_bin2int},
    {"boxit_fast",  boxit_fast, METH_VARARGS, doc_boxit_fast},
    {"boxit",  boxit, METH_VARARGS, doc_boxit},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};



PyMODINIT_FUNC initbinutils(void)
{
    (void) Py_InitModule("binutils", binutils_methods);
}






