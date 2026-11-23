# Plant Disease Classifier - Project Report

## 1. Short description

This project classifies a submitted leaf image into one of 36 fixed crop-condition classes using a supplied VGG19 model. Its local React interface shows the predicted crop, condition, top-three class scores, a searchable class catalogue and project plots. It performs single-label image classification; it does not locate lesions or measure disease severity.

## 2. Requirements to run locally

- **Platform:** Windows local launch; 64-bit Python 3.10-3.12, an AVX-capable CPU and a current browser. CPU inference is supported; no GPU is required. Use the supported Microsoft Visual C++ runtime for TensorFlow on Windows.
- **Python packages:** tensorflow==2.16.2; tf-keras==2.16.0; numpy==1.26.4; Pillow>=10.4,<13. Install from backend/requirements.txt in a virtual environment.
- **Required files:** models/best_model.h5 (172.6 MiB), backend/server.py, backend/classes.json and the included dist/ frontend with its assets. Training images and notebooks are unnecessary for inference.
- **Setup and launch:** First setup needs internet for dependencies. Extract the package and run Start-PlantLab.cmd; open http://127.0.0.1:8787. Node.js is unnecessary for the prebuilt app. Frontend edits require Node.js 22+ and pnpm 11.

Manual setup from the extracted project root (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/server.py --model models/best_model.h5 --port 8787
```

## 3. Classification details

The output space contains 14 crops, 12 healthy classes and 24 disease/pest-condition classes. A class combines crop and condition, for example Tomato___Late_blight. The complete ordered identifiers are in backend/classes.json; display names below retain their meaning. The source identifier spells citrus greening as "Haunglongbing"; the display spelling is corrected here.

| Crop | Supported condition classes |
|---|---|
| Apple | Healthy; cedar apple rust |
| Blueberry | Healthy |
| Cherry (including sour) | Healthy; powdery mildew |
| Corn (maize) | Healthy; Cercospora / gray leaf spot; common rust; northern leaf blight |
| Grape | Healthy; black rot; Esca (black measles); Isariopsis leaf spot |
| Orange | Huanglongbing (citrus greening) |
| Peach | Healthy; bacterial spot |
| Bell pepper | Healthy; bacterial spot |
| Potato | Healthy; early blight; late blight |
| Raspberry | Healthy |
| Soybean | Healthy |
| Squash | Powdery mildew |
| Strawberry | Healthy; leaf scorch |
| Tomato | Healthy; bacterial spot; early blight; late blight; leaf mold; Septoria leaf spot; two-spotted spider mite; target spot; yellow leaf curl virus; mosaic virus |

A displayed 80% means a softmax class score of 0.80. It does not mean 80% diseased leaf area, 80% severity or 80% measured accuracy. Calibration is unverified. All 36 scores sum to approximately 100%; the interface ranks the top three and its plot groups the remainder.

## 4. Best model and available evidence

The supplied deployment checkpoint is models/best_model.h5: a VGG19 ImageNet backbone with a Flatten layer, a 256-unit ReLU layer and a 36-unit softmax output. It accepts 256 x 256 RGB images and has 28,422,500 parameters. The notebook configures checkpoint selection by validation accuracy.

This is the only supplied deployable H5 checkpoint, so it is the model used by the interface. The filename "best_model" does not establish that VGG19 is the best architecture or that this checkpoint has a trustworthy measured accuracy. No reliable independent benchmark or comparison with alternative models was supplied. No 98% accuracy claim is justified.

## 5. Key findings

- **Working integration:** The model loads through tf_keras and returns finite, ranked class scores. The frontend separates crop, condition and score, exposes all 36 classes and retains the original notebook figures. Functional success does not validate diagnostic correctness.
- **Preprocessing mismatch:** The training generator uses VGG19 preprocessing (BGR conversion and ImageNet mean subtraction), while the supplied GUI divides RGB pixels by 255. The default bridge preserves the GUI behavior. This mismatch remains unresolved in this delivery; a clearer UI does not repair prediction quality.
- **Limited model sanity checks:** On one image from each of the 36 training folders, default preprocessing matched 1/36 folder labels; experimental training-style preprocessing matched 17/36. These are small in-sample diagnostics, not test accuracy. Changing preprocessing alone is not a validated fix.
- **Evaluation weaknesses:** The archive contains 52,814 training images, 1,500 validation images and 35 test images. Validation covers only 8/36 classes. All 1,500 validation relative filenames occur in Train, and the notebook copies resized training files into Valid. This creates leakage concerns; filename overlap is not proof of byte identity.
- **Class-map and unknown-input limits:** The original training class-index map was not saved alongside the checkpoint. The integration reconstructs it from sorted training folder names, so historical ordering still needs verification. There is no validated rejection stage for non-leaf or unfamiliar inputs.
- **Plot interpretation:** The three supplied notebook figures are preprocessed training-image previews with display clipping. They are not lesion heatmaps, accuracy/loss curves or a confusion matrix. The current score chart explains model output only.

Evidence: supplied model and notebook; archive directory audit; local functional and 36-class diagnostic checks. Technical references: [Keras VGG19 preprocessing](https://keras.io/2/api/applications/vgg/) and [TensorFlow installation](https://www.tensorflow.org/install/pip).
