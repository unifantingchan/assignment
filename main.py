import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

from User_Registration import UserRegistration
from Order_Placement import Cart, OrderPlacement, UserProfile, RestaurantMenu, PaymentMethod
from Restaurant_Browsing import RestaurantDatabase, RestaurantBrowsing

USERS_FILE = "users.json"


def _ensure_user_schema(user_dict):
    user_dict.setdefault("confirmed", False)
    user_dict.setdefault("delivery_address", "123 Main St")
    user_dict.setdefault("favorites", [])
    user_dict.setdefault("orders", [])
    user_dict.setdefault("reviews", {})


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f) or {}
    # Upgrade schema for older saved files
    for _, u in users.items():
        if isinstance(u, dict):
            _ensure_user_schema(u)
    return users


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mobile Food Delivery App")
        self.geometry("760x520")

        self.user_data = load_users()

        self.registration = UserRegistration()
        self.registration.users = self.user_data  # load existing users

        self.database = RestaurantDatabase()
        self.browsing = RestaurantBrowsing(self.database)

        self.logged_in_email = None
        self.current_frame = None
        self.show_startup_frame()

    def show_startup_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = StartupFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_register_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = RegisterFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_login_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def login_user(self, email):
        self.logged_in_email = email
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MainAppFrame(self, email)
        self.current_frame.pack(fill="both", expand=True)


class StartupFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Welcome to the Mobile Food Delivery App", font=("Arial", 16)).pack(pady=30)

        tk.Button(self, text="Register", command=self.go_to_register, width=20).pack(pady=10)
        tk.Button(self, text="Login", command=self.go_to_login, width=20).pack(pady=10)

    def go_to_register(self):
        self.master.show_register_frame()

    def go_to_login(self):
        self.master.show_login_frame()


class RegisterFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Register New User", font=("Arial", 14)).pack(pady=20)

        self.email_entry = self.create_entry("Email:")
        self.pass_entry = self.create_entry("Password:", show="*")
        self.conf_pass_entry = self.create_entry("Confirm Password:", show="*")

        tk.Button(self, text="Register", command=self.register_user).pack(pady=10)
        tk.Button(self, text="Back", command=self.go_back).pack()

    def create_entry(self, label_text, show=None):
        frame = tk.Frame(self)
        frame.pack(pady=5)
        tk.Label(frame, text=label_text, width=18, anchor="e").pack(side="left")
        entry = tk.Entry(frame, show=show, width=30)
        entry.pack(side="left")
        return entry

    def register_user(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get()
        confirm_password = self.conf_pass_entry.get()

        result = self.master.registration.register(email, password, confirm_password)
        if result["success"]:
            save_users(self.master.registration.users)
            messagebox.showinfo("Success", "Registration successful! Please log in.")
            self.master.show_login_frame()
        else:
            messagebox.showerror("Error", result["error"])

    def go_back(self):
        self.master.show_startup_frame()


class LoginFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="User Login", font=("Arial", 14)).pack(pady=20)

        self.email_entry = self.create_entry("Email:")
        self.pass_entry = self.create_entry("Password:", show="*")

        tk.Button(self, text="Login", command=self.login).pack(pady=10)
        tk.Button(self, text="Back", command=self.go_back).pack()

    def create_entry(self, label_text, show=None):
        frame = tk.Frame(self)
        frame.pack(pady=5)
        tk.Label(frame, text=label_text, width=18, anchor="e").pack(side="left")
        entry = tk.Entry(frame, show=show, width=30)
        entry.pack(side="left")
        return entry

    def login(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get()
        users = self.master.registration.users
        if email in users and users[email]["password"] == password:
            self.master.login_user(email)
        else:
            messagebox.showerror("Error", "Invalid email or password")

    def go_back(self):
        self.master.show_startup_frame()


class MainAppFrame(tk.Frame):
    def __init__(self, master, user_email):
        super().__init__(master)
        self.master_app = master
        self.user_email = user_email

        tk.Label(self, text=f"Welcome, {user_email}", font=("Arial", 14)).pack(pady=10)

        self.database = master.database
        self.browsing = master.browsing

        # Ensure schema exists for this user
        user_record = master.registration.users.get(user_email, {})
        _ensure_user_schema(user_record)

        # Create user profile (backed by the same user_record dict for persistence)
        self.user_profile = UserProfile(
            delivery_address=user_record.get("delivery_address", "123 Main St"),
            email=user_email,
            store=user_record
        )

        self.cart = Cart()
        self.restaurant_menu = RestaurantMenu(available_items=["Burger", "Pizza", "Salad"])
        self.order_placement = OrderPlacement(self.cart, self.user_profile, self.restaurant_menu)

        # Search frame
        search_frame = tk.Frame(self)
        search_frame.pack(pady=10, fill="x")

        tk.Label(search_frame, text="Cuisine:").pack(side="left")
        self.cuisine_entry = tk.Entry(search_frame, width=20)
        self.cuisine_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="Search", command=self.search_restaurants).pack(side="left")

        # Restaurant results
        self.results_tree = ttk.Treeview(self, columns=("name", "cuisine", "location", "rating"), show="headings", height=8)
        for col, title in [("name", "Name"), ("cuisine", "Cuisine"), ("location", "Location"), ("rating", "Rating")]:
            self.results_tree.heading(col, text=title)
            self.results_tree.column(col, width=160 if col == "name" else 120, anchor="w")
        self.results_tree.pack(pady=10, fill="x", padx=10)

        # Action buttons
        action_frame = tk.Frame(self)
        action_frame.pack(pady=5)

        tk.Button(action_frame, text="View All Restaurants", command=self.view_all_restaurants).grid(row=0, column=0, padx=5, pady=2)
        tk.Button(action_frame, text="Add Item to Cart", command=self.add_item_to_cart).grid(row=0, column=1, padx=5, pady=2)
        tk.Button(action_frame, text="View Cart", command=self.view_cart).grid(row=0, column=2, padx=5, pady=2)
        tk.Button(action_frame, text="Checkout", command=self.checkout).grid(row=0, column=3, padx=5, pady=2)

        # New feature buttons
        feature_frame = tk.Frame(self)
        feature_frame.pack(pady=8)

        tk.Button(feature_frame, text="Order History", command=self.open_order_history).grid(row=0, column=0, padx=5, pady=2)
        tk.Button(feature_frame, text="Favorites", command=self.open_favorites).grid(row=0, column=1, padx=5, pady=2)
        tk.Button(feature_frame, text="Profile", command=self.open_profile).grid(row=0, column=2, padx=5, pady=2)
        tk.Button(feature_frame, text="Review Order", command=self.open_review).grid(row=0, column=3, padx=5, pady=2)

        self.view_all_restaurants()

    def _persist(self):
        save_users(self.master_app.registration.users)

    def search_restaurants(self):
        self.results_tree.delete(*self.results_tree.get_children())
        cuisine = self.cuisine_entry.get().strip()
        results = self.browsing.search_by_filters(cuisine_type=cuisine if cuisine else None)
        for r in results:
            self.results_tree.insert("", "end", values=(r["name"], r["cuisine"], r["location"], r["rating"]))

    def view_all_restaurants(self):
        self.results_tree.delete(*self.results_tree.get_children())
        for r in self.database.get_restaurants():
            self.results_tree.insert("", "end", values=(r["name"], r["cuisine"], r["location"], r["rating"]))

    def add_item_to_cart(self):
        menu_popup = AddItemPopup(self, self.restaurant_menu, self.cart)
        self.wait_window(menu_popup)

    def view_cart(self):
        cart_view = CartViewPopup(self, self.cart)
        self.wait_window(cart_view)

    def checkout(self):
        validation = self.order_placement.validate_order()
        if not validation["success"]:
            messagebox.showerror("Error", validation["message"])
            return
        checkout_popup = CheckoutPopup(self, self.order_placement, on_success=self._persist)
        self.wait_window(checkout_popup)

    def open_profile(self):
        popup = ProfilePopup(self, self.master_app, self.user_profile, on_saved=self._persist)
        self.wait_window(popup)

    def open_order_history(self):
        popup = OrderHistoryPopup(self, self.user_profile, on_saved=self._persist)
        self.wait_window(popup)

    def open_favorites(self):
        popup = FavoritesPopup(self, self.user_profile, self.database, on_saved=self._persist)
        self.wait_window(popup)

    def open_review(self):
        popup = ReviewPopup(self, self.user_profile, on_saved=self._persist)
        self.wait_window(popup)


