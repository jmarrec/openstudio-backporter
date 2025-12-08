import openstudio


def get_objects_by_type(idf_file: openstudio.IdfFile, idd_object_type_name: str) -> list[openstudio.IdfObject]:
    """Similar to workspace.getObjectsByType, but for IdfFile with an older Version.

    In an older version, the IddFile being not the current version, every object is label UserCustom except version.
    """
    return [obj for obj in idf_file.objects() if obj.iddObject().name() == idd_object_type_name]


def brief_description(idf_obj: openstudio.IdfObject) -> str:
    """Get a brief description of the IdfObject."""
    return f"{idf_obj.iddObject().name()} '{idf_obj.nameString()}'"


def get_target(idf_file: openstudio.IdfFile, idf_obj: openstudio.IdfObject, index: int) -> openstudio.OptionalIdfObject:
    """Get the target object for the Inlet Air Mixer Schedule."""
    # Can't call getTarget, this is not a Workspace
    handle_ = idf_obj.getString(index)
    if not handle_.is_initialized():
        print(f"For {brief_description(idf_obj=idf_obj)}, String at index {index} is not initialized.")
        return openstudio.OptionalIdfObject()

    return idf_file.getObject(openstudio.toUUID(handle_.get()))
