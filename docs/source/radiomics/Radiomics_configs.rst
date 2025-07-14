.. _Radiomics_configuration_file:

Radiomics Configuration File
============================

The radiomics configuration file defines the radiomics features to extract and the settings to use for extraction.

This file enables different configurations to be sent to PyRadiomics, except for features based on Gabor-filtered images, which are directly implemented in Img2Radiomics using SimpleITK (sitk).

A radiomics configuration file can contain one or more configurations. Each configuration starts with a description line, beginning with the symbol **#**. Each configuration includes:
- A configuration name (`configName`), which serves as a prefix for the radiomics feature names in the results Excel files.
- The image type (`imageType`), which can be `'Original'` or a filtering option.
- Additional parameters relevant to the configuration.

**Example of radiomics features on original images:**

.. code-block:: bash

    #Original
    configName: Original
    imageType: Original
    binWidth: 25
    verbose: False 
    padDistance: 0
    preCrop: True

**Example of radiomics features extracted from images filtered with Laplacian of Gaussian (LoG) using four different sigma values:**

.. code-block:: bash

    #LoG
    configName: LoG
    imageType: LoG
    sigma: [1.0, 3.0, 5.0, 10.0]
    binWidth: 25
    verbose: False 
    padDistance: 10
    preCrop: True

**Example of radiomics features extracted from images filtered with Coiflet 3 (wavelet):**

.. code-block:: bash

    #Wavelet Coif3
    configName: Wavelet_Coif3
    imageType: Wavelet
    start_level: 0
    level: 1
    wavelet: coif3
    binWidth: 25
    verbose: False 
    padDistance: 10
    preCrop: True

**Example of radiomics features extracted from images filtered with Gabor:**

.. code-block:: bash

    #Gabor_S8Fp5A45
    configName: Gabor_S8Fp5A45
    imageType: Gabor
    binWidth: 25
    verbose: False
    padDistance: 10
    preCrop: False
    size: 8
    freq: 0.5
    angle: math.pi/4
    save: False

**Note:** More details will be added in future updates.
