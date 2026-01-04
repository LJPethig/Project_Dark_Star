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

from typing import List, Optional


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

    def matches(self, word: str) -> bool:
        """Check if player input matches this object's keywords."""
        return word.lower() in [k.lower() for k in self.keywords]

    def on_examine(self) -> str:
        """Default examine behavior (can be overridden in subclasses)."""
        return self.examine_text or f"You see nothing special about the {self.name}."

    def on_use(self) -> str:
        """Default use behavior (can be overridden)."""
        return f"You can't use {self.name}."


class PortableItem(Interactable):
    """
    Items that can be taken, carried, equipped, and modified during play.
    Mutable state will be added on-demand as mechanics require it
    (e.g., durability for tools, O2 for EVA suit, schematics for scan tool).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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