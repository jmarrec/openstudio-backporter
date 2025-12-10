#!/usr/bin/env python
"""Tests for `openstudio-backporter` package, from 3.11.0 to 3.10.0."""

from pathlib import Path

import openstudio

from openstudiobackporter import Backporter
from openstudiobackporter.helpers import get_objects_by_type

THIS_DIR = Path(__file__).parent / "3_11_0"


def backport_and_save(osm_rel_path: Path) -> openstudio.IdfFile:
    backporter = Backporter(to_version="3.10.0", save_intermediate=False)
    idf_file = backporter.backport_file(osm_path=THIS_DIR / osm_rel_path)
    new_name = f"output_{osm_rel_path.stem.replace('3_11_0', '3_10_0')}.osm"
    idf_file.save(THIS_DIR / new_name)

    # Ensure we can still load the backported file
    m_ = openstudio.model.Model.load(THIS_DIR / new_name)
    assert m_.is_initialized()

    return idf_file


def test_vt_CoilAvailabilitySchedules():
    # Deleted Availablity Schedule at position 2 in a bunch of coils
    idf_file = backport_and_save(osm_rel_path=Path("CoilAvailabilitySchedules_3_11_0.osm"))

    coils = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Coil:Cooling:DX:VariableSpeed")
    assert len(coils) == 1
    coil = coils[0]

    # Before Deletion: Name
    assert coil.getString(1).get() == "Coil Cooling DX Variable Speed 1"
    # After Deletion: Indoor Air Inlet Node Name
    assert coil.isEmpty(2)  # Indoor Air Inlet Node Name
    assert coil.isEmpty(3)  # Indoor Air Outlet Node Name
    assert coil.getInt(4).get() == 1  # Nominal Speed Level {dimensionless}

    # Last Field
    assert coil.getString(25).get() == "{872ca954-6bc5-4943-b51a-0a669700549d}"  # Speed Data List
    assert coil.numFields() == 26
