import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_added_fields,
    copy_with_deleted_fields,
)


def _evaluate_regular_curve(curve_obj: openstudio.IdfObject, x_values: list[float]) -> list[float]:
    """Evaluate a curve object at a given x value.

    Args:
    -----
    * curve_obj: (openstudio.IdfObject) The curve object to evaluate
    * x_values: (list[float]) The x values at which to evaluate the curve

    Returns:
    -------
    * (list[float]) The evaluated y values of the curve at the given x values

    Preconditions:
    --------------
    * curve_obj must be a valid curve object (not OS:Table:Lookup)
    * It assumes the Curve object did not get any IDD changes between 3.8.0 and the version of openstudio you use
    """

    curve_idd = curve_obj.iddObject()
    curve_idd_name = curve_idd.name()
    if curve_idd_name == "OS:Table:Lookup":
        raise ValueError("OS:Table:Lookup curves cannot be evaluated directly")

    m = openstudio.model.Model()

    model_curve_idd = m.iddFile().getObject(curve_idd_name)
    assert model_curve_idd.is_initialized(), f"Curve type '{curve_idd_name}' not found in IddFile"
    model_curve_idd = model_curve_idd.get()

    # We check that the IDD matches the one in the model, to ensure that the curve object is compatible with the model
    n_this = curve_idd.numFields() + curve_idd.properties().numExtensible
    n_model = model_curve_idd.numFields() + model_curve_idd.properties().numExtensible
    if n_this != n_model:
        raise ValueError(
            f"Curve object of type '{curve_idd_name}' has {curve_idd.numFields()} fields, "
            f"but the model expects {model_curve_idd.numFields()} fields. "
            "This indicates that the curve object is not compatible with the model."
        )
    for i in range(n_this):
        this_field = curve_idd.getField(i).get()
        model_field = model_curve_idd.getField(i).get()
        if this_field.name() != model_field.name():
            raise ValueError(
                f"Curve object of type '{curve_idd_name}' has field '{this_field.name()}' at index {i}, "
                f"but the model expects field '{model_field.name()}'. "
                "This indicates that the curve object is not compatible with the model."
            )

    o_ = m.addObject(openstudio.IdfObject(model_curve_idd))
    assert o_.is_initialized(), f"Failed to add curve object of type '{curve_idd_name}' to model"
    curve = o_.get().to_Curve().get()

    if curve.numVariables() != 1:
        raise ValueError(
            f"Curve object of type '{curve_idd_name}' has {curve.numVariables()} variables, but only 1 is supported"
        )

    for i in range(curve_obj.numFields()):
        if value := curve_obj.getString(i):
            curve.setString(i, value.get())

    return [curve.evaluate(x) for x in x_values]


