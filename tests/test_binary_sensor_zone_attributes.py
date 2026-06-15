# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from lennoxs30api.s30api_async import lennox_system, lennox_zone

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.binary_sensor import (
    ZONE_BINARY_ATTRIBUTE_SENSORS,
    S30ZoneAttributeBinarySensor,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from tests.conftest import conftest_base_entity_availability


def _descriptor(attr: str) -> dict:
    return next(d for d in ZONE_BINARY_ATTRIBUTE_SENSORS if d["attr"] == attr)


@pytest.mark.asyncio()
async def test_zone_defrost_binary_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.defrost = True
    s = S30ZoneAttributeBinarySensor(hass, manager, system, zone, _descriptor("defrost"))
    await s.async_added_to_hass()

    assert s.unique_id == (system.unique_id + "_" + str(zone.id)).replace("-", "") + "_DEF"
    assert s.name == system.name + "_" + zone.name + "_defrost"
    assert s.is_on is True
    assert s.device_class == BinarySensorDeviceClass.RUNNING
    assert s.entity_category == EntityCategory.DIAGNOSTIC
    assert len(s.extra_state_attributes) == 0

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"defrost": False}, "defrost")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.is_on is False

    conftest_base_entity_availability(manager, system, s)


@pytest.mark.asyncio()
async def test_zone_fan_binary_sensor_not_diagnostic(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.fan = False
    s = S30ZoneAttributeBinarySensor(hass, manager, system, zone, _descriptor("fan"))

    assert s.unique_id == (system.unique_id + "_" + str(zone.id)).replace("-", "") + "_FANB"
    assert s.is_on is False
    assert s.device_class == BinarySensorDeviceClass.RUNNING
    assert s.entity_category is None


@pytest.mark.asyncio()
async def test_zone_heat_coast_binary_sensor_no_device_class(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    zone.heatCoast = False
    s = S30ZoneAttributeBinarySensor(hass, manager, system, zone, _descriptor("heatCoast"))

    assert s.name == system.name + "_" + zone.name + "_heat_coast"
    assert s.device_class is None
    assert s.entity_category == EntityCategory.DIAGNOSTIC
