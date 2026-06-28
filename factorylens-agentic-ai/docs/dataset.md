# Dataset provenance and validation

FactoryLens uses the Magnetic Tile Surface Defect Dataset published by the dataset authors. It contains six categories: blowhole, break, crack, fray, uneven and defect-free. The downloader reads directly from the original repository.

Expected distribution:

| Class | Images |
|---|---:|
| Blowhole | 115 |
| Break | 85 |
| Crack | 57 |
| Fray | 32 |
| Uneven | 103 |
| Free | 952 |
| **Total** | **1,344** |

The validator checks per-class counts, image readability, SHA-256 values, duplicate files, and the presence of PNG masks for all 392 defective JPG images. It writes a JSON validation report and a CSV manifest.

Because the dataset is strongly imbalanced, the training pipeline uses class-weighted cross-entropy and reports macro F1 rather than accuracy alone.
