# models/player.py
from typing import List, Optional, Tuple
from models.interactable import PortableItem
from constants import PLAYER_NAME


class Player:
    """Player character with inventory, equipped items, and carry capacity."""

    def __init__(self, name: str = PLAYER_NAME):
        self.name = name
        self._inventory: List[PortableItem] = []

        # Explicit, fixed slots — simple, debuggable, no dict overhead
        self.head_slot:  Optional[PortableItem] = None
        self.body_slot:  Optional[PortableItem] = None
        self.torso_slot: Optional[PortableItem] = None
        self.waist_slot: Optional[PortableItem] = None
        self.feet_slot:  Optional[PortableItem] = None

        self.max_carry_mass: float = 10.0

    @property
    def current_carry_mass(self) -> float:
        """Mass of loose (unequipped) items only."""
        return sum(item.mass for item in self._inventory)

    def get_inventory(self) -> List[PortableItem]:
        return self._inventory.copy()

    def add_to_inventory(self, item: PortableItem) -> Tuple[bool, str]:
        """Add item to loose inventory with mass check."""
        if self.current_carry_mass + item.mass > self.max_carry_mass:
            remaining = self.max_carry_mass - self.current_carry_mass
            return False, f"Too heavy! You can carry {remaining:.1f} kg more."

        self._inventory.append(item)
        return True, f"You take the {item.name}."

    def remove_from_inventory(self, item: PortableItem) -> bool:
        if item in self._inventory:
            self._inventory.remove(item)
            return True
        return False

    def equip(self, item: PortableItem) -> Tuple[bool, str]:
        """
        Equip an item in its designated slot.
        - Moves any old item in the slot back to loose inventory.
        - Returns (success, message) for feedback.
        """
        if not hasattr(item, "equip_slot"):
            return False, f"Cannot equip {item.name} — no equip slot defined."

        slot = item.equip_slot
        slot_attr = f"{slot}_slot"

        if not hasattr(self, slot_attr):
            return False, f"Invalid slot: {slot}"

        # Handle old item
        old_item = getattr(self, slot_attr)
        if old_item:
            success, msg = self.add_to_inventory(old_item)
            if not success:
                return False, f"Cannot unequip {old_item.name} — {msg}"

        # Equip new item
        setattr(self, slot_attr, item)

        # Remove from loose inventory if it was there
        self.remove_from_inventory(item)

        return True, f"You equip the {item.name}."