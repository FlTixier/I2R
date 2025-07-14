.. _Pipeline_file:

Pipeline File
=============

**Img2Radiomics** operates through a pipeline file, which contains a sequence of instructions, or *modules*, that are executed in order.

Examples of pipeline files are available in the `img2radiomics` folder.

You can add comments in the pipeline file by prefixing the comment text with the `#` symbol.

Each module in the pipeline file follows a specific format, as shown below:

.. code-block:: bash

    MODULE_NAME:
    {
        key_1: value_1
        ...
        key_n: value_n
    }

The following sections provide detailed information about each module that can be used in the pipeline file.
