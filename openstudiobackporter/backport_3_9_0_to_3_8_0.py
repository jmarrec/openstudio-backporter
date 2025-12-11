import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_cutoff_fields,
    copy_with_deleted_fields,
)


def run_translation(idf_3_9_0: openstudio.IdfFile) -> openstudio.IdfFile:
    """Backport an IdfFile from 3.9.0 to 3.8.0."""
    logger.info("Backporting from 3.9.0 to 3.8.0")

    idd_3_8_0 = (
        openstudio.IddFactory.instance()
        .getIddFile(openstudio.IddFileType("OpenStudio"), openstudio.VersionString(3, 8, 0))
        .get()
    )
    targetIdf = openstudio.IdfFile(idd_3_8_0)

    for obj in idf_3_9_0.objects():
        iddname = obj.iddObject().name()

        iddObject_ = idd_3_8_0.getObject(iddname)
        if not iddObject_.is_initialized():  # pragma: no cover
            # Object type doesn't exist in target version, skip it (None in 3.9.0 to 3.8.0 backport)
            logger.warning(f"{brief_description(idf_obj=obj)} does not exist in version 3.8.0, skipping.")
            continue

        iddObject = iddObject_.get()
        newObject = openstudio.IdfObject(iddObject)

        if iddname == "OS:Controller:OutdoorAir":

            # 2 Fields have been made required from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * High Humidity Outdoor Air Flow Ratio * 24
            # * Control High Indoor Humidity Based on Outdoor Humidity Ratio * 25
            # Fields were made required, so they filled in the default value. I don't see the point reverting that.
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

        elif iddname == "OS:OutputControl:Files":
            # 1 Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Output Space Sizing * 9

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={9})
            targetIdf.addObject(newObject)

        elif iddname == "OS:HeatPump:PlantLoop:EIR:Heating":

            # 3 Fields have been inserted from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Heat Recovery Inlet Node Name * 7
            # * Heat Recovery Outlet Node Name * 8
            # * Heat Recovery Reference Flow Rate * 12

            # 1 required Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Minimum Heat Recovery Outlet Temperature * 36

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={7, 8, 12, 36})
            targetIdf.addObject(newObject)

        elif iddname == "OS:HeatPump:PlantLoop:EIR:Cooling":

            # 3 Fields have been inserted from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Heat Recovery Inlet Node Name * 7
            # * Heat Recovery Outlet Node Name * 8
            # * Heat Recovery Reference Flow Rate * 12

            # 5 fields added at end, 2 are required Fields, from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Maximum Heat Recovery Outlet Temperature * 26
            # * Minimum Thermosiphon Minimum Temperature Difference * 30

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={7, 8, 12, 26, 27, 28, 29, 30})
            targetIdf.addObject(newObject)

        elif iddname == "OS:AirTerminal:SingleDuct:SeriesPIU:Reheat":
            # 5 Fields have been added (at the end) from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Fan Control Type * 16
            # * Minimum Fan Turn Down Ratio * 17
            # * Heating Control Type * 18
            # * Design Heating Discharge Air Temperature * 19
            # * High Limit Heating Discharge Air Temperature * 20

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=16)
            targetIdf.addObject(newObject)

        elif iddname == "OS:AirTerminal:SingleDuct:ParallelPIU:Reheat":
            # 5 Fields have been added (at the end) from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Fan Control Type * 17
            # * Minimum Fan Turn Down Ratio * 18
            # * Heating Control Type * 19
            # * Design Heating Discharge Air Temperature * 20
            # * High Limit Heating Discharge Air Temperature * 21

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=17)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Chiller:Electric:EIR":
            # 7 fields added at end, 3 required Fields has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Condenser Flow Control * 35
            # * Condenser Minimum Flow Fraction * 38
            # * Thermosiphon Minimum Temperature Difference * 40

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=35)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Chiller:Electric:ReformulatedEIR":
            # 7 fields added at end, 3 required Fields has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Condenser Flow Control * 31
            # * Condenser Minimum Flow Fraction * 34
            # * Thermosiphon Minimum Temperature Difference * 36 (at end)

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=31)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Sizing:Zone":
            # 1 required Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Sizing Option * 39 (at end)

            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=39)
            targetIdf.addObject(newObject)

        else:
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

    return targetIdf
