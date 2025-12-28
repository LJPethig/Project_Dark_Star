# models/security_panel.py
from enum import Enum

class SecurityLevel(Enum):
    NONE = 0
    LOW_SEC_KEYCARD_ONLY = 1
    HIGH_SEC_KEYCARD_ONLY = 2
    HIGH_SEC_KEYCARD_PIN = 3

class SecurityPanel:
    def __init__(self, panel_id: str, door_id: str, security_level: int, side: str):
        self.panel_id = panel_id
        self.door_id = door_id
        self.side = side  # e.g., "sub corridor" or "cargo bay"
        self.security_level = SecurityLevel(security_level)
        self.is_broken = False
        self.repair_progress = 0.0  # 0.0 to 1.0

    def attempt_unlock(self, player_inventory: list[str], pin_input: str | None = None) -> tuple[bool, str]:
        """Attempt to unlock the door using this panel."""
        if self.is_broken:
            return False, f"The panel on this side is damaged."

        # Check required items
        required_keycard = self.security_level in [SecurityLevel.LOW_SEC_KEYCARD_ONLY, SecurityLevel.HIGH_SEC_KEYCARD_ONLY, SecurityLevel.HIGH_SEC_KEYCARD_PIN]
        if required_keycard and not any(card in player_inventory for card in ["id_card_low_sec", "id_card_high_sec"]):
            return False, "You need an ID card to swipe."

        # Check PIN if required
        required_pin = self.security_level in [SecurityLevel.HIGH_SEC_KEYCARD_PIN]
        if required_pin and pin_input != "1234":  # Placeholder PIN - replace with actual logic
            return False, "Incorrect PIN."

        # Check for Success - unlock the door
        if self.security_level == SecurityLevel.LOW_SEC_KEYCARD_ONLY:
            return True, "Access granted. The door unlocks."
        elif self.security_level == SecurityLevel.HIGH_SEC_KEYCARD_ONLY:
            if "id_card_high_sec" in player_inventory:
                return True, "Access granted. The door unlocks."
            else:
                return False, "Access denied. Incorrect security card"

    def attempt_lock(self, player_inventory: list[str]) -> tuple[bool, str]:
        """Attempt to lock the door using this panel."""
        if self.is_broken:
            return False, f"The panel on this side is damaged."

        # Same check as unlock for now (ID card required)
        required_keycard = self.security_level in [SecurityLevel.LOW_SEC_KEYCARD_ONLY, SecurityLevel.HIGH_SEC_KEYCARD_ONLY, SecurityLevel.HIGH_SEC_KEYCARD_PIN]
        if required_keycard and not any(card in player_inventory for card in ["id_card_low_sec", "id_card_high_sec"]):
            return False, "You need a valid ID card to swipe."

        # Check for Success - lock the door
        if self.security_level == SecurityLevel.LOW_SEC_KEYCARD_ONLY:
            return True, "Access granted. The door locks."
        elif self.security_level == SecurityLevel.HIGH_SEC_KEYCARD_ONLY:
            if "id_card_high_sec" in player_inventory:
                return True, "Access granted. The door locks."
            else:
                return False, "Access denied. Incorrect security card"

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