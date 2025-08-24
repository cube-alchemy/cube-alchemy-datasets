# Cube Alchemy Datasets

A collection of small datasets for data projects, examples, and tutorials.

## Contents

- `examples/` - Real-world sample datasets
  - `adventureworks/` - AdventureWorks sample data (CSV)
- `synthetic/` - Artificially generated datasets
- `tutorials/` - Tutorial-specific datasets

## Usage

Easily download datasets directly from GitHub using Python:

```python
import pandas as pd

# Download a dataset directly from GitHub
url = "https://raw.githubusercontent.com/cube-alchemy/cube-alchemy-datasets/main/examples/adventureworks/Source/Sales.csv"
df = pd.read_csv(url, sep='\t') 
```

## Licensing

- Code (scripts, utilities, and example notebooks in this repository) is licensed under the MIT License. See the root [LICENSE](./LICENSE).
- Data: Each dataset has its own license in its directory. For example, `examples/adventureworks` CSVs are under LGPL-3.0 (see that folder's `LICENSE`).
