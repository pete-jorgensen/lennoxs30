# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from lennoxs30api.s30api_async import lennox_system, lennox_zone

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import (
    ZONE_ATTRIBUTE_SENSORS,
    S30ZoneAttributeSensor,
)
from tests.conftest import conftest_base_entity_availability


def _descriptor(attr: str) -> dict:
    return next(d for d in ZONE_ATTRIBUTE_SENSORS if d["attr"] == attr)


@pytest.mark.asyncio()
async def test_zone_damper_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.damper = 55
    s = S30ZoneAttributeSensor(hass, manager, system, zone, _descriptor("damper"))
    await s.async_added_to_hass()

    assert s.unique_id == (system.unique_id + "_" + str(zone.id)).replace("-", "") + "_DMP"
    assert s.name == system.name + "_" + zone.name + "_damper"
    assert s.native_value == 55
    assert s.native_unit_of_measurement == PERCENTAGE
    assert s.state_class == SensorStateClass.MEASUREMENT
    assert s.device_class is None
    assert s.entity_category is None
    assert len(s.extra_state_attributes) == 0

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id

    conftest_base_entity_availability(manager, system, s)


@pytest.mark.asyncio()
async def test_zone_balance_point_sensor_units(hass, manager: Manager):
    from homeassistant.components.sensor import SensorDeviceClass

    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.balancePoint = 35
    s = S30ZoneAttributeSensor(hass, manager, system, zone, _descriptor("balancePoint"))

    assert s.native_value == 35
    assert s.device_class == SensorDeviceClass.TEMPERATURE
    assert s.entity_category == EntityCategory.DIAGNOSTIC

    manager.is_metric = False
    assert s.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    manager.is_metric = True
    assert s.native_unit_of_measurement == UnitOfTemperature.CELSIUS


@pytest.mark.asyncio()
async def test_zone_temp_operation_sensor_and_callback(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.tempOperation = "off"
    s = S30ZoneAttributeSensor(hass, manager, system, zone, _descriptor("tempOperation"))
    await s.async_added_to_hass()

    assert s.name == system.name + "_" + zone.name + "_temp_operation"
    assert s.native_value == "off"
    assert s.native_unit_of_measurement is None
    assert s.state_class is None
    assert s.device_class is None
    assert s.entity_category == EntityCategory.DIAGNOSTIC

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"tempOperation": "heating"}, "tempOperation")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.native_value == "heating"