def _evaluate_table_lookup(
    idf_3_8_0: openstudio.IdfFile, curve_obj: openstudio.IdfObject, x_values: list[float]
) -> list[float] | None:
    if curve_obj.iddObject().name() != "OS:Table:Lookup":
        raise ValueError("Only OS:Table:Lookup curves are accepted")

    if curve_obj.getString(3).get().lower() != 'divisoronly':
        logger.warning(f"{brief_description(idf_obj=curve_obj)} is not 'DivisorOnly', cannot evaluate.")
        return None
    divisor = curve_obj.getDouble(4).value_or(1.0)
    assert divisor > 0, f"{brief_description(idf_obj=curve_obj)}: Divisor must be greater than 0, got {divisor}"

    ind_var_list_uid = openstudio.toUUID(curve_obj.getString(2).get())
    ind_var_list_ = idf_3_8_0.getObject(ind_var_list_uid)
    if not ind_var_list_.is_initialized():
        raise ValueError(f"{brief_description(idf_obj=curve_obj)}: independent variable list is not found.")
    ind_var_list = ind_var_list_.get()
    if ind_var_list.numExtensibleGroups() != 1:
        raise ValueError(
            f"{brief_description(idf_obj=curve_obj)}: independent variable list has "
            f"{ind_var_list.numExtensibleGroups()} extensible groups, expected 1."
        )
    ind_var_uid = openstudio.toUUID(ind_var_list.getExtensibleGroup(0).getString(0).get())
    ind_var_ = idf_3_8_0.getObject(ind_var_uid)
    if not ind_var_.is_initialized():
        raise ValueError(f"{brief_description(idf_obj=curve_obj)}: independent variable is not found.")
    ind_var = ind_var_.get()

    interp_method = ind_var.getString(2).get().lower()
    extrap_method = ind_var.getString(3).get().lower()
    if interp_method != 'linear':
        logger.warning(f"{brief_description(idf_obj=ind_var)}: not 'Linear' for interpolation, " "cannot evaluate.")
        return None
    if extrap_method != 'linear':
        logger.warning(f"{brief_description(idf_obj=ind_var)}: not 'Linear' for extrapolation, " "cannot evaluate.")
        return None

    y_values: list[float | None] = [None for _ in x_values]

    if curve_obj.numExtensibleGroups() != ind_var.numExtensibleGroups():
        raise ValueError(
            f"{brief_description(idf_obj=curve_obj)}: the number of extensible groups in the curve and "
            "independent variable do not match."
        )

    xs = []
    ys = []
    for i, (x_eg, y_eg) in enumerate(zip(ind_var.extensibleGroups(), curve_obj.extensibleGroups())):
        x = x_eg.getDouble(0).get()
        y = y_eg.getDouble(0).get()
        xs.append(x)
        ys.append(y / divisor)

    for i, x in enumerate(x_values):
        if x < xs[0] or x > xs[-1]:
            logger.warning(
                f"{brief_description(idf_obj=curve_obj)}: the x value {x} is outside the range of the independent "
                f"variable ({xs[0]} to {xs[-1]}), cannot evaluate."
            )
            continue

        for j in range(1, len(xs)):
            if x <= xs[j]:
                # Linear interpolation
                y = ys[j - 1] + (ys[j] - ys[j - 1]) * (x - xs[j - 1]) / (xs[j] - xs[j - 1])
                y_values[i] = y
                break

    # Verify that all x values were evaluated
    for i, y in enumerate(y_values):
        if y is None:
            logger.warning(f"{brief_description(idf_obj=curve_obj)}: the x value {x_values[i]} could not be evaluated.")
            return None

    return y_values  # type: ignore[return-value]


