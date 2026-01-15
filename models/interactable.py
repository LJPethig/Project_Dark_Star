# models/interactable.py
"""
Interactable Object Hierarchy — Current and Planned

This module defines the core object system for Project Dark Star.
All game objects (tools, suits, terminals, panels, etc.) are instances with:
  • Identity and description
  • Mutable runtime state
  • Extensible behavior via methods

Current implemented structure:
    Interactable
    ├── PortableItem      ← mass, equip_slot, durability, condition, O2, schematics, etc.
    └── FixedObject       ← powered, accessed_by, tamper_count, etc.

Planned future evolution:
    FixedObject
    └── Terminal                  ← Shared terminal features: login, session, credentials
        ├── MedicalTerminal
        ├── StorageTerminal
        ├── NavigationTerminal
        ├── PersonalTerminal
        └── ... (EngineeringTerminal, SecurityTerminal, etc.)

Benefits of this design:
  • Clean separation between portable and fixed objects
  • Shared terminal behavior without duplication
  • Easy addition of specialized terminals or tool subtypes
  • Full runtime state persistence on live instances (critical for durability, O2, schematics, login state)

The switch from dataclasses to proper classes enables true object identity and mutable state
— essential for deep mechanics while keeping current behavior 100% intact.
"""

from typing import List, Optional, Any


class Interactable:
    """Base class for all objects the player can interact with in rooms."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        examine_text: str = "",
        keywords: Optional[List[str]] = None,
        **extra_fields,  # Capture any additional JSON fields (mass, equip_slot, etc.)
    ):
        self.id = id
        self.name = name
        self.description = description
        self.examine_text = examine_text or description
        self.keywords = keywords or [name.lower()]

        # Store any extra fields passed from JSON (e.g., mass, equip_slot)
        self.__dict__.update(extra_fields)

    def matches(self, input_str: str) -> bool:
        """Return True if input_str exactly matches any keyword (case-insensitive).
            Keywords are checked longest-first at match time to favor more specific phrases
            when multiple objects share shorter common keywords (e.g., 'storage')."""
        input_lower = input_str.lower()
        # Sort keywords at match time: longest and most specific first
        sorted_keywords = sorted(self.keywords, key=lambda k: (-len(k), k.lower()))
        for kw in sorted_keywords:
            if input_lower == kw.lower():
                return True
        return False

    def on_examine(self) -> str:
        """Default examine behavior (can be overridden in subclasses)."""
        return self.description or f"You see nothing special about the {self.name}."

    def on_use(self) -> str:
        """Default use behavior (can be overridden)."""
        return f"You can't use {self.name}."


class PortableItem(Interactable):
    """
    Items that can be taken, carried, equipped, etc.
    Common dynamic fields are now declared here for static type checking and IDE support.
    Defaults are placeholders only — real values from JSON override them via __dict__.update(kwargs).
    """

    mass: float = 0.0
    equip_slot: Optional[str] = None
    # Future common fields go here (e.g. condition: float = 1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs) # ← JSON values override defaults above

        # Core portable flag — can be overridden via JSON if needed
        self.takeable: bool = True

        # Future mutable state will be added here via targeted initialization
        # in _place_portable_items() or specific item handlers.
        # Examples (to be added later):
        # - self.durability = 100.0
        # - self.o2_current = 0.0
        # - self.loaded_schematics = []


class FixedObject(Interactable):
    """
    Objects permanently attached to a room (terminals, control panels, etc.).
    Mutable state will be added on-demand (e.g., powered, session_active).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Core fixed flag
        self.takeable: bool = False

        # Future state will be added here as needed
        # Examples (to be added later):
        # - self.powered = True
        # - self.current_user = None
        # - self.tamper_count = 0

class StorageUnit(FixedObject):
    """
    A fixed storage unit (locker, cabinet, rack) that can hold PortableItem instances.
    Supports open/close state and mass-based capacity.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Runtime state — only what we use now
        self.contents: List[PortableItem] = []          # Items currently inside
        self.is_open: bool = False                      # Open/closed state
        self.capacity_mass: float = kwargs.get("capacity_mass", 100.0)

        # Current total mass of contents (updated on add/remove)
        self.current_mass: float = 0.0

    def can_add_item(self, item: PortableItem) -> bool:
        """Check if an item can fit by mass."""
        item_mass = getattr(item, "mass", 0.0)
        return (self.current_mass + item_mass) <= self.capacity_mass

    def add_item(self, item: PortableItem) -> bool:
        """Add an item if capacity allows. Returns success."""
        if not self.can_add_item(item):
            return False
        self.contents.append(item)
        self.current_mass += getattr(item, "mass", 0.0)
        return True

    def remove_item(self, item: PortableItem) -> bool:
        """Remove an item if present. Returns success."""
        if item in self.contents:
            self.contents.remove(item)
            self.current_mass -= getattr(item, "mass", 0.0)
            return True
        return False

    def get_contents_list(self) -> str:
        """Return a formatted string of contents for look in / examine."""
        if not self.contents:
            return "It is empty."

        item_names = [item.name for item in self.contents]
        if len(item_names) == 1:
            return item_names[0]
        elif len(item_names) == 2:
            return f"{item_names[0]} and {item_names[1]}"
        else:
            return ", ".join(item_names[:-1]) + f", and {item_names[-1]}"

    def get_description_string(self) -> str:
        """Return formatted string for room description: name + state + contents."""
        if not self.is_open:
            return f"%{self.name}%"

        state = " (open)"
        if not self.contents:
            contents_str = ": empty"
        else:
            item_names = [f"^{item.name}^" for item in self.contents]  # ← CHANGED: ^ for portables
            if len(item_names) == 1:
                contents_str = f": {item_names[0]}"
            elif len(item_names) == 2:
                contents_str = f": {item_names[0]} and {item_names[1]}"
            else:
                contents_str = f": {', '.join(item_names[:-1])}, and {item_names[-1]}"

        return f"%{self.name}%{state}{contents_str}"

class UtilityBelt(PortableItem):
    """
    Wearable belt that can have small devices (e.g. PAM) clipped/attached to it.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # List of attached portable devices (PAM to start, room for future attachments)
        self.attached_pam: bool = False