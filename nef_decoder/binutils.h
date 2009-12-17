#include <Python.h>


// Prototypes.
const char* positive_inttobin32(int);
const char* negative_inttobin32(int);
const char* inttobin32(int);
const char* positive_inttobin8(int);
const char* negative_inttobin8(int);
const char* inttobin8(int);
void positive_inttobin_var(int, int, char*);
void negative_inttobin_var(int, int, char*);
void inttobin_var(int, int, char*);
int bintoint(const char*, int);
void strtobin(const char*, const int, char*);
static PyObject * int2bin(PyObject*, PyObject*);
static PyObject * data2bin(PyObject*, PyObject*);
static PyObject * bin2int(PyObject*, PyObject*, PyObject*);
PyMODINIT_FUNC initbinutils(void);

