<p align="left">
  <img src="logo_I2R.png" alt="Image2Radiomics Logo" height="60">
</p>

## Image2Radiomics (I2R)

[📘 **View the Documentation**](https://i2r.readthedocs.io/en/latest/)

This open-source Python package facilitates radiomics feature extraction from medical imaging, focusing on reproducibility across all processing steps before and after radiomics feature extraction. Rather than emphasizing feature extraction alone, this package ensures that every stage of the workflow is consistent and repeatable.

Using a straightforward instruction file, the package allows users to perform a series of operations, including:

- Image conversion (DICOM to NIfTI)
- Image resampling (using [c3d](https://sourceforge.net/projects/c3d/) or [SimpleITK](https://simpleitk.org/))  
- Image segmentation (using [TotalSegmentator](https://github.com/wasserth/TotalSegmentator))  
- Segmentation selection (by merging or excluding masks from a list)  
- Mask thresholding  
- Image windowing  
- Image harmonization  
- Feature normalization  
- Feature harmonization (with [ComBAT](https://github.com/Jfortin1/neuroCombat))  
- Radiomics feature extraction (using [PyRadiomics](https://pyradiomics.readthedocs.io/en/latest/))  
- Model evaluation  

---

## 📖 Citation

If you use this framework in your research or publications, please cite the following paper:

*Tixier, Florent, et al. "Ensuring Reproducibility and Deploying Models with the Image2Radiomics Framework: An Evaluation of Image Processing on PanNET Model Performance."* *Cancers*, vol. 17, no. 15, 2025.  
DOI: [https://doi.org/10.3390/cancers17152552](https://doi.org/10.3390/cancers17152552)

**BibTeX:**

```bibtex
@article{tixier2025,
    author  = {Tixier, Florent and Lopez-Ramirez, Felipe and Syailendra, Emir and Blanco, Alejandra and Javed, Ammar A. and Chu, Linda C. and Kawamoto, Satomi and Fishman, Elliot K.},
    title   = {Ensuring Reproducibility and Deploying Models with the Image2Radiomics Framework: An Evaluation of Image Processing on PanNET Model Performance},
    journal = {Cancers},
    year    = {2025},
    volume  = {17},
    number  = {15},
    doi     = {10.3390/cancers17152552}
}
```
---

## 🚧 Coming Soon

A new version of the framework is currently in development and will include:

-  A graphical user interface (GUI) for easier use
-  Support for saving and reloading processing pipelines in JSON format
-  Direct model saving and reuse through the GUI
-  And more to come

If you’d like to be notified when the new version is released, please fill out this short form:

👉 [**Stay updated on new releases**](https://forms.office.com/r/5wD34W1sA8)

---

## 🏛️ Funding

> This work was supported by the Lustgarten Foundation.  


## ⚠️ Intended Use

> **Warning:** Not intended for clinical use.

