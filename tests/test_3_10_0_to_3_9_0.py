#!/usr/bin/env python
"""Tests for `openstudio-backporter` package, from 3.10.0 to 3.9.0."""

from pathlib import Path

import openstudio

from openstudiobackporter import Backporter
from openstudiobackporter.helpers import get_objects_by_type, get_target

THIS_DIR = Path(__file__).parent / "3_10_0"


def backport_and_save(osm_rel_path: Path) -> openstudio.IdfFile:
    backporter = Backporter(to_version="3.9.0", save_intermediate=False)
    idf_file = backporter.backport_file(osm_path=THIS_DIR / osm_rel_path)
    new_name = f"output_{osm_rel_path.stem.replace('3_10_0', '3_9_0')}.osm"
    idf_file.save(THIS_DIR / new_name, True)

    # Ensure we can still load the backported file
    m_ = openstudio.model.Model.load(THIS_DIR / new_name)
    assert m_.is_initialized()

    return idf_file


def test_vt_GroundHeatExchangerVertical():
    idf_file = backport_and_save(osm_rel_path=Path("GroundHeatExchangerVertical_3_10_0.osm"))

    ghe_verts = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:GroundHeatExchanger:Vertical")
    assert len(ghe_verts) == 1
    ghe_vert = ghe_verts[0]

    assert ghe_vert.getInt(5).get() == 120  # Number of Bore Holes
    #  Bore Hole Top Depth (pos 6) was deleted
    assert ghe_vert.getDouble(6).get() == 76.2  # Bore Hole Length


def test_vt_WaterHeaterHeatPump():
    idf_file = backport_and_save(osm_rel_path=Path("WaterHeaterHeatPump_3_10_0.osm"))

    hpwhs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:WaterHeater:HeatPump")
    assert len(hpwhs) == 1
    hpwh = hpwhs[0]

    assert hpwh.getString(1).get() == "Water Heater Heat Pump 1"

    # Before Deletion: Inlet Air Mixer Schedule
    # Can't call getTarget, this is not a Workspace
    target_ = get_target(idf_file=idf_file, idf_obj=hpwh, index=24)
    assert target_.is_initialized()
    assert target_.get().nameString() == "HPWH Inlet Air Mixer Schedule"

    # Deleted: Tank Element Control Logic

    # After deletion and also last field: Control Sensor Location In Stratified Tank
    assert hpwh.getString(25).get() == "Heater2"


def test_vt_SpaceInfiltrationDesignFlowRate():
    idf_file = backport_and_save(osm_rel_path=Path("SpaceInfiltrationDesignFlowRate_3_10_0.osm"))

    spidfrs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:SpaceInfiltration:DesignFlowRate")
    assert len(spidfrs) == 1
    spidfr = spidfrs[0]

    # Previous last field: Velocity Squared Term Coefficient
    assert spidfr.getDouble(12).get() == 0.2

    # Last field: Density Basis should have been deleted
    assert spidfr.numFields() == 13


def test_vt_ZoneVentilationDesignFlowRate():
    idf_file = backport_and_save(osm_rel_path=Path("ZoneVentilationDesignFlowRate_3_10_0.osm"))

    zvidfrs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ZoneVentilation:DesignFlowRate")
    assert len(zvidfrs) == 1
    zvidfr = zvidfrs[0]

    # Previous last field: Maximum Wind Speed
    assert zvidfr.getDouble(25).get() == 40.0

    # Last field: Density Basis should have been deleted
    assert zvidfr.numFields() == 26


def test_vt_PythonPluginSearchPaths_New():
    """This object was added in 3.10.0, so should not be present in backported file."""
    idf_file = backport_and_save(osm_rel_path=Path("PythonPluginSearchPaths_New_3_10_0.osm"))

    search_paths = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:PythonPlugin:SearchPaths")
    assert len(search_paths) == 0
