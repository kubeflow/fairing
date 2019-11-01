# kubeflow.fairing.functions package

## Submodules

## kubeflow.fairing.functions.function_shim module


#### class kubeflow.fairing.functions.function_shim.ObjectType()
Bases: `enum.Enum`

An enumeration.


### CLASS( = 2)

### FUNCTION( = 1)

### NOT_SUPPORTED( = 3)

#### kubeflow.fairing.functions.function_shim.call(serialized_fn_file)
Get the content from serialized function.


* **Parameters**

    **serialized_fn_file** – the file includes serialized function



* **Returns**

    object: The content of object.



#### kubeflow.fairing.functions.function_shim.compare_version(local_python_version)
Compare the Python major and minor version for local and remote python.


* **Parameters**

    **local_python_version** – Python version of local environment



* **Returns**

    None.



#### kubeflow.fairing.functions.function_shim.get_execution_obj_type(obj)
Get the execution object type, the object can be a function or class.


* **Parameters**

    **obj** – The name of object such as the function or class



* **Returns**

    int: The corresponding object type.


## Module contents
