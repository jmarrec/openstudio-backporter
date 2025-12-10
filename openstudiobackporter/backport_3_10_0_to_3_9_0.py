import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_cutoff_fields,
    copy_with_deleted_fields,
)


def run_translation(idf_3_10_0: openstudio.IdfFile) -> openstudio.IdfFile:
    """Backport an IdfFile from 3.10.0 to 3.9.0."""
    logger.info("Backporting from 3.10.0 to 3.9.0")

    idd_3_9_0 = (
        openstudio.IddFactory.instance()
        .getIddFile(openstudio.IddFileType("OpenStudio"), openstudio.VersionString(3, 9, 0))
        .get()
    )
    targetIdf = openstudio.IdfFile(idd_3_9_0)

    for obj in idf_3_10_0.objects():
        iddname = obj.iddObject().name()

        iddObject_ = idd_3_9_0.getObject(iddname)
        if not iddObject_.is_initialized():
            # Object type doesn't exist in target version, skip it
            logger.warning(f"{brief_description(idf_obj=obj)} does not exist in version 3.9.0, skipping.")
            continue

        iddObject = iddObject_.get()
        newObject = openstudio.IdfObject(iddObject)

        if iddname == "OS:WaterHeater:HeatPump":

            # 1 Field has been inserted from 3.9.0 to 3.10.0:
            # ----------------------------------------------
            # * Tank Element Control Logic * 25

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={25})
            targetIdf.addObject(newObject)

        elif iddname == 'OS:GroundHeatExchanger:Vertical':
            # 1 Field has been inserted from 3.9.0 to 3.10.0:
            # ----------------------------------------------
            # * Bore Hole Top Depth * 6

            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={6})
            targetIdf.addObject(newObject)

        elif iddname == 'OS:ZoneVentilation:DesignFlowRate' or iddname == "OS:SpaceInfiltration:DesignFlowRate":
            # 1 Field has been added (at end) from 3.9.0 to 3.10.0:
            # -------------------------------------------
            # * Density Basis * 13 or 26
            cut_off = 26 if iddname == "OS:ZoneVentilation:DesignFlowRate" else 13
            copy_with_cutoff_fields(obj=obj, newObject=newObject, cutoff_index=cut_off)
            targetIdf.addObject(newObject)

        else:
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

    return targetIdf
