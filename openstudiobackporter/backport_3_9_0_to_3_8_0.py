import openstudio
from loguru import logger


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

        if iddname == "OS:Controller:OutdoorAir":

            # 2 Fields have been made required from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * High Humidity Outdoor Air Flow Ratio * 24
            # * Control High Indoor Humidity Based on Outdoor Humidity Ratio * 25
            targetIdf.addObject(obj)

        elif iddname == "OS:OutputControl:Files":
            # 1 Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Output Space Sizing * 9
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            skip = 9

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

        elif iddname == "OS:HeatPump:PlantLoop:EIR:Heating":

            # 3 Fields have been inserted from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Heat Recovery Inlet Node Name * 7
            # * Heat Recovery Outlet Node Name * 8
            # * Heat Recovery Reference Flow Rate * 12

            # 1 required Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Minimum Heat Recovery Outlet Temperature * 36
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 7:
                        # fields before the inserted ones → same index
                        newObject.setString(i, value.get())
                    elif i < 9:
                        # 7 and 8 are new fields we are deleting
                        continue
                    elif i < 12:
                        # fields between old 7–9 were shifted by +2
                        newObject.setString(i - 2, value.get())
                    elif i < 36:
                        # fields after 10 were shifted by +3
                        newObject.setString(i - 3, value.get())
                    else:
                        # Field 36 was added, we remove it
                        continue

            targetIdf.addObject(newObject)

        elif iddname == "OS:HeatPump:PlantLoop:EIR:Cooling":

            # 3 Fields have been inserted from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Heat Recovery Inlet Node Name * 7
            # * Heat Recovery Outlet Node Name * 8
            # * Heat Recovery Reference Flow Rate * 12

            # 2 required Fields have been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Maximum Heat Recovery Outlet Temperature * 26
            # * Minimum Thermosiphon Minimum Temperature Difference * 30
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 7:
                        # fields before the inserted ones → same index
                        newObject.setString(i, value.get())
                    elif i < 9:
                        # 7 and 8 are new fields we are deleting
                        continue
                    elif i < 12:
                        # fields between old 7–9 were shifted by +2
                        newObject.setString(i - 2, value.get())
                    elif i < 26:
                        # fields after 10 were shifted by +3
                        newObject.setString(i - 3, value.get())
                    elif i < 30:
                        # fields between old 26–30 were shifted by +4
                        newObject.setString(i - 4, value.get())
                    else:
                        # Field 30 was added, we remove it
                        continue

            targetIdf.addObject(newObject)

        elif iddname == "OS:AirTerminal:SingleDuct:SeriesPIU:Reheat":
            # 5 Fields have been added (at the end) from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Fan Control Type * 16
            # * Minimum Fan Turn Down Ratio * 17
            # * Heating Control Type * 18
            # * Design Heating Discharge Air Temperature * 19
            # * High Limit Heating Discharge Air Temperature * 20

            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 16:
                        newObject.setString(i, value.get())

            targetIdf.addObject(newObject)

        elif iddname == "OS:AirTerminal:SingleDuct:ParallelPIU:Reheat":
            # 5 Fields have been added (at the end) from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Fan Control Type * 17
            # * Minimum Fan Turn Down Ratio * 18
            # * Heating Control Type * 19
            # * Design Heating Discharge Air Temperature * 20
            # * High Limit Heating Discharge Air Temperature * 21
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 17:
                        newObject.setString(i, value.get())

            targetIdf.addObject(newObject)

        elif iddname == "OS:Chiller:Electric:EIR":
            # 3 required Fields has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Condenser Flow Control * 35
            # * Condenser Minimum Flow Fraction * 38
            # * Thermosiphon Minimum Temperature Difference * 40
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 35:
                        # fields before the inserted ones → same index
                        newObject.setString(i, value.get())
                    elif i == 35:
                        # 35 is new field we are deleting
                        continue
                    elif i < 38:
                        # fields between old 35–38 were shifted by +1
                        newObject.setString(i - 1, value.get())
                    elif i == 38:
                        # 38 is new field we are deleting
                        continue
                    elif i < 40:
                        # fields between old 38–40 were shifted by +2
                        newObject.setString(i - 2, value.get())
                    else:
                        # Field 40 was added, and it is the last, we remove it
                        continue

            targetIdf.addObject(newObject)

        elif iddname == "OS:Chiller:Electric:ReformulatedEIR":
            # 3 required Fields has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Condenser Flow Control * 31
            # * Condenser Minimum Flow Fraction * 34
            # * Thermosiphon Minimum Temperature Difference * 36 (at end)

            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 31:
                        # fields before the inserted ones → same index
                        newObject.setString(i, value.get())
                    elif i == 31:
                        # 31 is new field we are deleting
                        continue
                    elif i < 34:
                        # fields between old 31–34 were shifted by +1
                        newObject.setString(i - 1, value.get())
                    elif i == 34:
                        # 34 is new field we are deleting
                        continue
                    elif i < 36:
                        # fields between old 34–36 were shifted by +2
                        newObject.setString(i - 2, value.get())
                    else:
                        # Field 36 was added, and it is the last, we remove it
                        continue

            targetIdf.addObject(newObject)

        elif iddname == "OS:Sizing:Zone":
            # 1 required Field has been added from 3.8.0 to 3.9.0:
            # ----------------------------------------------
            # * Sizing Option * 39 (at end)
            iddObject = idd_3_8_0.getObject(iddname).get()
            newObject = openstudio.IdfObject(iddObject)

            for i in range(obj.numFields()):
                value = obj.getString(i)
                if value.is_initialized():
                    if i < 39:
                        newObject.setString(i, value.get())

            targetIdf.addObject(newObject)

        else:
            targetIdf.addObject(obj)

    return targetIdf
