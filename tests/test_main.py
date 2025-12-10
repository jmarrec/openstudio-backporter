import shutil
import sys
from pathlib import Path

from openstudiobackporter.main import main


def test_main(monkeypatch, tmp_path: Path):
    ori_osm_path = Path(__file__).parent / "3_11_0/CoilAvailabilitySchedules_3_10_0.osm"
    assert ori_osm_path.is_file()

    osm_path = tmp_path / "test_model.osm"
    shutil.copy(ori_osm_path, osm_path)
    monkeypatch.setattr(sys, "argv", ["__main__.py", "--to-version", "3.8.0", str(osm_path)])
    main()
    backported_osm_path = tmp_path / "test_model_backported_to_3.8.0.osm"
    assert backported_osm_path.is_file()


def test_main_intermediate(monkeypatch, tmp_path: Path):
    ori_osm_path = Path(__file__).parent / "3_11_0/CoilAvailabilitySchedules_3_10_0.osm"
    assert ori_osm_path.is_file()

    osm_path = tmp_path / "test_model.osm"
    shutil.copy(ori_osm_path, osm_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["__main__.py", "--to-version", "3.8.0", "--save-intermediate", "--verbose", str(osm_path)],
    )
    main()
    for intermediate_version in ["3.9.0", "3.8.0"]:
        intermediate_osm_path = tmp_path / f"test_model_backported_to_{intermediate_version}.osm"
        assert intermediate_osm_path.is_file()
