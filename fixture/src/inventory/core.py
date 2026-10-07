from dataclasses import dataclass, field


@dataclass
class Item:
    sku: str
    name: str
    quantity: int
    unit_price: float


@dataclass
class Inventory:
    items: dict[str, Item] = field(default_factory=dict)

    def add(self, item: Item) -> None:
        self.items[item.sku] = item

    def remove(self, sku: str) -> None:
        del self.items[sku]

    def get(self, sku: str) -> Item:
        return self.items[sku]
