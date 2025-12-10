from pathlib import Path

import openstudio
from loguru import logger

from openstudiobackporter import backport_3_9_0_to_3_8_0, backport_3_10_0_to_3_9_0, backport_3_11_0_to_3_10_0


def run_translation_noop(idf_file: openstudio.IdfFile) -> openstudio.IdfFile:
    """No-op translation function."""
    return idf_file


VERSION_TRANSLATION_MAP = {
    "3.8.0": run_translation_noop,
    "3.9.0": backport_3_9_0_to_3_8_0.run_translation,
    "3.10.0": backport_3_10_0_to_3_9_0.run_translation,
    "3.11.0": backport_3_11_0_to_3_10_0.run_translation,
}

# Harcoding because of mkdocs
KNOWN_TO_VERSIONS = ["3.8.0", "3.9.0", "3.10.0"]
"""List of all known versions that can be translated *to*."""
assert KNOWN_TO_VERSIONS == list(VERSION_TRANSLATION_MAP.keys())[:-1]


def normalize_version(version: openstudio.VersionString) -> str:
    """Normalize a version string to the format 'X.Y.Z'."""
    return f"{version.major()}.{version.minor()}.{version.patch().value_or(0)}"


class Backporter:

    def __init__(self, to_version: str, save_intermediate: bool = False):
        if to_version not in VERSION_TRANSLATION_MAP:
            raise ValueError(f"Unsupported target version: {to_version}")

        self.to_version = openstudio.VersionString(to_version)
        self.to_version_str = to_version
        self.save_intermediate = save_intermediate
        self.osm_path = Path("in.osm")

    def backport_file(self, osm_path: Path) -> openstudio.IdfFile:
        """Backport an OpenStudio Model (OSM) file to an earlier version."""
        if not osm_path.exists():
            raise FileNotFoundError(f"The specified OSM file does not exist: {osm_path}")

        self.osm_path = osm_path
        version = openstudio.IdfFile.loadVersionOnly(osm_path)
        if not version.is_initialized():
            raise ValueError(f"Could not determine version of the input OSM file: {osm_path}")
        version = version.get()
        logger.warning(f"Detected OSM version: {version.str()}")
        print(version.str())
        if version <= self.to_version:
            raise ValueError(
                f"The input OSM file version {version.str()} is not newer "
                f"than the target version {self.to_version_str}"
            )

        # Do not try to load from openstudio.model.Model.load since it will fail for any older version rather than the
        # current one.
        ori_idd = openstudio.IddFactory.instance().getIddFile(openstudio.IddFileType("OpenStudio"), version).get()

        idf_file = openstudio.IdfFile.load(osm_path, ori_idd)
        if not idf_file.is_initialized():
            raise ValueError(f"Failed to load model from '{osm_path}'")
        idf_file = idf_file.get()
        return self.backport(idf_file=idf_file)

    def backport(self, idf_file: openstudio.IdfFile) -> openstudio.IdfFile:
        """Backport an OpenStudio Model as an IdfFile to an earlier version."""

        version = idf_file.version()
        if version <= self.to_version:
            raise ValueError(
                f"The input OSM file version {version.str()} is not newer "
                f"than the target version {self.to_version_str}"
            )

        while version != self.to_version:
            version_str = normalize_version(version=version)
            if version_str not in VERSION_TRANSLATION_MAP:
                raise ValueError(f"No translation available from version {version_str} to {self.to_version_str}")
            logger.debug(f"Translating input data from version {version_str}")
            translator = VERSION_TRANSLATION_MAP[version_str]
            # Translators translate the data in place so no need to reassign.
            idf_file = translator(idf_file)
            version = idf_file.version()
            if self.save_intermediate:
                intermediate_path = self.osm_path.with_name(f"{self.osm_path.stem}_backported_to_{version.str()}.osm")
                idf_file.save(intermediate_path, True)
                logger.info(f"Saved intermediate backported file to '{intermediate_path}'")

        return idf_file
