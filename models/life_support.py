# models/life_support.py
from typing import Dict
from models.ship import Ship
from models.room import Room
from constants import SHIP_VOLUME_M3
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
        o2_consumed_m3_per_min = 0.00058  # ~0.84 m³/day per person / 1440 min
        co2_produced_m3_per_min = 0.00049  # ~0.7 m³/day per person / 1440 min

        self.ppo2_drop_per_min = (o2_consumed_m3_per_min / self.ship_volume_m3) * 760
        self.ppco2_rise_per_min = (co2_produced_m3_per_min / self.ship_volume_m3) * 760

        # Global baselines (nominal ship-wide)
        self.global_pressure_psi: float = 14.7
        self.global_temperature_c: float = 20.0  # average fallback
        self.global_ppo2_mmhg: float = 150.0
        self.global_ppco2_mmhg: float = 2.5

        # Components (dumb for MVP — efficiency 0.0–1.0)
        # set to 0.0 for testing - essentially life support is off.
        self.co2_scrubber = {"efficiency": 0.0}
        self.oxygen_generator = {"efficiency": 0.0}
        self.thermal_control = {"efficiency": 0.0}

        # Per-room current temp (init to target, will drift)
        for room in self.ship.rooms.values():
            room.current_temperature = room.target_temperature
            # Add random initial drift (±1.0 °C for MVP)
            drift_range = 1.0
            room.current_temperature += random.uniform(-drift_range, drift_range)

        # Debug initial values (remove later)
        print(
            f"Initial state | "
            f"Crew quarters temp: {self.ship.rooms['crew quarters'].current_temperature:.2f} °C | "
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
            "air_quality": self.air_quality_percent,
        }


    def advance_time(self, minutes: int):
        """Advance simulation by given minutes, looping per minute (capped at 72 hours)."""
        MAX_MINUTES_PER_STEP = 259200  # Realistic life support calculations for up to 180 days of time advance

        # Cap the loop to prevent huge jumps from freezing (rare for MVP)
        effective_minutes = min(minutes, MAX_MINUTES_PER_STEP)


        for _ in range(effective_minutes):
            # Metabolic + correction
            self.global_ppco2_mmhg += self.ppco2_rise_per_min * (1 - self.co2_scrubber["efficiency"])
            self.global_ppo2_mmhg -= self.ppo2_drop_per_min * (1 - self.oxygen_generator["efficiency"])

            # Temp drift
            for room in self.ship.rooms.values():
                current = room.current_temperature
                target = room.target_temperature

                # Active thermal correction only functions when efficiency is high enough (≥ 80%)
                if self.thermal_control["efficiency"] >= 0.8:
                    drift_rate_per_min = 0.005  # full healthy-system correction rate
                    room.current_temperature += (target - current) * drift_rate_per_min

                # Passive heat loss always occurs (even when correction is active)
                room.current_temperature -= 0.001 * (1 - self.thermal_control["efficiency"])

        # Clamp
        self.global_ppo2_mmhg = max(0, self.global_ppo2_mmhg)
        self.global_ppco2_mmhg = max(0, self.global_ppco2_mmhg)

        # Debug (remove later)
        print(
            f"Time +{minutes} min | "
            f"Crew quarters temp: {self.ship.rooms['crew quarters'].current_temperature:.2f} °C | "
            f"Pressure: {self.global_pressure_psi:.2f} psi | "
            f"ppO₂: {self.global_ppo2_mmhg:.2f} mmHg | "
            f"ppCO₂: {self.global_ppco2_mmhg:.2f} mmHg | "
            f"Air Quality: {self.air_quality_percent:.2f}%"
        )