class AddItemPopup(tk.Toplevel):
    def __init__(self, master, menu, cart):
        super().__init__(master)
        self.title("Add Item to Cart")
        self.menu = menu
        self.cart = cart

        tk.Label(self, text="Select an item to add to cart:").pack(pady=10)

        self.item_var = tk.StringVar(value=self.menu.available_items[0] if self.menu.available_items else "")
        tk.OptionMenu(self, self.item_var, *self.menu.available_items).pack(pady=5)

        tk.Label(self, text="Quantity:").pack()
        self.qty_entry = tk.Entry(self)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(pady=5)

        tk.Button(self, text="Add to Cart", command=self.add_to_cart).pack(pady=10)

    def add_to_cart(self):
        try:
            qty = int(self.qty_entry.get())
        except Exception:
            messagebox.showerror("Error", "Quantity must be a number")
            return

        item = self.item_var.get()
        price = 10.0  # static price for simplicity
        msg = self.cart.add_item(item, price, qty)
        messagebox.showinfo("Cart", msg)
        self.destroy()


class CartViewPopup(tk.Toplevel):
    def __init__(self, master, cart):
        super().__init__(master)
        self.title("Cart Items")

        items = cart.view_cart()
        if not items:
            tk.Label(self, text="Your cart is empty").pack(pady=20)
        else:
            for i in items:
                tk.Label(self, text=f"{i['name']} x{i['quantity']} = ${i['subtotal']:.2f}").pack()


class CheckoutPopup(tk.Toplevel):
    def __init__(self, master, order_placement, on_success=None):
        super().__init__(master)
        self.title("Checkout")
        self.order_placement = order_placement
        self.on_success = on_success

        order_data = order_placement.proceed_to_checkout()
        tk.Label(self, text="Review your order:", font=("Arial", 12)).pack(pady=10)

        for item in order_data["items"]:
            tk.Label(self, text=f"{item['name']} x{item['quantity']} = ${item['subtotal']:.2f}").pack()

        total = order_data["total_info"]
        tk.Label(self, text=f"Subtotal: ${total['subtotal']:.2f}").pack()
        tk.Label(self, text=f"Tax: ${total['tax']:.2f}").pack()
        tk.Label(self, text=f"Delivery Fee: ${total['delivery_fee']:.2f}").pack()
        tk.Label(self, text=f"Total: ${total['total']:.2f}").pack()

        tk.Label(self, text=f"Delivery Address: {order_data['delivery_address']}").pack(pady=5)

        tk.Label(self, text="Payment Method:").pack(pady=5)
        self.payment_method = tk.StringVar(value="credit_card")
        tk.Radiobutton(self, text="Credit Card", variable=self.payment_method, value="credit_card").pack()
        tk.Radiobutton(self, text="Paypal", variable=self.payment_method, value="paypal").pack()

        tk.Button(self, text="Confirm Order", command=self.confirm_order).pack(pady=12)

    def confirm_order(self):
        payment_method_obj = PaymentMethod()
        result = self.order_placement.confirm_order(payment_method_obj)
        if result["success"]:
            if self.on_success:
                self.on_success()
            messagebox.showinfo(
                "Order Confirmed",
                f"Order ID: {result['order_id']}
Estimated Delivery: {result['estimated_delivery']}
Status: Placed"
            )
            self.destroy()
        else:
            messagebox.showerror("Error", result["message"])


