import unittest

from User_Registration import UserRegistration
from Restaurant_Browsing import RestaurantDatabase
from Order_Placement import Cart, RestaurantMenu, OrderPlacement, UserProfile, PaymentMethod


class TestIntegrationFlows(unittest.TestCase):
    def setUp(self):
        self.reg = UserRegistration()
        self.db = RestaurantDatabase()
        self.menu = RestaurantMenu(available_items=["Burger", "Pizza", "Salad"])

        # Register a user and use the underlying record as the persistence store
        self.reg.register("user@example.com", "Password123", "Password123")
        self.user_record = self.reg.users["user@example.com"]

        self.profile = UserProfile(email="user@example.com", store=self.user_record)
        self.cart = Cart()
        self.placement = OrderPlacement(self.cart, self.profile, self.menu)

    def test_place_order_updates_history(self):
        self.cart.add_item("Pizza", 10.0, 2)
        result = self.placement.confirm_order(PaymentMethod())
        self.assertTrue(result["success"])
        self.assertEqual(len(self.user_record["orders"]), 1)

    def test_add_favorite_then_list(self):
        name = self.db.get_restaurants()[0]["name"]
        self.profile.add_favorite_restaurant(name)
        self.assertIn(name, self.user_record["favorites"])

    def test_profile_edit_persists(self):
        self.profile.update_delivery_address("456 New Ave")
        self.assertEqual(self.user_record["delivery_address"], "456 New Ave")

    def test_review_only_after_delivered(self):
        self.cart.add_item("Burger", 10.0, 1)
        r = self.placement.confirm_order(PaymentMethod())
        oid = r["order_id"]

        # Cannot review while Placed
        fail = self.profile.add_order_review(oid, 5, "Nice")
        self.assertFalse(fail["success"])

        # Mark delivered and review
        self.profile.update_order_status(oid, "Delivered")
        ok = self.profile.add_order_review(oid, 5, "Nice")
        self.assertTrue(ok["success"])
        self.assertIn(oid, self.user_record["reviews"])


if __name__ == "__main__":
    unittest.main()
