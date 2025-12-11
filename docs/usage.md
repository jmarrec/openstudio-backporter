# Usage

To use openstudio-backporter in a project

```
import openstudiobackporter
```

# CLI

This also ships with a CLI, that you can invoke via `python -m openstudiobackporter`

Example:

```shell
python -m openstudiobackporter \
       --to-version 3.8.0 \
       --save-intermediate \
       --verbose \
       /path/to/model3_10_0.osm
```

See `python -m openstudiobackporter --help` for the list of command line parameters and how to use it.

```python exec="true"
from openstudiobackporter.main import get_parser

parser = get_parser()
print(f"```\n{parser.format_help()}\n```")

```
