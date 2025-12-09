# Installation

## Stable release

To install openstudio-backporter, run this command in your
terminal:

``` console
$ pip install openstudio-backporter
```

This is the preferred method to install `openstudio-backporter`, as it will always install the most recent stable release.

If you don't have [pip][] installed, this [Python installation guide][]
can guide you through the process.

## From source

The source for openstudio-backporter can be downloaded from
the [Github repo][].

You can either clone the public repository:

``` console
$ git clone git://github.com/jmarrec/openstudio-backporter
```

Or download the [tarball][]:

``` console
$ curl -OJL https://github.com/jmarrec/openstudio-backporter/tarball/main
```

Once you have a copy of the source, you can install it with:

``` console
pip install poetry
poetry install --all-groups
```

Or you can also `pip install .` if you prefer.

  [pip]: https://pip.pypa.io
  [Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
  [Github repo]: https://github.com/jmarrec/openstudio-backporter
  [tarball]: https://github.com/openstudio-backporter/tarball/main
