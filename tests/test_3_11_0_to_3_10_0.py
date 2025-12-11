#!/usr/bin/env python
"""Tests for `openstudio-backporter` package, from 3.11.0 to 3.10.0."""

from pathlib import Path

import openstudio

from openstudiobackporter import Backporter
from openstudiobackporter.backport_3_11_0_to_3_10_0 import DX_HEATING_COIL_SIZING_RATIOS
from openstudiobackporter.helpers import get_objects_by_type

THIS_DIR = Path(__file__).parent / "3_11_0"


def backport_and_save(osm_rel_path: Path) -> openstudio.IdfFile:
    backporter = Backporter(to_version="3.10.0", save_intermediate=False)
    idf_file = backporter.backport_file(osm_path=THIS_DIR / osm_rel_path)
    new_name = f"output_{osm_rel_path.stem.replace('3_11_0', '3_10_0')}.osm"
    idf_file.save(THIS_DIR / new_name, True)

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


def test_vt_ControllerMechanicalVentilation():
    idf_file = backport_and_save(osm_rel_path=Path("ControllerMechanicalVentilation_3_11_0.osm"))

    controller_mvs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Controller:MechanicalVentilation")
    assert len(controller_mvs) == 1
    controller_mv = controller_mvs[0]

    # This field was changed from ProportionalControl to ProportionalControlBasedonOccupancySchedule
    assert controller_mv.getString(4).get() == "ProportionalControlBasedonOccupancySchedule"


def test_vt_DXHeatingCoilSizingRatio():
    idf_file = backport_and_save(osm_rel_path=Path("DXHeatingCoilSizingRatio_3_11_0.osm"))

    for idd_object_type_name, deleted_field_index in DX_HEATING_COIL_SIZING_RATIOS.items():
        objs = get_objects_by_type(idf_file=idf_file, idd_object_type_name=idd_object_type_name)
        assert len(objs) == 1
        obj = objs[0]

        # This is the only object where it was INSERTED, all others have it at the end
        if idd_object_type_name != "OS:AirLoopHVAC:UnitaryHeatPump:AirToAir:MultiSpeed":
            # Previous last field: DX Heating Coil Sizing Ratio
            assert obj.numFields() == deleted_field_index, f"Failed for {idd_object_type_name}"

    unitarys = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:AirLoopHVAC:UnitaryHeatPump:AirToAir:MultiSpeed"
    )
    assert len(unitarys) == 1
    unitary = unitarys[0]

    # This is the only field where it wasn't added at the end... Here Field 10 was changed from
    # Minimum Outdoor Dry-Bulb Temperature for Compressor Operation to
    # DX Heating Coil Sizing Ratio, so we need to skip it there
    # before changed
    assert unitary.getString(9).get() == "{4696d8bf-0b14-48d4-933c-94a9528ac84d}"  # Heating Coil
    # Reset back to the OS SDK Ctor default from v3.10.0
    assert unitary.getDouble(10).get() == -8.0  # Minimum Outdoor Dry-Bulb Temperature for Compressor Operation {C}
    # after changed
    assert unitary.getString(11).get() == "{0c95cb49-b78a-4430-9965-25c3cbfc84b4}"  # Cooling Coil

    # Last Field
    assert unitary.getString(31).get() == "autosize"  # Speed 4 Supply Air Flow Rate During Cooling Operation {m3/s}
    assert unitary.numFields() == 32


def test_vt_EvaporativeFluidCooler():
    idf_file = backport_and_save(osm_rel_path=Path("EvaporativeFluidCooler_3_11_0.osm"))

    evap_cooler_single_speeds = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:EvaporativeFluidCooler:SingleSpeed"
    )
    assert len(evap_cooler_single_speeds) == 1
    evap_cooler_single_speed = evap_cooler_single_speeds[0]

    assert evap_cooler_single_speed.getString(1).get() == "Evaporative Fluid Cooler Single Speed 1"

    # Before insertion: Performance Input Method
    assert evap_cooler_single_speed.getString(7).get() == "StandardDesignCapacity"
    # Before insertion: Outdoor Air Inlet Node Name
    assert evap_cooler_single_speed.isEmpty(8)
    # New Field: Heat Rejection Capacity and Nominal Capacity Sizing Ratio has been deleted, so after it
    assert evap_cooler_single_speed.getDouble(9).get() == 123.0  # Standard Design Capacity

    # Fields made required
    assert evap_cooler_single_speed.getString(13).get() == "Autosize"  # Design Entering Water Temperature
    assert evap_cooler_single_speed.getDouble(14).get() == 35.0  # Design Entering Air Temperature
    assert evap_cooler_single_speed.getDouble(15).get() == 26.6  # Design Entering Air Wet-bulb Temperature


