from inventory import Inventory, Item


def test_add_and_get():
    inv = Inventory()
    inv.add(Item("A1", "Widget", 3, 2.5))
    assert inv.get("A1").quantity == 3


def test_remove():
    inv = Inventory()
    inv.add(Item("A1", "Widget", 3, 2.5))
    inv.remove("A1")
    assert "A1" not in inv.items
