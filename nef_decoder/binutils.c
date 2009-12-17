/*
                        binary <-> decimal utilities

Credits: c_bin2dec dilip.mathews: http://www.daniweb.com/code/snippet216372.html
*/
#include <Python.h>



const char* inttobin(int);
int bintoint(const char *, int);


const char* inttobin(int num) {
    static char bin[32 + 1] = { 0 };
    int i = 0;
    
    memset(bin, '0', 32);
    while (num > 0) {
        bin[32 - 1 - i++] = '0' + num % 2;
        num >>= 1;
    }
    return bin;
}


int bintoint(const char *bin, int len) {
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



PyDoc_STRVAR(doc_int2bin, 
        "int-> (ascii). Encode a positive integer into a string of 1s and 0s.");
static PyObject * int2bin(PyObject *self, PyObject *args) {
    int n;
    const int count;

    
    // Parse input arguments.
    if (!PyArg_ParseTuple(args, "ii", &n, &count))
        return(NULL);
    
    // If we get a negative integer, rise an exception. Otherwise convert the
    // integer.
    // FIXME: handle the case n < 0
    if(n < 0) {
        PyErr_SetString(PyExc_TypeError, 
                        "negative integers are not supported.\n");
        return(NULL);
    }
    return(Py_BuildValue("s", inttobin(n)));
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



static PyMethodDef binutils_methods[] = {
    {"int2bin",  int2bin, METH_VARARGS, doc_int2bin},
    {"bin2int",  (PyCFunction)bin2int, METH_VARARGS|METH_KEYWORDS, doc_bin2int},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initbinutils(void)
{
    (void) Py_InitModule("binutils", binutils_methods);
}






