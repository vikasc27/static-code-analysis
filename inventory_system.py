# inventory_system.py
"""
Improved inventory system for the static-analysis lab.
Fixes applied:
- removed mutable default args
- use explicit exception handling (no bare except)
- safe file handling with `with` and JSON error handling
- removed dangerous eval() usage
- input validation and clear return values
- use logging instead of appending to a mutable log list
- safe access to dictionary with .get()
- type hints added
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Global variable for inventory
stock_data: Dict[str, int] = {}

logger = logging.getLogger(__name__)


def add_item(item: str, qty: int) -> bool:
    """Add qty of item to stock_data. Returns True on success, False on failure."""
    if not isinstance(item, str) or item.strip() == "":
        logger.error("add_item: invalid item name: %r", item)
        return False

    # Validate quantity is an int
    try:
        qty = int(qty)
    except (ValueError, TypeError):
        logger.error("add_item: quantity must be an integer, got %r", qty)
        return False

    # Prevent accidental negative adds (you may allow but here we normalize to allow removal separately)
    stock_data[item] = stock_data.get(item, 0) + qty
    logger.info("%s: Added %d of %s", datetime.now().isoformat(), qty, item)
    return True


def remove_item(item: str, qty: int) -> bool:
    """Remove qty of item from stock_data. Returns True if removal happened, False if item not found or invalid qty."""
    if not isinstance(item, str) or item.strip() == "":
        logger.error("remove_item: invalid item name: %r", item)
        return False

    try:
        qty = int(qty)
    except (ValueError, TypeError):
        logger.error("remove_item: quantity must be an integer, got %r", qty)
        return False

    if item not in stock_data:
        logger.warning("remove_item: item %s not found in inventory", item)
        return False

    stock_data[item] -= qty
    if stock_data[item] <= 0:
        del stock_data[item]
        logger.info("remove_item: %s removed from inventory (qty <= 0)", item)
    else:
        logger.info("remove_item: reduced %s by %d, remaining %d", item, qty, stock_data.get(item, 0))
    return True


def get_qty(item: str) -> int:
    """Return quantity of item (0 if not present)."""
    if not isinstance(item, str) or item.strip() == "":
        logger.error("get_qty: invalid item name: %r", item)
        return 0
    return stock_data.get(item, 0)


def load_data(file: str = "inventory.json") -> bool:
    """Load inventory from file. Returns True on success, False on failure (file absent or invalid JSON)."""
    global stock_data
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # ensure all values are ints
            normalized: Dict[str, int] = {}
            for k, v in data.items():
                try:
                    normalized[str(k)] = int(v)
                except (ValueError, TypeError):
                    logger.warning("load_data: ignoring invalid quantity for %r: %r", k, v)
            stock_data = normalized
            logger.info("load_data: loaded %d items from %s", len(stock_data), file)
            return True
        else:
            logger.error("load_data: JSON root is not an object in %s", file)
            return False
    except FileNotFoundError:
        logger.warning("load_data: file %s not found; starting with empty inventory", file)
        stock_data = {}
        return False
    except json.JSONDecodeError as e:
        logger.error("load_data: JSON decode error in %s: %s", file, e)
        stock_data = {}
        return False
    except OSError as e:
        logger.error("load_data: OS error reading %s: %s", file, e)
        return False


def save_data(file: str = "inventory.json") -> bool:
    """Save inventory to file. Returns True on success, False on failure."""
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(stock_data, f, indent=2)
        logger.info("save_data: saved %d items to %s", len(stock_data), file)
        return True
    except OSError as e:
        logger.error("save_data: error writing to %s: %s", file, e)
        return False


def print_data() -> None:
    """Print a simple report to stdout."""
    print("Items Report")
    for item in sorted(stock_data.keys()):
        print(f"{item} -> {stock_data[item]}")


def check_low_items(threshold: int = 5) -> List[str]:
    """Return list of items whose quantity is below threshold."""
    try:
        threshold = int(threshold)
    except (ValueError, TypeError):
        logger.error("check_low_items: threshold must be an integer, got %r", threshold)
        return []
    result: List[str] = []
    for item, qty in stock_data.items():
        if qty < threshold:
            result.append(item)
    return result


def main() -> None:
    # Configure logging for CLI usage
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Sample actions (these demonstrate validation and logging)
    add_item("apple", 10)
    add_item("banana", -2)  # allowed (net negative), but validated as int
    add_item("pear", "3")  # string that converts to int
    success = add_item(123, "ten")  # invalid: item name not str -> will be rejected
    if not success:
        logger.debug("main: attempted to add invalid item (type mismatch)")

    remove_item("apple", 3)
    remove_item("orange", 1)  # not present; will just log a warning

    print("Apple stock:", get_qty("apple"))
    print("Low items:", check_low_items())

    save_data()
    load_data()
    print_data()

    # replaced unsafe eval usage with a safe log or function call
    logger.info("main: finished sample run")


if __name__ == "__main__":
    main()
