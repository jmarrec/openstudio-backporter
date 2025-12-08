import openstudio
from loguru import logger


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

        if iddname == "OS:WaterHeater:HeatPump":

            # 1 Field has been inserted from 3.9.0 to 3.10.0:
            # ----------------------------------------------
            # * Tank Element Control Logic * 25

            iddObject = idd_3_9_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            skip = 25

            for i in range(obj.numFields()):
                if i == skip:
                    continue
                elif i < skip:
                    if value := obj.getString(i):
                        newObject.setString(i, value.get())
                else:
                    if value := obj.getString(i):
                        newObject.setString(i - 1, value.get())

            targetIdf.addObject(newObject)

        elif iddname == 'OS:GroundHeatExchanger:Vertical':
            # 1 Field has been inserted from 3.9.0 to 3.10.0:
            # ----------------------------------------------
            # * Bore Hole Top Depth * 6

            iddObject = idd_3_9_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            skip = 6

            for i in range(obj.numFields()):
                if i == skip:
                    continue
                elif i < skip:
                    if value := obj.getString(i):
                        newObject.setString(i, value.get())
                else:
                    if value := obj.getString(i):
                        newObject.setString(i - 1, value.get())

            targetIdf.addObject(newObject)

        elif iddname == 'OS:ZoneVentilation:DesignFlowRate' or iddname == "OS:SpaceInfiltration:DesignFlowRate":
            # Last field was added
            iddObject = idd_3_9_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields() - 1):
                if value := obj.getString(i):
                    newObject.setString(i, value.get())

            targetIdf.addObject(newObject)

        else:
            targetIdf.addObject(obj)

    return targetIdf
