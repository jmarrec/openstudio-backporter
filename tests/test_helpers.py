import openstudio

from openstudiobackporter import helpers


def test_get_objects_by_type():
    m = openstudio.model.Model()
    n_zones = 5
    for i in range(n_zones):
        zone = openstudio.model.ThermalZone(m)
        zone.setName(f"Zone {i + 1}")

    m.getBuilding()
    idf_file = m.toIdfFile()

    zones = helpers.get_objects_by_type(idf_file, "OS:ThermalZone")
    assert len(zones) == 5
    for i, zone in enumerate(zones, start=1):
        assert zone.nameString() == f"Zone {i}"


def test_brief_description():
    m = openstudio.model.Model()
    zone = openstudio.model.ThermalZone(m)
    zone.setName("Test Zone")
    idf_file = m.toIdfFile()
    idf_obj = helpers.get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ThermalZone")[0]
    description = helpers.brief_description(idf_obj)
    assert description == "OS:ThermalZone 'Test Zone'"

    # No name
    idf_obj = idf_file.versionObject().get()
    assert not idf_obj.name().is_initialized()
    description = helpers.brief_description(idf_obj)
    assert description == "OS:Version"


def test_get_target():
    m = openstudio.model.Model()

    zone = openstudio.model.ThermalZone(m)
    zone.setName("Test Zone")

    idf_file = m.toIdfFile()
    zone = helpers.get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ThermalZone")[0]
    assert not helpers.get_target(idf_file=idf_file, idf_obj=zone, index=2).is_initialized()  # Multiplier, empty
    sizing_zone = helpers.get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Sizing:Zone")[0]

    target_zone_ = helpers.get_target(idf_file=idf_file, idf_obj=sizing_zone, index=1)
    assert target_zone_.is_initialized()
    assert target_zone_.get() == zone

    # This is a string, but not a target
    assert not helpers.get_target(idf_file=idf_file, idf_obj=sizing_zone, index=2).is_initialized()