class ProfilePopup(tk.Toplevel):
    def __init__(self, master_frame, app, user_profile, on_saved=None):
        super().__init__(master_frame)
        self.title("Profile")
        self.app = app
        self.user_profile = user_profile
        self.on_saved = on_saved

        tk.Label(self, text="Update delivery address", font=("Arial", 11, "bold")).pack(pady=(10, 5))

        addr_frame = tk.Frame(self)
        addr_frame.pack(pady=5, padx=10, fill="x")
        tk.Label(addr_frame, text="Address:", width=10, anchor="e").pack(side="left")
        self.addr_entry = tk.Entry(addr_frame, width=40)
        self.addr_entry.insert(0, self.user_profile.delivery_address)
        self.addr_entry.pack(side="left")

        tk.Button(self, text="Save Address", command=self.save_address).pack(pady=5)

        tk.Label(self, text="Update password", font=("Arial", 11, "bold")).pack(pady=(12, 5))

        self.cur_entry = self._pw_entry("Current:")
        self.new_entry = self._pw_entry("New:")
        self.conf_entry = self._pw_entry("Confirm:")

        tk.Button(self, text="Save Password", command=self.save_password).pack(pady=8)

    def _pw_entry(self, label):
        frame = tk.Frame(self)
        frame.pack(pady=3, padx=10, fill="x")
        tk.Label(frame, text=label, width=10, anchor="e").pack(side="left")
        e = tk.Entry(frame, show="*", width=40)
        e.pack(side="left")
        return e

    def save_address(self):
        new_addr = self.addr_entry.get()
        result = self.user_profile.update_delivery_address(new_addr)
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            messagebox.showinfo("Profile", "Address updated.")
        else:
            messagebox.showerror("Profile", result["message"])

    def save_password(self):
        email = self.user_profile.email
        result = self.app.registration.update_password(
            email,
            self.cur_entry.get(),
            self.new_entry.get(),
            self.conf_entry.get()
        )
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            messagebox.showinfo("Profile", "Password updated.")
            self.cur_entry.delete(0, "end")
            self.new_entry.delete(0, "end")
            self.conf_entry.delete(0, "end")
        else:
            messagebox.showerror("Profile", result["error"])


