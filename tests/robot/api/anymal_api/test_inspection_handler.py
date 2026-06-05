from pathlib import Path
from unittest.mock import Mock

import pytest
from alitra import Frame, Position
from pytest_mock import MockerFixture
from requests import Response

from isar_anymal.robot.api.anymal_api.models import InspectionEventDto
from isar_anymal.robot.api.anymal_api.server_sent_event_handlers.inspection_handler import (
    _process_acoustic_inspection,
)
from isar_anymal.robot.api.request_handler import RequestHandler
from robot_interface.models.inspection.inspection import AcousticMeasurement

from tests.robot.utilities import build_acoustic_task, default_robot_pose


@pytest.mark.requires_private_test_data
def test_process_acoustic_inspection(mocker: MockerFixture) -> None:
    test_data_dir: Path = Path(__file__).parent.parent.parent / "test_data"
    fixture_path: str = str(test_data_dir / "inspection_acoustic_event_example.json")
    with open(fixture_path, "r") as f:
        event: InspectionEventDto = InspectionEventDto.model_validate_json(f.read())

    listing_response: Mock = Mock(spec=Response)
    listing_response.json.return_value = {
        "totalItems": 1,
        "items": [{"inspection": {"filename": "acoustic.mp4"}}],
    }
    raw_data_response: Mock = Mock(spec=Response)
    raw_data_response.content = b"\x00\x01\x02"
    raw_data_response.headers = {"content-type": "video/mp4"}

    request_handler: Mock = Mock(spec=RequestHandler)
    request_handler.get = Mock(side_effect=[listing_response, raw_data_response])

    inspection: AcousticMeasurement = _process_acoustic_inspection(
        event=event,
        request_handler=request_handler,
        robot_pose=default_robot_pose(),
        target_position=Position(x=0, y=0, z=0, frame=Frame("asset")),
        task=build_acoustic_task(),
    )

    assert inspection.metadata.leak_rate == pytest.approx(0.5505, rel=1e-3)
    assert inspection.metadata.result == "RI_ANOMALY"
    assert inspection.metadata.frequency_from == 35000
