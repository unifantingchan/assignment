import unittest
from unittest import mock
from datetime import datetime, date
import uuid


def _today_iso():
    return date.today().isoformat()


def _generate_order_id():
    # Short, readable ID while still unique enough for a coursework app
    return "ORD-" + uuid.uuid4().hex[:10].upper()


class CartItem:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def update_quantity(self, new_quantity):
        self.quantity = new_quantity

    def get_subtotal(self):
        return self.price * self.quantity


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, name, price, quantity):
        if quantity <= 0:
            return "Quantity must be greater than 0"

        for item in self.items:
            if item.name == name:
                item.update_quantity(item.quantity + quantity)
                return f"Updated {name} quantity to {item.quantity}"

        self.items.append(CartItem(name, price, quantity))
        return f"Added {name} to cart"

    def remove_item(self, name):
        self.items = [item for item in self.items if item.name != name]
        return f"Removed {name} from cart"

    def update_item_quantity(self, name, new_quantity):
        for item in self.items:
            if item.name == name:
                item.update_quantity(new_quantity)
                return f"Updated {name} quantity to {new_quantity}"
        return f"{name} not found in cart"

    def calculate_total(self):
        subtotal = sum(item.get_subtotal() for item in self.items)
        tax = subtotal * 0.10
        delivery_fee = 5.00 if subtotal > 0 else 0.00
        total = subtotal + tax + delivery_fee
        return {"subtotal": subtotal, "tax": tax, "delivery_fee": delivery_fee, "total": total}

    def view_cart(self):
        return [{"name": i.name, "quantity": i.quantity, "subtotal": i.get_subtotal()} for i in self.items]

    def clear(self):
        self.items = []


class RestaurantMenu:
    def __init__(self, available_items):
        self.available_items = available_items

    def is_item_available(self, item_name):
        return item_name in self.available_items


class PaymentMethod:
    def process_payment(self, amount):
        return amount > 0


class UserProfile:
    """User state for the session, optionally backed by a persistent user record dict."""
    def __init__(self, delivery_address="123 Main St", email=None, store=None):
        self.email = email
        self.delivery_address = delivery_address

        # In-memory defaults (will be overridden by store if provided)
        self.favorites = []
        self.orders = []
        self.reviews = {}

        self._store = store
        if self._store is not None:
            # Hydrate from store
            self.delivery_address = self._store.get("delivery_address", self.delivery_address)
            self.favorites = list(self._store.get("favorites", []))
            self.orders = list(self._store.get("orders", []))
            self.reviews = dict(self._store.get("reviews", {}))

    def _sync(self):
        if self._store is None:
            return
        self._store["delivery_address"] = self.delivery_address
        self._store["favorites"] = list(self.favorites)
        self._store["orders"] = list(self.orders)
        self._store["reviews"] = dict(self.reviews)

    # Feature 1: Order History
    def view_order_history(self):
        # Newest first (by date string then creation time if present)
        return sorted(self.orders, key=lambda o: (o.get("date", ""), o.get("created_at", "")), reverse=True)

    def add_order_record(self, record):
        self.orders.append(record)
        self._sync()

    # Feature 2: Order Filtering
    def filter_orders(self, status=None, date_from=None, date_to=None):
        def parse_iso(d):
            if d is None:
                return None
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return None

        d_from = parse_iso(date_from)
        d_to = parse_iso(date_to)

        filtered = []
        for o in self.view_order_history():
            if status and o.get("status") != status:
                continue
            od = parse_iso(o.get("date"))
            if d_from and (od is None or od < d_from):
                continue
            if d_to and (od is None or od > d_to):
                continue
            filtered.append(o)
        return filtered

    def update_order_status(self, order_id, new_status):
        for o in self.orders:
            if o.get("order_id") == order_id:
                o["status"] = new_status
                self._sync()
                return {"success": True, "message": "Order status updated"}
        return {"success": False, "message": "Order not found"}

    # Feature 3: Profile editing (address only at profile layer)
    def update_delivery_address(self, new_address):
        if not isinstance(new_address, str) or not new_address.strip():
            return {"success": False, "message": "Delivery address cannot be empty"}
        self.delivery_address = new_address.strip()
        self._sync()
        return {"success": True, "message": "Delivery address updated"}

    # Feature 4: Restaurant Favorites
    def add_favorite_restaurant(self, restaurant_name):
        name = (restaurant_name or "").strip()
        if not name:
            return {"success": False, "message": "Restaurant name cannot be empty"}
        if name in self.favorites:
            return {"success": False, "message": "Restaurant already in favorites"}
        self.favorites.append(name)
        self._sync()
        return {"success": True, "message": "Added to favorites"}

    def remove_favorite_restaurant(self, restaurant_name):
        name = (restaurant_name or "").strip()
        if name in self.favorites:
            self.favorites.remove(name)
            self._sync()
            return {"success": True, "message": "Removed from favorites"}
        return {"success": False, "message": "Restaurant not in favorites"}

    def list_favorites(self):
        return list(self.favorites)

    # Feature 5: Order Review
    def add_order_review(self, order_id, rating, text):
        if not order_id:
            return {"success": False, "message": "Order ID is required"}
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {"success": False, "message": "Rating must be an integer between 1 and 5"}
        if not isinstance(text, str) or not text.strip():
            return {"success": False, "message": "Review text cannot be empty"}

        # Verify order exists and is Delivered
        order = next((o for o in self.orders if o.get("order_id") == order_id), None)
        if order is None:
            return {"success": False, "message": "Order not found"}
        if order.get("status") != "Delivered":
            return {"success": False, "message": "Only Delivered orders can be reviewed"}

        self.reviews[order_id] = {"rating": rating, "text": text.strip(), "date": _today_iso()}
        self._sync()
        return {"success": True, "message": "Review saved"}

    def get_review(self, order_id):
        return self.reviews.get(order_id)


