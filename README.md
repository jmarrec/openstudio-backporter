# openstudio-backporter


[![pypi](https://img.shields.io/pypi/v/openstudio-backporter.svg)](https://pypi.org/project/openstudio-backporter/)
[![python](https://img.shields.io/pypi/pyversions/openstudio-backporter.svg)](https://pypi.org/project/openstudio-backporter/)
[![Build Status](https://github.com/jmarrec/openstudio-backporter/actions/workflows/dev.yml/badge.svg)](https://github.com/jmarrec/openstudio-backporter/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/jmarrec/openstudio-backporter/branch/main/graphs/badge.svg)](https://codecov.io/github/jmarrec/openstudio-backporter)

A small library to backport an [OpenStudio](https://github.com/NREL/OpenStudio) OSM model to an older version.

**Note**: I am only adding backports as old as I need to. Contribution welcomed.

* Documentation: <https://jmarrec.github.io/openstudio-backporter>
* GitHub: <https://github.com/jmarrec/openstudio-backporter>
* PyPI: <https://pypi.org/project/openstudio-backporter/>
* TestPyPI: <https://test.pypi.org/project/openstudio-backporter/>

## Install

```shell
pip install openstudio-backporter
```

## Usage

### CLI
A CLI feature is provided, that you can invoke via `python -m openstudiobackporter`

See `python -m openstudiobackporter --help` for the list of command line parameters and how to use it.

Example:

```shell
python -m openstudiobackporter \
       --to-version 3.8.0 \
       --save-intermediate \
       --verbose \
       /path/to/model3_10_0.osm
```

### Library

You can also use it as a library:

```python
from pathlib import Path
from openstudiobackporter import Backporter

backporter = Backporter(to_version="3.9.0", save_intermediate=False)
idf_file = backporter.backport_file(osm_path=Path("/path/to/model_3_10_0.osm"))

# or
model = openstudio.model.exampleModel()
idf_file = backporter.backport(idf_file=model) # or model.toIdfFile()
```


---

This is free software (MIT License) contributed by [EffiBEM](https://effibem.com).

Leveraging software, [EffiBEM](https://effibem.com) specializes in providing new ways to streamline your workflows and create new tools that work with limited inputs for your specific applications. We also offer support and training services on BEM simulation engines (OpenStudio and EnergyPlus).