def run_translation(idf_3_8_0: openstudio.IdfFile) -> openstudio.IdfFile:
    """Backport an IdfFile from 3.8.0 to 3.7.0."""
    logger.info("Backporting from 3.8.0 to 3.7.0")

    idd_3_7_0 = (
        openstudio.IddFactory.instance()
        .getIddFile(openstudio.IddFileType("OpenStudio"), openstudio.VersionString(3, 7, 0))
        .get()
    )
    targetIdf = openstudio.IdfFile(idd_3_7_0)

    for obj in idf_3_8_0.objects():
        iddname = obj.iddObject().name()

        iddObject_ = idd_3_7_0.getObject(iddname)
        if not iddObject_.is_initialized():  # pragma: no cover
            # Object type doesn't exist in target version, skip it (None in 3.8.0 to 3.7.0 backport)
            logger.warning(f"{brief_description(idf_obj=obj)} does not exist in version 3.7.0, skipping.")
            continue

        iddObject = iddObject_.get()
        newObject = openstudio.IdfObject(iddObject)

        if iddname == "OS:HeatExchanger:AirToAir:SensibleAndLatent":

            # 4 Fields have been removed from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Sensible Effectiveness at 75% Heating Air Flow {dimensionless} * 6
            # * Latent Effectiveness at 75% Heating Air Flow {dimensionless} * 7
            # * Sensible Effectiveness at 75% Cooling Air Flow {dimensionless} * 10
            # * Latent Effectiveness at 75% Cooling Air Flow {dimensionless} * 11

            # 4 Fields have been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Sensible Effectiveness of Heating Air Flow Curve Name * 20
            # * Latent Effectiveness of Heating Air Flow Curve Name * 21
            # * Sensible Effectiveness of Cooling Air Flow Curve Name * 22
            # * Latent Effectiveness of Cooling Air Flow Curve Name * 23

            # copy the object while inserting fields for the Effectiveness at 75%
            eff_75_indices = (6, 7, 10, 11)
            eff_100_indices = (4, 5, 6, 7)
            eff_curve_indices = (20, 21, 22, 23)
            copy_with_added_fields(obj=obj, newObject=newObject, inserted_indices=set(eff_75_indices))

            # loop through the effectiveness curves and convert them
            for e100, e75, ec in zip(eff_100_indices, eff_75_indices, eff_curve_indices):
                curve_uid = openstudio.toUUID(obj.getField(ec).get())
                curve_obj_ = idf_3_8_0.getObject(curve_uid)
                if curve_obj_:
                    curve_obj = curve_obj_.get()
                    curve_idd_name = curve_obj.iddObject().name()
                    x_values = [0.75, 1.0]

                    if curve_idd_name == "OS:Table:Lookup":
                        y_values = _evaluate_table_lookup(idf_3_8_0=idf_3_8_0, curve_obj=curve_obj, x_values=x_values)
                        if y_values is None:
                            logger.warning(
                                f"{brief_description(idf_obj=obj)}: Effectiveness curve '{curve_obj.name().get()}' "
                                "is a table lookup that cannot be evaluated, skipping conversion and using "
                                "constant effectiveness instead."
                            )
                            y_values = [1.0, 1.0]
                    else:
                        y_values = _evaluate_regular_curve(curve_obj=curve_obj, x_values=x_values)

                    e100_value = obj.getDouble(e100).value_or(1.0)
                    y75, y100 = y_values

                    newObject.setDouble(e75, y75 * e100_value)
                    # If y100 isn't near 1.0, we warn
                    if abs(y100 - 1.0) > 1e-3:
                        logger.warning(
                            f"{brief_description(idf_obj=obj)}: Effectiveness curve '{curve_obj.name().get()}' "
                            f"evaluated at 100% flow is {y100:.6f}, expected 1.0. "
                            "This may indicate that the curve is not normalized to 1.0 at 100% flow."
                        )

                else:  # if no curve has been assigned, assume a constant effectiveness
                    if value := obj.getString(e100):
                        newObject.setString(e75, value.get())

            targetIdf.addObject(newObject)

        elif (
            iddname == "OS:ZoneHVAC:PackagedTerminalAirConditioner" or iddname == "OS:ZoneHVAC:PackagedTerminalHeatPump"
        ):

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 10
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={10})
            targetIdf.addObject(newObject)

        elif iddname == "OS:ZoneHVAC:WaterToAirHeatPump":

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 9
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={9})
            targetIdf.addObject(newObject)

        elif iddname == "OS:AirLoopHVAC:UnitarySystem":

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 35
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={35})
            targetIdf.addObject(newObject)

        elif iddname == "OS:People:Definition":

            # 1 Key has been changed from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Mean Radiant Temperature Calculation Type * 10
            #   * ZoneAveraged -> EnclosureAveraged
            copy_object_as_is(obj=obj, newObject=newObject)
            if value := obj.getString(10):
                value = value.get()
                value = 'ZoneAveraged' if value == 'EnclosureAveraged' else value
                newObject.setString(10, value)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Schedule:Day":

            # 1 Field has been modified from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Interpolate to Timestep * 3 - Changed from bool to string choice
            copy_object_as_is(obj=obj, newObject=newObject)
            if value := obj.getString(3):
                value = value.get()
                value = 'Yes' if value not in ('No', '') else value
                newObject.setString(3, value)
            targetIdf.addObject(newObject)

        else:
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

    return targetIdf
