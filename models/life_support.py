# models/life_support.py
from typing import Dict
from models.ship import Ship
from models.room import Room
from constants import (
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
        self.ship_volume_m3 = sum(room.volume_m3 for room in self.ship.rooms.values())
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
        """Advance simulation by given minutes"""
        minutes = int(minutes)  # ensure integer (optional safety)

        eff = self.thermal_control["efficiency"]

        if eff < 1.0:
            # Global heat loss rate per minute (quadratic inefficiency scaling)
            loss_per_minute = 10.0e-5 * (1 - eff) ** 2
            total_loss = minutes * loss_per_minute

            # Per-room thermal mass variation: larger rooms cool slower
            # Normalized so ship-wide average temperature drop matches uniform case
            avg_volume = self.ship_volume_m3 / len(self.ship.rooms)

            # Precompute raw factors and their volume-weighted sum
            raw_factors = {}
            weighted_sum = 0.0
            for room in self.ship.rooms.values():
                raw_factor = (avg_volume / room.volume_m3) ** 0.15
                raw_factors[room.id] = raw_factor
                weighted_sum += raw_factor * room.volume_m3

            # Normalization ensures weighted average factor = 1.0
            normalization = self.ship_volume_m3 / weighted_sum

            # Apply normalized loss to each room
            for room in self.ship.rooms.values():
                factor = raw_factors[room.id] * normalization
                room.current_temperature -= total_loss * factor

            # Apply efficiency-dependent fluctuation (global)
            if eff >= 0.7:
                fluctuation = random.uniform(-0.5, 0.5)
            elif 0.3 <= eff <= 0.6:
                fluctuation = random.uniform(-0.8, 0.2)
            else:
                fluctuation = random.uniform(-1.5, 0.0)

            for room in self.ship.rooms.values():
                room.current_temperature += fluctuation

        # Gas simulation (vectorized)
        co2_eff = self.co2_scrubber["efficiency"]
        o2_eff = self.oxygen_generator["efficiency"]

        self.global_ppco2_mmhg += minutes * self.ppco2_rise_per_min * (1 - co2_eff)
        self.global_ppo2_mmhg -= minutes * self.ppo2_drop_per_min * (1 - o2_eff)

        # Clamp partial pressures
        self.global_ppo2_mmhg = max(0.0, self.global_ppo2_mmhg)
        self.global_ppco2_mmhg = max(0.0, self.global_ppco2_mmhg)

    def test_life_support(self):
        """Baseline test: simulate time jumps for each efficiency level.
        All components (thermal, CO₂ scrubber, O₂ generator) use the same efficiency.
        Each level starts from identical initial state."""
        print("=== Life Support Baseline Test (global logic, SHIP_VOLUME_M3=550) ===")
        print("Time jumps: 1, 7, 14, 30, 60, 90, 180, 360 days (cumulative per efficiency)")
        print("All efficiencies (thermal, CO₂, O₂) set to same value per run")
        print("Each efficiency level starts from the same initial global state.\n")

        time_jumps_days = [1, 7, 14, 30, 60, 90, 180, 360]
        efficiencies = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]

        original_eff = {
            "thermal": self.thermal_control["efficiency"],
            "co2": self.co2_scrubber["efficiency"],
            "o2": self.oxygen_generator["efficiency"],
        }

        initial_temps = {room.id: room.current_temperature for room in self.ship.rooms.values()}
        initial_globals = {
            'ppo2': self.global_ppo2_mmhg,
            'ppco2': self.global_ppco2_mmhg,
            'pressure': self.global_pressure_psi
        }

        for eff in efficiencies:
            print(f"\nEfficiency: {eff:.1f} (thermal, CO₂ scrubber, O₂ generator)")

            self.thermal_control["efficiency"] = eff
            self.co2_scrubber["efficiency"] = eff
            self.oxygen_generator["efficiency"] = eff

            for room in self.ship.rooms.values():
                room.current_temperature = initial_temps[room.id]
            self.global_ppo2_mmhg = initial_globals['ppo2']
            self.global_ppco2_mmhg = initial_globals['ppco2']
            self.global_pressure_psi = initial_globals['pressure']

            print("  Initial:")
            self._print_current_state()

            cumulative_days = 0
            for days in time_jumps_days:
                cumulative_days += days
                minutes = days * 1440
                self.advance_time(minutes)
                print(f"  After +{cumulative_days} days total:")
                self._print_current_state()

        self.thermal_control["efficiency"] = original_eff["thermal"]
        self.co2_scrubber["efficiency"] = original_eff["co2"]
        self.oxygen_generator["efficiency"] = original_eff["o2"]

        print("Test complete. Efficiency restored.")


    def _print_current_state(self):
        """Print current per-room temperatures and global gases/pressure, sorted by room id."""
        rooms_sorted = sorted(self.ship.rooms.values(), key=lambda r: r.id)
        print("  Room                  Temp     ppO₂     ppCO₂    Pressure")
        print("  -------------------- -------- -------- -------- --------")
        for room in rooms_sorted:
            print(f"    {room.id:20} {room.current_temperature:5.2f}   "
                  f"{self.global_ppo2_mmhg:6.2f}   "
                  f"{self.global_ppco2_mmhg:6.2f}   "
                  f"{self.global_pressure_psi:6.2f}")