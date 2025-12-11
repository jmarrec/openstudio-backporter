import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_cutoff_fields,
    copy_with_deleted_fields,
    get_target,
)

COILS_WITH_AVAIL_SCHED = {
    "OS:Coil:Cooling:DX:VariableSpeed",
    "OS:Coil:Heating:DX:VariableSpeed",
    "OS:Coil:Cooling:WaterToAirHeatPump:EquationFit",
    "OS:Coil:Heating:WaterToAirHeatPump:EquationFit",
    "OS:Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit",
    "OS:Coil:Heating:WaterToAirHeatPump:VariableSpeedEquationFit",
    "OS:Coil:WaterHeating:AirToWaterHeatPump",
    "OS:Coil:WaterHeating:AirToWaterHeatPump:Wrapped",
    "OS:Coil:WaterHeating:AirToWaterHeatPump:VariableSpeed",
}

# Added at end: DX Heating Coil Sizing Ratio
DX_HEATING_COIL_SIZING_RATIOS = {
    "OS:ZoneHVAC:PackagedTerminalHeatPump": 25,
    "OS:ZoneHVAC:WaterToAirHeatPump": 25,
    "OS:AirLoopHVAC:UnitaryHeatPump:AirToAir": 18,
    "OS:AirLoopHVAC:UnitaryHeatPump:AirToAir:MultiSpeed": 10,
}


def run_translation(idf_3_11_0: openstudio.IdfFile) -> openstudio.IdfFile:
    """Backport an IdfFile from 3.11.0 to 3.10.0."""
    logger.info("Backporting from 3.11.0 to 3.10.0")

    idd_3_10_0 = (
        openstudio.IddFactory.instance()
        .getIddFile(openstudio.IddFileType("OpenStudio"), openstudio.VersionString(3, 10, 0))
        .get()
    )
    targetIdf = openstudio.IdfFile(idd_3_10_0)

    for obj in idf_3_11_0.objects():
        iddname = obj.iddObject().name()

        iddObject_ = idd_3_10_0.getObject(iddname)
        if not iddObject_.is_initialized():
            # Object type doesn't exist in target version, skip it
            logger.warning(f"{brief_description(idf_obj=obj)} does not exist in version 3.10.0, skipping.")
            continue

        iddObject = iddObject_.get()
        newObject = openstudio.IdfObject(iddObject)

        if iddname in COILS_WITH_AVAIL_SCHED:
            # 1 Field has been inserted from 3.10.0 to 3.11.0:
            # ----------------------------------------------
            # * Availability Schedule Name * 2

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={2})
            targetIdf.addObject(newObject)

        elif iddname == "OS:Site:WaterMainsTemperature":
            # 2 Fields have been inserted (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Temperature Multiplier * 5
            # * Temperature Offset * 6

            # copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={5, 6})
            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=5)
            targetIdf.addObject(newObject)

        elif iddname == "OS:ThermalStorage:ChilledWater:Stratified":
            # 1 Field was made required from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Nominal Cooling Capacity * 10
            # But we don't care about this change, so just copy as is

            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

            # Note: we added a WaterHeater:Sizing object for it though, this we'll delete

        elif iddname == "OS:WaterHeater:Sizing":
            wh_ = get_target(idf_file=idf_3_11_0, idf_obj=obj, index=1)
            if wh_.is_initialized():  # pragma: no cover
                whIddObject = wh_.get().iddObject()
                if whIddObject.name() == "OS:ThermalStorage:ChilledWater:Stratified":
                    # skip this object
                    continue

            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Sizing:Zone":
            # 2 Fields have been added (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Heating Coil Sizing Method * 40
            # * Maximum Heating Capacity To Cooling Load Sizing Ratio * 41

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=40)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Sizing:System":
            # 2 Fields have been added (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Heating Coil Sizing Method * 39
            # * Maximum Heating Capacity To Cooling Capacity Sizing Ratio * 40

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=39)
            targetIdf.addObject(newObject)

        elif iddname == "OS:HeatPump:AirToWater:FuelFired:Heating":
            # 1 Field has been added (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Minimum Unloading Ratio * 32

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=32)
            targetIdf.addObject(newObject)

        elif iddname == "OS:HeatPump:AirToWater:FuelFired:Cooling":
            # 1 Field has been added (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Minimum Unloading Ratio * 27

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=27)
            targetIdf.addObject(newObject)

        elif iddname in DX_HEATING_COIL_SIZING_RATIOS:
            # 1 Field has been added (at end) from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * DX Heating Coil Sizing Ratio * variable

            cut_off = DX_HEATING_COIL_SIZING_RATIOS[iddname]

            if iddname == "OS:AirLoopHVAC:UnitaryHeatPump:AirToAir:MultiSpeed":
                # This is the only field where it wasn't added at the end... Here Field 10 was changed from
                # Minimum Outdoor Dry-Bulb Temperature for Compressor Operation to
                # DX Heating Coil Sizing Ratio, so we need to skip it there
                copy_object_as_is(obj=obj, newObject=newObject)
                # Information is gone, so we reset to the OS SDK Ctor default from v3.10.0
                newObject.setDouble(cut_off, -8.0)
            else:
                copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=cut_off)

            targetIdf.addObject(newObject)

        elif iddname == "OS:Controller:MechanicalVentilation":

            # 1 Field has been modified from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * System Outdoor Air Method * 4 - Removed ProportionalControl
            # as mapping to ProportionalControlBasedonOccupancySchedule
            # Don't care
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

        elif iddname == "OS:People":
            # 2 Fields have been inserted from 3.10.0 to 3.11.0:
            # ------------------------------------------------
            # * Clothing Insulation Calculation Method * 8
            # * Clothing Insulation Calculation Method Schedule Name * 9

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={8, 9})
            targetIdf.addObject(newObject)

        elif iddname == "OS:EvaporativeFluidCooler:SingleSpeed":
            # 1 Field has been inserted from 3.10.0 to 3.10.1:
            # ------------------------------------------------
            # * Heat Rejection Capacity and Nominal Capacity Sizing Ratio * 9

            # 3 Fields were made required from 3.10.0 to 3.10.1:
            # ------------------------------------------------
            # * Design Entering Water Temperature * 14
            # * Design Entering Air Temperature * 15
            # * Design Entering Air Wet-bulb Temperature * 16
            # That part I don't care, leave the new values as is

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={9})
            targetIdf.addObject(newObject)

        elif iddname == "OS:EvaporativeFluidCooler:TwoSpeed":
            # 3 Fields were made required from 3.10.0 to 3.10.1:
            # ------------------------------------------------
            # * Design Entering Water Temperature * 24
            # * Design Entering Air Temperature * 25
            # * Design Entering Air Wet-bulb Temperature * 26
            # Don't care, leave the new values as is
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

        elif iddname == "OS:OutputControl:Files":
            # 1 Field has been added (at end) from 3.10.0 to 3.11.0:
            # ----------------------------------------------
            # * Output Plant Component Sizing * 32

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=32)
            targetIdf.addObject(newObject)

        else:
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

    return targetIdf
