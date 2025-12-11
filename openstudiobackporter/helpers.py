import openstudio


def get_objects_by_type(idf_file: openstudio.IdfFile, idd_object_type_name: str) -> list[openstudio.IdfObject]:
    """Similar to workspace.getObjectsByType, but for IdfFile with an older Version.

    In an older version, the IddFile being not the current version, every object is label UserCustom except version.
    """
    return [obj for obj in idf_file.objects() if obj.iddObject().name() == idd_object_type_name]


def brief_description(idf_obj: openstudio.IdfObject) -> str:
    """Get a brief description of the IdfObject."""
    if (name_ := idf_obj.name()).is_initialized():
        return f"{idf_obj.iddObject().name()} '{name_}'"
    else:
        return f"{idf_obj.iddObject().name()}"


def get_target(idf_file: openstudio.IdfFile, idf_obj: openstudio.IdfObject, index: int) -> openstudio.OptionalIdfObject:
    """Get the target object for the Inlet Air Mixer Schedule."""
    # Can't call getTarget, this is not a Workspace
    handle_: openstudio.OptionalString = idf_obj.getString(index, returnDefault=False, returnUninitializedEmpty=True)
    if not handle_.is_initialized():
        print(f"For {brief_description(idf_obj=idf_obj)}, String at index {index} is not initialized.")
        return openstudio.OptionalIdfObject()

    handle_str = handle_.get()

    # m_handle isn't being set properly until you reload the model, so we have to look it up ourselves
    for x in idf_file.objects():
        if x.getString(0).value_or('') == handle_str:
            return openstudio.OptionalIdfObject(x)

    return openstudio.OptionalIdfObject()


def copy_object_as_is(obj: openstudio.IdfObject, newObject: openstudio.IdfObject) -> None:
    """Copy an IdfObject as is.

    Even though the object didn't change, the IddObject might have changed field names or memo, etc.

    Args:
    -----
    * obj: (openstudio.IdfObject) (float): The source IdfObject, from the newer version
    * newObject: (openstudio.IdfObject) The target IdfObject, from the older version
    """
    for i in range(obj.numFields()):
        if value := obj.getString(i):
            newObject.setString(i, value.get())


def copy_with_deleted_fields(
    obj: openstudio.IdfObject, newObject: openstudio.IdfObject, skip_indices: set[int]
) -> None:
    """Copy an IdfObject while skipping certain field indices.

    Args:
    -----
    * obj: (openstudio.IdfObject) (float): The source IdfObject, from the newer version
    * newObject: (openstudio.IdfObject) The target IdfObject, from the older version
    * skip_indices: (set[int]) The set of field indices to skip (0-indexed)
    """

    offset = 0
    for i in range(obj.numFields()):
        if i in skip_indices:
            offset += 1
            continue
        if value := obj.getString(i):
            newObject.setString(i - offset, value.get())


def copy_with_cutoff_fields(obj: openstudio.IdfObject, newObject: openstudio.IdfObject, cutoff_index: int) -> None:
    """Copy an IdfObject while skipping fields from a certain index onward.

    Args:
    -----
    * obj: (openstudio.IdfObject) (float): The source IdfObject, from the newer version
    * newObject: (openstudio.IdfObject) The target IdfObject, from the older version
    * cutoff_index: (int) The index from which to stop copying fields (0-indexed)
    """
    for i in range(obj.numFields()):
        if i >= cutoff_index:
            break
        if value := obj.getString(i):
            newObject.setString(i, value.get())