class OrderHistoryPopup(tk.Toplevel):
    def __init__(self, master_frame, user_profile, on_saved=None):
        super().__init__(master_frame)
        self.title("Order History")
        self.user_profile = user_profile
        self.on_saved = on_saved

        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=8, padx=10, fill="x")

        tk.Label(filter_frame, text="Status:").pack(side="left")
        self.status_var = tk.StringVar(value="")
        tk.OptionMenu(filter_frame, self.status_var, "", "Placed", "Preparing", "Delivered", "Cancelled").pack(side="left", padx=5)

        tk.Label(filter_frame, text="From (YYYY-MM-DD):").pack(side="left")
        self.from_entry = tk.Entry(filter_frame, width=12)
        self.from_entry.pack(side="left", padx=5)

        tk.Label(filter_frame, text="To:").pack(side="left")
        self.to_entry = tk.Entry(filter_frame, width=12)
        self.to_entry.pack(side="left", padx=5)

        tk.Button(filter_frame, text="Apply", command=self.refresh).pack(side="left", padx=5)
        tk.Button(filter_frame, text="Clear", command=self.clear_filters).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self, columns=("order_id", "date", "status", "total"), show="headings", height=10)
        for col, title, w in [("order_id", "Order ID", 180), ("date", "Date", 110), ("status", "Status", 110), ("total", "Total", 110)]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(padx=10, pady=8, fill="x")

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Mark as Delivered", command=self.mark_delivered).pack(side="left", padx=5)

        self.refresh()

    def clear_filters(self):
        self.status_var.set("")
        self.from_entry.delete(0, "end")
        self.to_entry.delete(0, "end")
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        status = self.status_var.get() or None
        d_from = self.from_entry.get().strip() or None
        d_to = self.to_entry.get().strip() or None

        orders = self.user_profile.filter_orders(status=status, date_from=d_from, date_to=d_to) if (status or d_from or d_to) else self.user_profile.view_order_history()
        for o in orders:
            self.tree.insert("", "end", values=(o.get("order_id"), o.get("date"), o.get("status"), f"${o.get('total_amount', 0):.2f}"))

    def mark_delivered(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Order History", "Select an order first.")
            return
        order_id = self.tree.item(selected[0])["values"][0]
        result = self.user_profile.update_order_status(order_id, "Delivered")
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            self.refresh()
            messagebox.showinfo("Order History", "Order marked as Delivered.")
        else:
            messagebox.showerror("Order History", result["message"])


class FavoritesPopup(tk.Toplevel):
    def __init__(self, master_frame, user_profile, database, on_saved=None):
        super().__init__(master_frame)
        self.title("Favorites")
        self.user_profile = user_profile
        self.database = database
        self.on_saved = on_saved

        tk.Label(self, text="Your favorite restaurants").pack(pady=8)

        self.listbox = tk.Listbox(self, width=50, height=10)
        self.listbox.pack(padx=10, pady=5)

        add_frame = tk.Frame(self)
        add_frame.pack(pady=5)

        names = [r["name"] for r in self.database.get_restaurants()]
        self.pick_var = tk.StringVar(value=names[0] if names else "")
        tk.OptionMenu(add_frame, self.pick_var, *names).pack(side="left", padx=5)

        tk.Button(add_frame, text="Add", command=self.add_selected).pack(side="left", padx=5)
        tk.Button(add_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)

        self.refresh()

    def refresh(self):
        self.listbox.delete(0, "end")
        for name in self.user_profile.list_favorites():
            self.listbox.insert("end", name)

    def add_selected(self):
        name = self.pick_var.get()
        result = self.user_profile.add_favorite_restaurant(name)
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            self.refresh()
        else:
            messagebox.showerror("Favorites", result["message"])

    def remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showerror("Favorites", "Select an item to remove.")
            return
        name = self.listbox.get(sel[0])
        result = self.user_profile.remove_favorite_restaurant(name)
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            self.refresh()
        else:
            messagebox.showerror("Favorites", result["message"])


class ReviewPopup(tk.Toplevel):
    def __init__(self, master_frame, user_profile, on_saved=None):
        super().__init__(master_frame)
        self.title("Review Order")
        self.user_profile = user_profile
        self.on_saved = on_saved

        delivered_orders = [o["order_id"] for o in self.user_profile.view_order_history() if o.get("status") == "Delivered"]

        tk.Label(self, text="Select a Delivered order to review").pack(pady=10)

        self.order_var = tk.StringVar(value=delivered_orders[0] if delivered_orders else "")
        tk.OptionMenu(self, self.order_var, *delivered_orders).pack(pady=5)

        tk.Label(self, text="Rating (1-5):").pack()
        self.rating_var = tk.IntVar(value=5)
        tk.Spinbox(self, from_=1, to=5, textvariable=self.rating_var, width=5).pack(pady=5)

        tk.Label(self, text="Review:").pack()
        self.text = tk.Text(self, width=60, height=6)
        self.text.pack(padx=10, pady=5)

        tk.Button(self, text="Submit Review", command=self.submit).pack(pady=10)

        if not delivered_orders:
            messagebox.showinfo("Review", "No Delivered orders found. Mark an order as Delivered in Order History first.")

    def submit(self):
        order_id = self.order_var.get()
        review_text = self.text.get("1.0", "end").strip()
        result = self.user_profile.add_order_review(order_id, int(self.rating_var.get()), review_text)
        if result["success"]:
            if self.on_saved:
                self.on_saved()
            messagebox.showinfo("Review", "Review saved.")
            self.destroy()
        else:
            messagebox.showerror("Review", result["message"])


if __name__ == "__main__":
    app = Application()
    app.mainloop()
