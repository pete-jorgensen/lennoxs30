# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.helpers import helper_create_system_unique_id
from custom_components.lennoxs30.sensor import (
    SYSTEM_ATTRIBUTE_SENSORS,
    S30SystemAttributeSensor,
)
from tests.conftest import conftest_base_entity_availability


def _descriptor(attr: str) -> dict:
    return next(d for d in SYSTEM_ATTRIBUTE_SENSORS if d["attr"] == attr)


@pytest.mark.asyncio()
async def test_system_ventilation_remaining_time_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    system.ventilationRemainingTime = 600
    s = S30SystemAttributeSensor(hass, manager, system, _descriptor("ventilationRemainingTime"))
    await s.async_added_to_hass()

    assert s.unique_id == helper_create_system_unique_id(system, "_VRT")
    assert s.name == system.name + "_ventilation_remaining_time"
    assert s.native_value == 600
    assert s.native_unit_of_measurement == UnitOfTime.MINUTES
    assert s.device_class == SensorDeviceClass.DURATION
    assert s.state_class == SensorStateClass.MEASUREMENT
    assert s.entity_category is None
    assert len(s.extra_state_attributes) == 0

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    conftest_base_entity_availability(manager, system, s)


@pytest.mark.asyncio()
async def test_system_active_alerts_count_sensor_and_callback(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    system.alerts_num_in_active_array = 0
    s = S30SystemAttributeSensor(hass, manager, system, _descriptor("alerts_num_in_active_array"))
    await s.async_added_to_hass()

    assert s.unique_id == helper_create_system_unique_id(system, "_ANA")
    assert s.native_value == 0
    assert s.state_class == SensorStateClass.MEASUREMENT
    assert s.entity_category == EntityCategory.DIAGNOSTIC

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        system.attr_updater({"numAlertsInActiveArray": 2}, "numAlertsInActiveArray", "alerts_num_in_active_array")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.native_value == 2


@pytest.mark.asyncio()
async def test_system_smart_away_state_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    system.sa_state = "enabled active"
    s = S30SystemAttributeSensor(hass, manager, system, _descriptor("sa_state"))

    assert s.unique_id == helper_create_system_unique_id(system, "_SAST")
    assert s.name == system.name + "_smart_away_state"
    assert s.native_value == "enabled active"
    assert s.native_unit_of_measurement is None
    assert s.device_class is None
    assert s.entity_category == EntityCategory.DIAGNOSTIC
