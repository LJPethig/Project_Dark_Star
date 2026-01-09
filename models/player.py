# models/player.py
from typing import Dict, List, Optional, Tuple
from models.interactable import PortableItem
from constants import PLAYER_NAME


class Player:
    """Player character with inventory, equipped items, and carry capacity."""

    def __init__(self, name: str = PLAYER_NAME):
        self.name = name
        self._inventory: List[PortableItem] = []
        self.equipped: Dict[str, Optional[PortableItem]] = {
            "body": None,
            "torso": None,
            "waist": None,
            "feet": None,
            "head": None,
        }
        self.max_carry_mass: float = 10.0


    @property
    def current_carry_mass(self) -> float:
        """Mass of loose (unequipped) items only. Equipped items don't count against carry limit."""
        return sum(item.mass for item in self._inventory)

    def get_inventory(self) -> List[PortableItem]:
        """Return copy of loose (unequipped) inventory."""
        return self._inventory.copy()

    def add_to_inventory(self, item: PortableItem) -> Tuple[bool, str]:
        """Add item to loose inventory with mass check."""
        if not isinstance(item, PortableItem):
            return False, "You can't carry that."

        mass = getattr(item, "mass", 0.0)
        new_total = self.current_carry_mass + mass  # ← uses property, no direct var
        if new_total > self.max_carry_mass:
            remaining = self.max_carry_mass - self.current_carry_mass
            return False, f"Too heavy! You can carry {remaining:.1f} kg more."

        self._inventory.append(item)
        # NO direct update needed — property recalculates automatically
        return True, f"You take the {item.name}."

    def remove_from_inventory(self, item: PortableItem) -> bool:
        """Remove from loose inventory."""
        if item in self._inventory:
            self._inventory.remove(item)
            # NO direct update needed — property recalculates
            return True
        return False

    def equip(self, item: PortableItem) -> Tuple[bool, str]:
        """Equip item in its slot, auto-unequip old if needed."""
        if not hasattr(item, "equip_slot") or item.equip_slot not in self.equipped:
            return False, f"Cannot equip {item.name} — invalid slot."

        slot = item.equip_slot

        # Auto-unequip old item
        old = self.equipped[slot]
        if old:
            success = self.add_to_inventory(old)
            if not success:
                return False, f"Cannot unequip {old.name} — inventory too full/heavy."

        # Remove from loose inventory (if present)
        self.remove_from_inventory(item)

        self.equipped[slot] = item
        return True, f"You equip the {item.name}."

    def unequip(self, slot: str) -> Tuple[bool, str]:
        """Unequip from slot and return to inventory."""
        if slot not in self.equipped:
            return False, f"Invalid slot: {slot}"

        item = self.equipped[slot]
        if item is None:
            return False, f"Nothing equipped in {slot}."

        success, msg = self.add_to_inventory(item)
        if success:
            self.equipped[slot] = None
            return True, f"You remove the {item.name}."
        return False, f"Cannot unequip {item.name}: {msg}"

    def get_equipped_summary(self) -> str:
        """Formatted equipped items for UI/description."""
        lines = [f"{slot.capitalize()}: {item.name if item else 'nothing'}"
                 for slot, item in self.equipped.items()]
        return "\n".join(lines)