import argparse

# TODO: temp
import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, '/Users/julien/Software/Others/OS-build-release/Products/python')

from openstudiobackporter.backporter import VERSION_TRANSLATION_MAP, Backporter

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backport an OpenStudio Model (OSM) file to an earlier version.")
    # Argument: -t, --to [VERSION], choices: list(VERSION_TRANSLATION_MAP.keys())
    parser.add_argument(
        "-t",
        "--to-version",
        type=str,
        required=True,
        choices=list(VERSION_TRANSLATION_MAP.keys()),
        help="Target OpenStudio version to backport to.",
    )
    # Argument: -s, --save-intermediate (bool)
    parser.add_argument(
        '-s', '--save-intermediate', action='store_true', help='Save intermediate versions during backporting'
    )
    # Argument: position: the pathlib.Path (must exist) to the input OSM file
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    parser.add_argument("osm_path", type=Path, help="Path to the input OpenStudio Model (OSM) file.")

    args = parser.parse_args()

    if args.verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="DEBUG")
    else:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="INFO")
    backporter = Backporter(to_version=args.to_version, save_intermediate=args.save_intermediate)
    backporter.backport_file(osm_path=args.osm_path)
