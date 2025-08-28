# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

MAX_QUALITY = 50
MIN_QUALITY = 0


class Item:
    """
    Represents an item in the Gilded Rose inventory system.

    Each item has a name, sell_in value (days until expiration),
    and quality value (measure of item value).
    """

    def __init__(self, name: str, sell_in: int, quality: int) -> None:
        """
        Initialize an item.

        Args:
            name: The name of the item
            sell_in: Number of days until the item expires
            quality: The current quality/value of the item
        """
        self.name = name
        self.sell_in = sell_in
        self.quality = quality

    def __repr__(self) -> str:
        """Return string representation of the item."""
        return "%s, %s, %s" % (self.name, self.sell_in, self.quality)


class ItemUpdater(ABC):
    """
    Abstract base class for item update strategies.

    Each concrete implementation handles the specific update rules
    for different types of items in the Gilded Rose inventory system.
    """

    @abstractmethod
    def update_quality(self, item: Item) -> None:
        """
        Update the quality of the item according to its specific rules.

        Args:
            item: The item to update
        """
        pass

    @abstractmethod
    def update_sell_in(self, item: Item) -> None:
        """
        Update the sell_in value of the item according to its specific rules.

        Args:
            item: The item to update
        """
        pass

    def update(self, item: Item) -> None:
        """
        Update both quality and sell_in for the item.

        Args:
            item: The item to update
        """
        self.update_quality(item)
        self.update_sell_in(item)


class ItemUpdaterFactory:
    """
    Factory class to create the appropriate updater for different item types.
    """

    _registry: dict[str, type[ItemUpdater]] = {}
    _instances: dict[type[ItemUpdater], ItemUpdater] = {}

    @classmethod
    def configure_defaults(cls) -> None:
        """Ensure built-in updaters are registered (idempotent)."""
        _ = (AgedBrieUpdater, SulfurasUpdater, BackstagePassUpdater, ConjuredItemUpdater, NormalItemUpdater)

    @classmethod
    def register(cls, keyword: str, updater_cls: type[ItemUpdater]) -> None:
        """Register an updater class for a keyword."""
        cls._registry[keyword.lower()] = updater_cls

    @classmethod
    def autoregister(cls, keyword: str):
        """Decorator for auto-registering an updater."""

        def decorator(updater_cls: type[ItemUpdater]) -> type[ItemUpdater]:
            cls.register(keyword, updater_cls)
            return updater_cls

        return decorator

    @classmethod
    def create_updater(cls, item: Item) -> ItemUpdater:
        """Create (or reuse) the appropriate updater based on item name."""
        name = item.name.lower()

        for keyword, updater_cls in cls._registry.items():
            if keyword in name:
                if updater_cls not in cls._instances:
                    cls._instances[updater_cls] = updater_cls()
                return cls._instances[updater_cls]

        if NormalItemUpdater not in cls._instances:
            cls._instances[NormalItemUpdater] = NormalItemUpdater()
        return cls._instances[NormalItemUpdater]


class NormalItemUpdater(ItemUpdater):
    """
    Updater for normal items that decrease in quality over time.
    """

    def update_quality(self, item: Item) -> None:
        """Update quality: -1 normally, -2 after sell_in date, never below MIN_QUALITY."""
        if item.quality > MIN_QUALITY:
            decrement = 2 if item.sell_in <= MIN_QUALITY else 1
            item.quality = max(MIN_QUALITY, item.quality - decrement)

    def update_sell_in(self, item: Item) -> None:
        """Update sell_in: always decreases by 1."""
        item.sell_in -= 1


@ItemUpdaterFactory.autoregister("aged brie")
class AgedBrieUpdater(ItemUpdater):
    """
    Updater for Aged Brie that increases in quality over time.
    """

    def update_quality(self, item: Item) -> None:
        """Update quality: +1 normally, +2 after sell_in date, never above MAX_QUALITY."""
        if item.quality < MAX_QUALITY:
            increment = 2 if item.sell_in <= MIN_QUALITY else 1
            item.quality = min(MAX_QUALITY, item.quality + increment)

    def update_sell_in(self, item: Item) -> None:
        """Update sell_in: always decreases by 1."""
        item.sell_in -= 1


@ItemUpdaterFactory.autoregister("sulfuras")
class SulfurasUpdater(ItemUpdater):
    """
    Updater for Sulfuras that never changes.
    """

    def update_quality(self, item: Item) -> None:
        """Update quality: never changes."""
        pass  # Sulfuras never changes

    def update_sell_in(self, item: Item) -> None:
        """Update sell_in: never changes."""
        pass  # Sulfuras never changes


@ItemUpdaterFactory.autoregister("backstage passes")
class BackstagePassUpdater(ItemUpdater):
    """
    Updater for Backstage passes that increase in quality as concert approaches.
    """

    def update_quality(self, item: Item) -> None:
        """Update quality based on days until concert."""
        if item.sell_in <= MIN_QUALITY:
            # Concert has passed
            item.quality = MIN_QUALITY
        elif item.sell_in <= 5:
            # 5 days or less: +3, but never above MAX_QUALITY
            item.quality = min(MAX_QUALITY, item.quality + 3)
        elif item.sell_in <= 10:
            # 10 days or less: +2, but never above MAX_QUALITY
            item.quality = min(MAX_QUALITY, item.quality + 2)
        else:
            # More than 10 days: +1, but never above MAX_QUALITY
            item.quality = min(MAX_QUALITY, item.quality + 1)

    def update_sell_in(self, item: Item) -> None:
        """Update sell_in: always decreases by 1."""
        item.sell_in -= 1


@ItemUpdaterFactory.autoregister("conjured")
class ConjuredItemUpdater(ItemUpdater):
    """
    Updater for conjured items that degrade twice as fast as normal items.
    """

    def update_quality(self, item: Item) -> None:
        """Update quality: -2 normally, -4 after sell_in date, never below MIN_QUALITY."""
        if item.quality > MIN_QUALITY:
            decrement = 4 if item.sell_in <= MIN_QUALITY else 2
            item.quality = max(MIN_QUALITY, item.quality - decrement)

    def update_sell_in(self, item: Item) -> None:
        """Update sell_in: always decreases by 1."""
        item.sell_in -= 1


class GildedRose:
    """
    The Gilded Rose inventory management system.

    This class manages a collection of items and updates their quality
    and sell_in values according to specific rules for each item type.
    """

    def __init__(self, items: list[Item]) -> None:
        """
        Initialize the Gilded Rose with a list of items.

        Args:
            items: List of Item objects to manage.
        """
        self.items = items

    def update_quality(self) -> None:
        """
        Update the quality and sell_in values for all items.

        Uses the Strategy pattern with ItemUpdater classes to handle
        different item types according to their specific rules.
        """
        for item in self.items:
            updater = ItemUpdaterFactory.create_updater(item)
            updater.update(item)
