# models/life_support.py
from typing import Dict
from models.ship import Ship
from models.room import Room
from constants import (
    SHIP_VOLUME_M3,
    DEFAULT_CREW_COUNT,
    HUMAN_O2_CONSUMPTION_M3_PER_MIN,
    HUMAN_CO2_PRODUCTION_M3_PER_MIN,
    CO2_SCRUBBER_EFFICIENCY,
    OXYGEN_GENERATOR_EFFICIENCY,
    THERMAL_CONTROL_EFFICIENCY,
)
import random


class LifeSupport:
    """
    Central simulation for ship atmosphere and life support.
    MVP: global values + basic components + time advance with temp drift.
    PAM reads local (initially global) values.
    """

    def __init__(self, ship: Ship):
        self.ship = ship
        self.ship_volume_m3 = SHIP_VOLUME_M3

        # Volume-scaled per-minute rates (human consumption in m³/min, converted to mmHg drop at 1 atm = 760 mmHg)
        o2_consumed_m3_per_min = HUMAN_O2_CONSUMPTION_M3_PER_MIN * DEFAULT_CREW_COUNT
        co2_produced_m3_per_min = HUMAN_CO2_PRODUCTION_M3_PER_MIN * DEFAULT_CREW_COUNT

        self.ppo2_drop_per_min = (o2_consumed_m3_per_min / self.ship_volume_m3) * 760
        self.ppco2_rise_per_min = (co2_produced_m3_per_min / self.ship_volume_m3) * 760

        # Global baselines (nominal ship-wide)
        self.global_pressure_psi: float = 14.7
        self.global_temperature_c: float = 20.0  # average fallback
        self.global_ppo2_mmhg: float = 150.0
        self.global_ppco2_mmhg: float = 2.5

        # Components (dumb for MVP — efficiency 0.0–1.0)
        self.co2_scrubber = {"efficiency": CO2_SCRUBBER_EFFICIENCY}
        self.oxygen_generator = {"efficiency": OXYGEN_GENERATOR_EFFICIENCY}
        self.thermal_control = {"efficiency": THERMAL_CONTROL_EFFICIENCY}

        # Per-room current temp (init to target with realistic variation)
        for room in self.ship.rooms.values():
            # Add random initial variation ±0.5 °C
            room.current_temperature = random.uniform(room.target_temperature - 0.5, room.target_temperature + 0.5)

        # Debug initial values (remove later)
        print(
            f"Initial state | "
            f"Captains quarters temp: {self.ship.rooms['captains quarters'].current_temperature:.2f} °C | "
            f"Pressure: {self.global_pressure_psi:.2f} psi | "
            f"ppO₂: {self.global_ppo2_mmhg:.2f} mmHg | "
            f"ppCO₂: {self.global_ppco2_mmhg:.2f} mmHg | "
            f"Air Quality: {self.air_quality_percent:.2f}%"
        )

    @property
    def air_quality_percent(self) -> float:
        """Simple MVP composite: 100 - penalties."""
        o2_penalty = max(0, (150 - self.global_ppo2_mmhg) * 0.5)
        co2_penalty = max(0, (self.global_ppco2_mmhg - 3) * 10)
        return max(0, min(100, 100 - o2_penalty - co2_penalty))

    def get_current_values(self, room: Room) -> Dict[str, float]:
        """Return env values for a room (PAM/event readout)."""
        # MVP: global pressure/O2/CO2, local temp
        return {
            "pressure_psi": self.global_pressure_psi,
            "temperature_c": room.current_temperature,
            "ppO2": self.global_ppo2_mmhg,
            "ppCO2": self.global_ppco2_mmhg,
            "air_quality": self.air_quality_percent,
        }

    def advance_time(self, minutes: int):
        """Advance simulation by given minutes, looping per minute (capped at 180 days)."""
        MAX_MINUTES_PER_STEP = 259200
        effective_minutes = min(minutes, MAX_MINUTES_PER_STEP)

        eff = self.thermal_control["efficiency"]

        # Pre-calculate total passive loss for the entire time step (vectorized, no per-minute loop for temp)
        if eff < 1.0:
            if eff >= 0.2 and eff <= 0.9:
                total_loss = effective_minutes * 0.00008 * (1 - eff)
            elif eff == 0.1:
                total_loss = effective_minutes * 0.00009 * (1 - eff)
            elif eff == 0.0:
                total_loss = effective_minutes * 0.0003 * (1 - eff)
            else:
                total_loss = 0.0

            for room in self.ship.rooms.values():
                room.current_temperature -= total_loss

        # Gas simulation (unchanged per-minute loop)
        for _ in range(effective_minutes):
            self.global_ppco2_mmhg += self.ppco2_rise_per_min * (1 - self.co2_scrubber["efficiency"])
            self.global_ppo2_mmhg -= self.ppo2_drop_per_min * (1 - self.oxygen_generator["efficiency"])

        # Final variation applied to all results
        fluctuation = random.uniform(-0.5, 0.5)
        for room in self.ship.rooms.values():
            room.current_temperature += fluctuation

        # Clamp gases
        self.global_ppo2_mmhg = max(0, self.global_ppo2_mmhg)
        self.global_ppco2_mmhg = max(0, self.global_ppco2_mmhg)

        # Debug print (unchanged)
        print(
            f"Time +{minutes} min | "
            f"Captains quarters temp: {self.ship.rooms['captains quarters'].current_temperature:.2f} °C | "
            f"Pressure: {self.global_pressure_psi:.2f} psi | "
            f"ppO₂: {self.global_ppo2_mmhg:.2f} mmHg | "
            f"ppCO₂: {self.global_ppco2_mmhg:.2f} mmHg | "
            f"Air Quality: {self.air_quality_percent:.2f}%"
        )

