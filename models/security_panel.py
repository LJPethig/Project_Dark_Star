# models/security_panel.py
from enum import Enum

class SecurityLevel(Enum):
    NONE = 0
    KEYCARD_LOW = 1
    KEYCARD_HIGH = 2
    KEYCARD_HIGH_PIN = 3

class SecurityPanel:
    def __init__(self, panel_id: str, door_id: str, security_level: int, side: str):
        self.panel_id = panel_id
        self.door_id = door_id
        self.side = side
        self.security_level = SecurityLevel(security_level)
        self.is_broken = False
        self.repair_progress = 0.0

    def _check_keycard(self, player_inventory: list[str]) -> tuple[bool, str]:
        """Check if player has appropriate card."""
        has_low = "id_card_low_sec" in player_inventory
        has_high = "id_card_high_sec" in player_inventory

        if self.security_level == SecurityLevel.KEYCARD_LOW:
            if has_low or has_high:
                return True, ""
            return False, "Access denied: ID card required."

        elif self.security_level in [SecurityLevel.KEYCARD_HIGH, SecurityLevel.KEYCARD_HIGH_PIN]:
            if has_high:
                return True, ""
            return False, "Access denied: high-security clearance required."

        return False, "No valid ID card."

    def _check_pin(self, pin_input: str | None) -> tuple[bool, str]:
        """Check PIN for level 3."""
        if self.security_level != SecurityLevel.KEYCARD_HIGH_PIN:
            return True, ""
        if pin_input is None:
            return False, "PIN required."
        if pin_input != "1234":  # Placeholder - replace with actual logic
            return False, "Incorrect PIN."
        return True, ""

    def attempt_unlock(self, player_inventory: list[str]) -> tuple[bool, str]:
        """Attempt to unlock the door using this panel (card check only)."""
        if self.is_broken:
            return False, "The panel on this side is damaged."

        has_card, msg = self._check_keycard(player_inventory)
        if not has_card:
            return False, msg

        return True, "Access granted. The door unlocks."

    def attempt_lock(self, player_inventory: list[str]) -> tuple[bool, str]:
        """Attempt to lock the door using this panel (card check only)."""
        if self.is_broken:
            return False, "The panel on this side is damaged."

        has_card, msg = self._check_keycard(player_inventory)
        if not has_card:
            return False, msg

        return True, "Access granted. The door locks."

    def damage(self, amount: float = 1.0):
        """Damage the panel (for future events)."""
        self.is_broken = True
        self.repair_progress = 0.0

    def repair(self, amount: float):
        """Repair progress."""
        self.repair_progress += amount
        if self.repair_progress >= 1.0:
            self.is_broken = False
            self.repair_progress = 1.0