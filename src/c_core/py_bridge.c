#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// Simple function to call Python and get result
char* call_python_function(const char *module_name, 
                          const char *function_name,
                          const char *args_json) {
    Py_Initialize();
    
    // Add current directory to Python path
    PyRun_SimpleString("import sys\n"
                       "sys.path.insert(0, '.')\n");
    
    char *result = NULL;
    
    // Import module
    PyObject *pModule = PyImport_ImportModule(module_name);
    if (pModule != NULL) {
        // Get function
        PyObject *pFunc = PyObject_GetAttrString(pModule, function_name);
        if (pFunc && PyCallable_Check(pFunc)) {
            // Parse JSON args
            PyObject *pArgs = NULL;
            if (args_json) {
                PyObject *json_module = PyImport_ImportModule("json");
                PyObject *loads_func = PyObject_GetAttrString(json_module, "loads");
                pArgs = PyObject_CallFunction(loads_func, "s", args_json);
                Py_XDECREF(loads_func);
                Py_XDECREF(json_module);
            } else {
                pArgs = PyTuple_New(0);
            }
            
            // Call function
            PyObject *pValue = PyObject_CallObject(pFunc, pArgs);
            Py_XDECREF(pArgs);
            
            if (pValue != NULL) {
                // Convert result to string
                PyObject *str_obj = PyObject_Str(pValue);
                const char *c_str = PyUnicode_AsUTF8(str_obj);
                if (c_str) {
                    result = strdup(c_str);
                }
                Py_XDECREF(str_obj);
                Py_DECREF(pValue);
            } else {
                PyErr_Print();
            }
            
            Py_XDECREF(pFunc);
        }
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }
    
    Py_Finalize();
    return result;
}

// Example: Call your master router
char* call_cortex_router(const char *query) {
    char args[1024];
    snprintf(args, sizeof(args), "{\"query\": \"%s\"}", query);
    
    return call_python_function("core.master_router", "route", args);
}

// Standalone executable
int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s \"query to process\"\n", argv[0]);
        return 1;
    }
    
    char *result = call_cortex_router(argv[1]);
    if (result) {
        printf("%s\n", result);
        free(result);
        return 0;
    } else {
        printf("Error processing query\n");
        return 1;
    }
}