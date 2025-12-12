import re
import unittest

class UserRegistration:
    def __init__(self):
        # users[email] schema:
        # {
        #   "password": str,
        #   "confirmed": bool,
        #   "delivery_address": str,
        #   "favorites": list[str],
        #   "orders": list[dict],
        #   "reviews": dict[str, dict]
        # }
        self.users = {}

    def _ensure_schema(self, email):
        if email not in self.users:
            return
        u = self.users[email]
        u.setdefault("confirmed", False)
        u.setdefault("delivery_address", "123 Main St")
        u.setdefault("favorites", [])
        u.setdefault("orders", [])
        u.setdefault("reviews", {})

    def register(self, email, password, confirm_password):
        if not self.is_valid_email(email):
            return {"success": False, "error": "Invalid email format"}
        if password != confirm_password:
            return {"success": False, "error": "Passwords do not match"}
        if not self.is_strong_password(password):
            return {"success": False, "error": "Password is not strong enough"}
        if email in self.users:
            return {"success": False, "error": "Email already registered"}

        self.users[email] = {
            "password": password,
            "confirmed": False,
            "delivery_address": "123 Main St",
            "favorites": [],
            "orders": [],
            "reviews": {},
        }
        return {"success": True, "message": "Registration successful, confirmation email sent"}

    def update_password(self, email, current_password, new_password, confirm_new_password):
        if email not in self.users:
            return {"success": False, "error": "User not found"}
        self._ensure_schema(email)

        if self.users[email]["password"] != current_password:
            return {"success": False, "error": "Current password is incorrect"}
        if new_password != confirm_new_password:
            return {"success": False, "error": "Passwords do not match"}
        if not self.is_strong_password(new_password):
            return {"success": False, "error": "Password is not strong enough"}

        self.users[email]["password"] = new_password
        return {"success": True, "message": "Password updated successfully"}

    def update_delivery_address(self, email, new_address):
        if email not in self.users:
            return {"success": False, "error": "User not found"}
        self._ensure_schema(email)

        if not isinstance(new_address, str) or not new_address.strip():
            return {"success": False, "error": "Delivery address cannot be empty"}

        self.users[email]["delivery_address"] = new_address.strip()
        return {"success": True, "message": "Delivery address updated successfully"}

    def is_valid_email(self, email):
        # Simple but safer than just '@' check
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))

    def is_strong_password(self, password):
        return (
            isinstance(password, str)
            and len(password) >= 8
            and any(c.isdigit() for c in password)
            and any(c.isalpha() for c in password)
        )


class TestUserRegistration(unittest.TestCase):
    def setUp(self):
        self.registration = UserRegistration()

    def test_successful_registration(self):
        result = self.registration.register("user@example.com", "Password123", "Password123")
        self.assertTrue(result["success"])
        self.assertIn("user@example.com", self.registration.users)
        self.assertIn("delivery_address", self.registration.users["user@example.com"])

    def test_invalid_email(self):
        result = self.registration.register("userexample.com", "Password123", "Password123")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid email format")

    def test_password_mismatch(self):
        result = self.registration.register("user@example.com", "Password123", "Password321")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Passwords do not match")

    def test_weak_password(self):
        result = self.registration.register("user@example.com", "pass", "pass")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Password is not strong enough")

    def test_email_already_registered(self):
        self.registration.register("user@example.com", "Password123", "Password123")
        result = self.registration.register("user@example.com", "Password123", "Password123")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Email already registered")

    def test_update_password_success(self):
        self.registration.register("user@example.com", "Password123", "Password123")
        result = self.registration.update_password("user@example.com", "Password123", "Newpass123", "Newpass123")
        self.assertTrue(result["success"])
        self.assertEqual(self.registration.users["user@example.com"]["password"], "Newpass123")

    def test_update_password_wrong_current(self):
        self.registration.register("user@example.com", "Password123", "Password123")
        result = self.registration.update_password("user@example.com", "Wrong", "Newpass123", "Newpass123")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Current password is incorrect")

    def test_update_delivery_address(self):
        self.registration.register("user@example.com", "Password123", "Password123")
        result = self.registration.update_delivery_address("user@example.com", "  456 New Ave  ")
        self.assertTrue(result["success"])
        self.assertEqual(self.registration.users["user@example.com"]["delivery_address"], "456 New Ave")


if __name__ == "__main__":
    unittest.main()