class OrderPlacement:
    def __init__(self, cart, user_profile, restaurant_menu):
        self.cart = cart
        self.user_profile = user_profile
        self.restaurant_menu = restaurant_menu

    def validate_order(self):
        if not self.cart.items:
            return {"success": False, "message": "Cart is empty"}

        for item in self.cart.items:
            if not self.restaurant_menu.is_item_available(item.name):
                return {"success": False, "message": f"{item.name} is not available"}
        return {"success": True, "message": "Order is valid"}

    def proceed_to_checkout(self):
        total_info = self.cart.calculate_total()
        return {
            "items": self.cart.view_cart(),
            "total_info": total_info,
            "delivery_address": self.user_profile.delivery_address,
        }

    def confirm_order(self, payment_method):
        if not self.validate_order()["success"]:
            return {"success": False, "message": "Order validation failed"}

        total_info = self.cart.calculate_total()
        payment_success = payment_method.process_payment(total_info["total"])

        if not payment_success:
            return {"success": False, "message": "Payment failed"}

        order_id = _generate_order_id()
        record = {
            "order_id": order_id,
            "items": self.cart.view_cart(),
            "total_amount": total_info["total"],
            "status": "Placed",
            "date": _today_iso(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.user_profile.add_order_record(record)

        # Optional: clear cart after placing order
        self.cart.clear()

        return {
            "success": True,
            "message": "Order confirmed",
            "order_id": order_id,
            "estimated_delivery": "45 minutes",
        }


class TestOrderPlacement(unittest.TestCase):
    def setUp(self):
        self.restaurant_menu = RestaurantMenu(available_items=["Burger", "Pizza", "Salad"])
        self.user_store = {
            "delivery_address": "123 Main St",
            "favorites": [],
            "orders": [],
            "reviews": {},
        }
        self.user_profile = UserProfile(delivery_address="123 Main St", email="user@example.com", store=self.user_store)
        self.cart = Cart()
        self.order = OrderPlacement(self.cart, self.user_profile, self.restaurant_menu)

    def test_validate_order_empty_cart(self):
        result = self.order.validate_order()
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Cart is empty")

    def test_validate_order_item_not_available(self):
        self.cart.add_item("Pasta", 15.99, 1)
        result = self.order.validate_order()
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Pasta is not available")

    def test_validate_order_success(self):
        self.cart.add_item("Burger", 8.99, 2)
        result = self.order.validate_order()
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Order is valid")

    def test_confirm_order_success_and_history_updated(self):
        self.cart.add_item("Pizza", 12.99, 1)
        payment_method = PaymentMethod()
        result = self.order.confirm_order(payment_method)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Order confirmed")
        self.assertTrue(result["order_id"].startswith("ORD-"))
        # History updated (and persisted into store)
        self.assertEqual(len(self.user_profile.orders), 1)
        self.assertEqual(len(self.user_store["orders"]), 1)

    def test_confirm_order_failed_payment(self):
        self.cart.add_item("Pizza", 12.99, 1)
        payment_method = PaymentMethod()
        with mock.patch.object(payment_method, "process_payment", return_value=False):
            result = self.order.confirm_order(payment_method)
            self.assertFalse(result["success"])
            self.assertEqual(result["message"], "Payment failed")


class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.user_store = {
            "delivery_address": "123 Main St",
            "favorites": [],
            "orders": [],
            "reviews": {},
        }
        self.user_profile = UserProfile(email="user@example.com", store=self.user_store)

    def test_favorites_add_remove(self):
        r1 = self.user_profile.add_favorite_restaurant("Italian Bistro")
        self.assertTrue(r1["success"])
        r2 = self.user_profile.add_favorite_restaurant("Italian Bistro")
        self.assertFalse(r2["success"])  # duplicate
        r3 = self.user_profile.remove_favorite_restaurant("Italian Bistro")
        self.assertTrue(r3["success"])

    def test_order_filtering(self):
        self.user_profile.add_order_record({"order_id": "O1", "date": "2025-01-01", "status": "Delivered"})
        self.user_profile.add_order_record({"order_id": "O2", "date": "2025-02-01", "status": "Placed"})
        delivered = self.user_profile.filter_orders(status="Delivered")
        self.assertEqual([o["order_id"] for o in delivered], ["O1"])
        jan_only = self.user_profile.filter_orders(date_from="2025-01-01", date_to="2025-01-31")
        self.assertEqual([o["order_id"] for o in jan_only], ["O1"])

    def test_review_only_delivered(self):
        self.user_profile.add_order_record({"order_id": "O1", "date": "2025-01-01", "status": "Placed"})
        fail = self.user_profile.add_order_review("O1", 5, "Great!")
        self.assertFalse(fail["success"])
        self.user_profile.update_order_status("O1", "Delivered")
        ok = self.user_profile.add_order_review("O1", 5, "Great!")
        self.assertTrue(ok["success"])
        self.assertEqual(self.user_profile.get_review("O1")["rating"], 5)


if __name__ == "__main__":
    unittest.main()
