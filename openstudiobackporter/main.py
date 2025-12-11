import argparse

# TODO: temp
import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, '/Users/julien/Software/Others/OS-build-release/Products/python')

from openstudiobackporter.backporter import KNOWN_TO_VERSIONS, Backporter


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openstudiobackporter", description="Backport an OpenStudio Model (OSM) file to an earlier version."
    )
    # Argument: -t, --to [VERSION], choices: list(VERSION_TRANSLATION_MAP.keys())
    parser.add_argument(
        "-t",
        "--to-version",
        type=str,
        required=True,
        choices=list(KNOWN_TO_VERSIONS),
        help="Target OpenStudio version to backport to.",
    )
    # Argument: -s, --save-intermediate (bool)
    parser.add_argument(
        '-s', '--save-intermediate', action='store_true', help='Save intermediate versions during backporting'
    )
    # Argument: position: the pathlib.Path (must exist) to the input OSM file
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    parser.add_argument("osm_path", type=Path, help="Path to the input OpenStudio Model (OSM) file.")

    return parser


def main(args_: list[str] | None = None) -> None:

    parser = get_parser()
    args = parser.parse_args(args_)

    if args.verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="DEBUG")
    else:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="INFO")
    backporter = Backporter(to_version=args.to_version, save_intermediate=args.save_intermediate)
    idf_file = backporter.backport_file(osm_path=args.osm_path)
    idf_path = args.osm_path.with_name(f"{args.osm_path.stem}_backported_to_{args.to_version}.osm")
    idf_file.save(idf_path, True)
    logger.info(f"Backported OSM file saved to: {idf_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
