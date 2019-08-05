# kubeflow.fairing.preprocessors package

## Submodules

## kubeflow.fairing.preprocessors.base module


#### class kubeflow.fairing.preprocessors.base.BasePreProcessor(input_files=None, command=None, executable=None, path_prefix='/app/', output_map=None)
Bases: `object`

Prepares a context that gets sent to the builder for the docker build and sets the entrypoint
:param input_files: the source files to be processed
:param executable: the file to execute using command (e.g. main.py)
:param output_map: a dict of files to be added without preprocessing
:param path_prefix: the prefix of the path where the files will be added in the container
:param command: the command to pass to the builder


### context_map()
Create context mapping from destination to source to avoid duplicates in context archive


* **Returns**

    c_map: a context map



### context_tar_gz(output_file=None)
Creating docker context file and compute a running cyclic redundancy check checksum.


* **Parameters**

    **output_file** – output file (Default value = None)



* **Returns**

    output_file,checksum: docker context file and checksum



### fairing_runtime_files()
Search the fairing runtime files ‘runtime_config.py’
:returns: cmd: the execute with absolute path


### get_command()
Get the execute with absolute path


* **Returns**

    cmd: the execute with absolute path



### is_requirements_txt_file_present()
Verfiy the requirements txt file if it is present.


* **Returns**

    res: get the present required files



### preprocess()
Preprocess the ‘input_files’.


* **Returns**

    input_files: get the input files



### set_default_executable()
Set the default executable file.


* **Returns**

    executable: get the default executable file if it is not existing, Or None



#### kubeflow.fairing.preprocessors.base.reset_tar_mtime(tarinfo)
Reset the mtime on the the tarball for reproducibility.

:param tarinfo: the tarball var
:returns: tarinfo: the modified tar ball

## kubeflow.fairing.preprocessors.converted_notebook module


#### class kubeflow.fairing.preprocessors.converted_notebook.ConvertNotebookPreprocessor(notebook_file=None, notebook_preprocessor=<class 'kubeflow.fairing.preprocessors.converted_notebook.FilterMagicCommands'>, executable=None, command=['python'], path_prefix='/app/', output_map=None, overwrite=True)
Bases: `kubeflow.fairing.preprocessors.base.BasePreProcessor`

Convert the notebook preprocessor.
:param BasePreProcessor: a context that gets sent to the builder for the docker build
and sets the entrypoint.


### preprocess()
Preprocessor the Notebook
:return:[]: the converted notebook list.


#### class kubeflow.fairing.preprocessors.converted_notebook.ConvertNotebookPreprocessorWithFire(class_name=None, notebook_file=None, notebook_preprocessor=<class 'kubeflow.fairing.preprocessors.converted_notebook.FilterIncludeCell'>, executable=None, command=['python'], path_prefix='/app/', output_map=None, overwrite=True)
Bases: `kubeflow.fairing.preprocessors.converted_notebook.ConvertNotebookPreprocessor`

Create an entrpoint using pyfire.


### preprocess()
Preprocessor the Notebook.
:return: results: the preprocessed notebook list.


#### class kubeflow.fairing.preprocessors.converted_notebook.FilterIncludeCell(\*\*kw)
Bases: `nbconvert.preprocessors.base.Preprocessor`

Notebook preprocessor that only includes cells that have a comment ‘fairing:include-cell’.
:param NbPreProcessor: the notebook preprocessor.


### filter_include_cell(src)
Filter the cell that have a comment ‘fairing:include-cell’.


* **Param**

    src: the source cell.



* **Returns**

    src: if the source cell matched the filter pattern, or Null.



### preprocess_cell(cell, resources, index)
Preprocess the notebook cell.


* **Parameters**

    
    * **cell** – the notebook cell


    * **resources** – the code source of the notebook cell.


    * **index** – unused argumnet.



* **Returns**

    cell,resources: the notebook cell and its filtered with magic pattern commands.



#### class kubeflow.fairing.preprocessors.converted_notebook.FilterMagicCommands(\*\*kw)
Bases: `nbconvert.preprocessors.base.Preprocessor`

Notebook preprocessor that have a comment which started with ‘!’ or ‘%’.
:param NbPreProcessor: the notebook preprocessor.


### filter_magic_commands(src)
Filter out the source commands with magic pattern.


* **Parameters**

    **src** – the source commands.



* **Returns**

    filtered: the filtered commands list.



### preprocess_cell(cell, resources, index)
preprocessor that includes cells


* **Param**

    cell: the notebook cell.



* **Param**

    resources: the code source of the notebook cell.



* **Param**

    index: unused argumnet.



* **Returns**

    cell,resources: the notebook cell and its filtered with magic pattern commands.


## kubeflow.fairing.preprocessors.full_notebook module


#### class kubeflow.fairing.preprocessors.full_notebook.FullNotebookPreProcessor(notebook_file=None, output_file='fairing_output_notebook.ipynb', input_files=None, command=None, path_prefix='/app/', output_map=None)
Bases: `kubeflow.fairing.preprocessors.base.BasePreProcessor`

The Full notebook preprocess for the context which comes from BasePreProcessor.
:param BasePreProcessor: a context that gets sent to the builder for the docker build and
sets the entrypoint


### set_default_executable()
Ingore the default executable setting for the full_notebook preprocessor.

## kubeflow.fairing.preprocessors.function module


#### class kubeflow.fairing.preprocessors.function.FunctionPreProcessor(function_obj, path_prefix='/app/', output_map=None, input_files=None)
Bases: `kubeflow.fairing.preprocessors.base.BasePreProcessor`

FunctionPreProcessor preprocesses a single function.
It sets as the command a function_shim that calls the function directly.
:param BasePreProcessor: a context that gets sent to the builder for the docker build
and sets the entrypoint.


### get_command()
Get the execute python command.
:returns: command: the command line will be executed

## Module contents
