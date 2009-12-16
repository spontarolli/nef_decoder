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
        if ((n > 1) || (n < 0)) {
            puts("\n\n ERROR! BINARY has only 1 and 0!\n");
            return (0);
        }
        b = b<<(len-k);
        // sum it up
        sum = sum + n * b;
    }
    return(sum);
}




static PyObject * int2bin(PyObject *self, PyObject *args) {
    int n;
    const int count;

    
    if (!PyArg_ParseTuple(args, "ii", &n, &count))
        return(NULL);
    
    if(n < 0)
        return(NULL);
    else if(n == 0)
        return(Py_BuildValue("s", "0"));
    
    return(Py_BuildValue("s", inttobin(n)));
}


static PyObject * bin2int(PyObject *self, PyObject *args) {
    const char *s;
    const int len;

    
    if (!PyArg_ParseTuple(args, "s#", &s, &len))
        return(NULL);
    
    if(len <= 0)
        return(NULL);
    
    return(Py_BuildValue("i", bintoint(s, len)));
}



static PyMethodDef binutils_methods[] = {
    {"int2bin",  int2bin, METH_VARARGS, "Convert a positive interger into its binary representation."},
    {"bin2int",  bin2int, METH_VARARGS, "Convert a binary string into an integer."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initbinutils(void)
{
    (void) Py_InitModule("binutils", binutils_methods);
}






