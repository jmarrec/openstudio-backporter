#!/usr/bin/env python
"""Tests for `openstudio-backporter` package, from 3.9.0 to 3.8.0."""

from pathlib import Path

import openstudio

from openstudiobackporter import Backporter
from openstudiobackporter.helpers import get_objects_by_type

THIS_DIR = Path(__file__).parent / "3_9_0"


def backport_and_save(osm_rel_path: Path) -> openstudio.IdfFile:
    backporter = Backporter(to_version="3.8.0", save_intermediate=False)
    idf_file = backporter.backport_file(osm_path=THIS_DIR / osm_rel_path)
    new_name = f"output_{osm_rel_path.stem.replace('3_9_0', '3_8_0')}.osm"
    idf_file.save(THIS_DIR / new_name, True)

    # Ensure we can still load the backported file
    m_ = openstudio.model.Model.load(THIS_DIR / new_name)
    assert m_.is_initialized()

    return idf_file


def test_vt_AirTerminalSingleDuctPIUReheat():
    idf_file = backport_and_save(osm_rel_path=Path("AirTerminalSingleDuctPIUReheat_3_9_0.osm"))

    seriess = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:AirTerminal:SingleDuct:SeriesPIU:Reheat")
    assert len(seriess) == 1
    series = seriess[0]

    # Previous last field: Convergence Tolerance
    assert series.getDouble(15).get() == 0.001

    # 4 deleted fields
    assert series.numFields() == 16

    parallels = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:AirTerminal:SingleDuct:ParallelPIU:Reheat"
    )
    assert len(parallels) == 1
    parallel = parallels[0]

    # Previous last field: Convergence Tolerance
    assert parallel.getDouble(16).get() == 0.001

    # 4 deleted fields
    assert parallel.numFields() == 17


def test_vt_ChillerElectric():
    idf_file = backport_and_save(osm_rel_path=Path("ChillerElectric_3_9_0.osm"))

    chiller_electric_eirs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Chiller:Electric:EIR")
    assert len(chiller_electric_eirs) == 1
    chiller_electric_eir = chiller_electric_eirs[0]

    assert chiller_electric_eir.getString(1).get() == "Chiller Electric EIR 1"

    # Previous last field: End-Use Subcategory
    assert chiller_electric_eir.getString(34).get() == "General"
    assert chiller_electric_eir.numFields() == 35

    chiller_electric_reformulatedeirs = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:Chiller:Electric:ReformulatedEIR"
    )
    assert len(chiller_electric_reformulatedeirs) == 1
    chiller_electric_reformulatedeir = chiller_electric_reformulatedeirs[0]

    assert chiller_electric_reformulatedeir.getString(1).get() == "Chiller Electric Reformulated EIR 1"

    # Previous last field: End-Use Subcategory
    assert chiller_electric_reformulatedeir.getString(30).get() == "General"
    assert chiller_electric_reformulatedeir.numFields() == 31


def test_vt_ControllerOutdoorAir():
    idf_file = backport_and_save(osm_rel_path=Path("ControllerOutdoorAir_3_9_0.osm"))

    controller_oas = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Controller:OutdoorAir")
    assert len(controller_oas) == 1
    controller_oa = controller_oas[0]

    # Fields 24 and 25 were made required, so they filled in the default value. I don't see the point reverting that.
    assert controller_oa.getString(1).get() == "Controller Outdoor Air 1"
    assert controller_oa.getString(22).get() == "No"  # High Humidity Control
    assert controller_oa.isEmpty(23)  # Humidistat Control Zone Name
    # These two left intact
    assert controller_oa.getDouble(24).get() == 1.0  # High Humidity Outdoor Air Flow Ratio
    assert controller_oa.getString(25).get() == "Yes"  # Control High Indoor Humidity Based on Outdoor Humidity Ratio
    assert controller_oa.getString(26).get() == "BypassWhenWithinEconomizerLimits"  # Heat Recovery Bypass Control Type
    assert controller_oa.getString(27).get() == "InterlockedWithMechanicalCooling"  # Economizer Operation Staging


