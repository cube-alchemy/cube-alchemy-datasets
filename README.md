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
url = "https://raw.githubusercontent.com/cube-alchemy/cube-alchemy-datasets/main/examples/adventureworks/Sales.csv"
df = pd.read_csv(url, sep='\t') 
```

## License

Each dataset has its own license information in its directory.