def test_vt_HeatPumpAirToWaterFuelFired():
    idf_file = backport_and_save(osm_rel_path=Path("HeatPumpAirToWaterFuelFired_3_11_0.osm"))

    hp_heatings = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:HeatPump:AirToWater:FuelFired:Heating"
    )
    assert len(hp_heatings) == 1
    hp_heating = hp_heatings[0]

    assert hp_heating.getString(1).get() == "Heat Pump Air To Water Fuel Fired Heating 1"

    # Last Field (Minimum Unloading Ratio) has been deleted
    # Previous last field: Standby Electric Power {W}
    assert hp_heating.getDouble(31).get() == 0.0
    assert hp_heating.numFields() == 32

    # Cooling side, exactly the same, except the deleted field is at position 27
    hp_coolings = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:HeatPump:AirToWater:FuelFired:Cooling"
    )
    assert len(hp_coolings) == 1
    hp_cooling = hp_coolings[0]

    assert hp_cooling.getString(1).get() == "Heat Pump Air To Water Fuel Fired Cooling 1"

    # Last Field (Minimum Unloading Ratio) has been deleted
    # Previous last field: Standby Electric Power {W}
    assert hp_cooling.getDouble(26).get() == 0.0
    assert hp_cooling.numFields() == 27


def test_vt_OutputControlFiles():
    idf_file = backport_and_save(osm_rel_path=Path("OutputControlFiles_3_11_0.osm"))

    ocfs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:OutputControl:Files")
    assert len(ocfs) == 1
    ocf = ocfs[0]

    # Last field ( Output Plant Component Sizing) has been deleted (position 32)
    # Previous last field: Output Tarcog
    assert ocf.getString(31).get() == "Yes"
    assert ocf.numFields() == 32


def test_vt_People():
    idf_file = backport_and_save(osm_rel_path=Path("People_3_11_0.osm"))

    peoples = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:People")
    assert len(peoples) == 1
    people = peoples[0]

    # 2 Fields have been inserted from 3.10.0 to 3.11.0:
    # ------------------------------------------------
    # * Clothing Insulation Calculation Method * 8
    # * Clothing Insulation Calculation Method Schedule Name * 9

    # Before deletion
    assert people.isEmpty(7)  # Work Efficiency Schedule Name
    # After deletion
    assert people.getString(8).get() == "{26b7994e-de80-4f7f-a424-69814193928f}"  # Clothing Insulation Schedule Name
    assert people.isEmpty(9)  # Air Velocity Schedule Name
    assert people.getInt(10).is_initialized()
    assert people.getInt(10).get() == 1  # Multiplier
    assert people.numFields() == 11


def test_vt_SiteWaterMainsTemperature():
    idf_file = backport_and_save(osm_rel_path=Path("SiteWaterMainsTemperature_3_11_0.osm"))

    mains_temps = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Site:WaterMainsTemperature")
    assert len(mains_temps) == 1
    mains_temp = mains_temps[0]

    # Deleted the last two fields
    # * Temperature Multiplier * 5
    # * Temperature Offset * 6
    assert mains_temp.numFields() == 5


def test_vt_Sizing():
    idf_file = backport_and_save(osm_rel_path=Path("Sizing_3_11_0.osm"))

    sizing_zones = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Sizing:Zone")
    assert len(sizing_zones) == 1
    sizing_zone = sizing_zones[0]

    # Deleted the last two fields
    # * Heating Coil Sizing Method * 40
    # * Maximum Heating Capacity To Cooling Load Sizing Ratio * 41

    # Last field
    assert sizing_zone.getString(39).get() == "Coincident"  # Sizing Option
    assert sizing_zone.numFields() == 40

    sizing_systems = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Sizing:System")
    assert len(sizing_systems) == 1
    sizing_system = sizing_systems[0]

    # Deleted the last two fields
    # * Heating Coil Sizing Method * 39
    # * Maximum Heating Capacity To Cooling Load Sizing Ratio * 40

    # Last field
    assert sizing_system.getString(38).get() == "autosize"  # Occupant Diversity
    assert sizing_system.numFields() == 39


def test_vt_ThermalStorageChilledWaterStratified():
    idf_file = backport_and_save(osm_rel_path=Path("ThermalStorageChilledWaterStratified_3_11_0.osm"))

    tss = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ThermalStorage:ChilledWater:Stratified")
    assert len(tss) == 1
    ts = tss[0]

    # The field was made required, but we kept it: Nominal Cooling Capacity * 10
    assert ts.getDouble(10).get() == 0.0  # Nominal Cooling Capacity"

    # I expect the WaterHeater:Sizing object to be gone
    wh_sizings = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:WaterHeater:Sizing")
    assert len(wh_sizings) == 0


def test_vt_WaterHeaterMixed():
    """This file has a WaterHeaterSizing attached to a WaterHeaterMixed, and it should be left intact."""
    idf_file = backport_and_save(osm_rel_path=Path("WaterHeaterMixed_3_11_0.osm"))

    whs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:WaterHeater:Mixed")
    assert len(whs) == 1

    # I expect the WaterHeater:Sizing object to be left intact
    wh_sizings = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:WaterHeater:Sizing")
    assert len(wh_sizings) == 1


def test_vt_WaterHeaterHeatPump_New():
    """This object was added in 3.10.0, so should not be present in backported file."""
    idf_file = backport_and_save(osm_rel_path=Path("HeatPumpAirToWater_New_3_11_0.osm"))

    hpwhs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:HeatPump:AirToWater")
    assert len(hpwhs) == 0