def test_vt_HeatPumpPlantLoopEIR():
    idf_file = backport_and_save(osm_rel_path=Path("HeatPumpPlantLoopEIR_3_9_0.osm"))

    hp_heatings = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:HeatPump:PlantLoop:EIR:Heating")
    assert len(hp_heatings) == 1
    hp_heating = hp_heatings[0]

    assert hp_heating.getString(1).get() == "Heat Pump Plant Loop EIR Heating 1"

    assert hp_heating.getString(4).get() == "AirSource"  # Condenser Type
    assert hp_heating.isEmpty(5)  # Source Side Inlet Node Name
    assert hp_heating.isEmpty(6)  # Source Side Outlet Node Name

    # Field 7, 8 were deleted (Heat Recovery Inlet/Outlet Node Name)
    assert hp_heating.isEmpty(7)  # Companion Heat Pump Name
    assert hp_heating.getString(8).get() == "Autosize"  # Load Side Reference Flow Rate {m3/s}
    assert hp_heating.getString(9).get() == "Autosize"  # Source Side Reference Flow Rate {m3/s}
    # Field 12 was deleted (Heat Recovery Reference Flow Rate)
    assert hp_heating.getString(10).get() == "Autosize"  # Reference Capacity {W}
    assert hp_heating.getDouble(11).get() == 7.5  # Reference Coefficient of Performance {W/W}

    assert hp_heating.getString(27).get() == "None"  # Heat Pump Defrost Control
    assert hp_heating.getDouble(28).get() == 0.058333  # Heat Pump Defrost Time Period Fraction
    assert hp_heating.isEmpty(29)  # Defrost Energy Input Ratio Function of Temperature Curve Name
    assert hp_heating.isEmpty(30)  # Timed Empirical Defrost Frequency
    assert hp_heating.isEmpty(31)  # Timed Empirical Defrost Heat Load Penalty Curve Name
    assert hp_heating.isEmpty(32)  # Timed Empirical Defrost Heat Input Energy Fraction Curve Name

    # Field 36 was added (Minimum Heat Recovery Outlet Temperature)
    assert hp_heating.numFields() == 33

    hp_coolings = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:HeatPump:PlantLoop:EIR:Cooling")
    assert len(hp_coolings) == 1
    hp_cooling = hp_coolings[0]

    assert hp_cooling.getString(1).get() == "Heat Pump Plant Loop EIR Cooling 1"
    assert hp_cooling.getString(4).get() == "AirSource"  # Condenser Type
    assert hp_cooling.isEmpty(5)  # Source Side Inlet Node Name
    assert hp_cooling.isEmpty(6)  # Source Side Outlet Node Name

    # Field 7, 8 were deleted (Heat Recovery Inlet/Outlet Node Name)
    assert hp_cooling.isEmpty(7)  # Companion Heat Pump Name
    assert hp_cooling.getString(8).get() == "Autosize"  # Load Side Reference Flow Rate {m3/s}
    assert hp_cooling.getString(9).get() == "Autosize"  # Source Side Reference Flow Rate {m3/s}
    # Field 12 was deleted (Heat Recovery Reference Flow Rate)
    assert hp_cooling.getString(10).get() == "Autosize"  # Reference Capacity {W}
    assert hp_cooling.getDouble(11).get() == 7.5  # Reference Coefficient of Performance {W/W}

    assert hp_cooling.getDouble(20).get() == 100.0  # Maximum Source Inlet Temperature {C}
    assert hp_cooling.isEmpty(21)  # Minimum Supply Water Temperature Curve Name
    assert hp_cooling.isEmpty(22)  # Maximum Supply Water Temperature Curve Name

    # Two last fields deleted Minimum/Maximum Supply Water Temperature Curve Name
    assert hp_cooling.numFields() == 23


def test_vt_OutputControlFiles():
    idf_file = backport_and_save(osm_rel_path=Path("OutputControlFiles_3_9_0.osm"))

    ocfs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:OutputControl:Files")
    assert len(ocfs) == 1
    ocf = ocfs[0]

    # Field: Output Space Sizing was added in 3.9.0 at position 9
    # Before deletion: Output AUDIT
    assert ocf.getString(8).get() == "Yes"
    # After deletion: Output Zone Sizing
    assert ocf.getString(9).get() == "No"

    # Last field: Output Tarcog
    assert ocf.getString(30).get() == "Yes"

    assert ocf.numFields() == 31


def test_vt_SizingZone():
    idf_file = backport_and_save(osm_rel_path=Path("SizingZone_3_9_0.osm"))

    sizing_zones = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Sizing:Zone")
    assert len(sizing_zones) == 1
    sizing_zone = sizing_zones[0]

    # Last field: Sizing Option * 39 (at end) was deleted
    assert sizing_zone.getDouble(32).get() == 0.005  # Zone Humidification Design Supply Air Humidity Ratio Difference
    assert sizing_zone.isEmpty(33)  # Zone Humidistat Dehumidification Set Point Schedule Name
    assert sizing_zone.isEmpty(34)  # Zone Humidistat Humidification Set
    assert sizing_zone.isEmpty(35)  # Design Zone Air Distribution Effectiveness in Cooling Mode
    assert sizing_zone.isEmpty(36)  # Design Zone Air Distribution Effectiveness in Heating
    assert sizing_zone.isEmpty(37)  # Design Zone Secondary Recirculation Fraction
    assert sizing_zone.isEmpty(38)  # Design Minimum Zone Ventilation Efficiency

    assert sizing_zone.numFields() == 39
