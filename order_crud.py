import tkinter as tk
from tkcalendar import Calendar
from tkcalendar import DateEntry
from tkinter import ttk
from tkinter import messagebox, filedialog
import customtkinter
import customtkinter as ctk
from customtkinter import CTkLabel, CTkEntry, CTkButton, CTkFrame, CTkImage, CTkToplevel, CTkComboBox
from PIL import Image
import sqlite3
import time
from datetime import datetime
import pytz
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import logging


#Data Imports
import pandas as pd
import json
import os
import sys
sys.path.append("C:/capstone")

#File imports
from product import ProductManagementSystem
from order import OrderManagementUI
from database import DatabaseManager
from pages_handler import FrameNames
from global_func import on_show, handle_logout, export_total_amount_mats
from product_crud import ProductsPage


class OrdersPage(tk.Frame):
    def __init__(self, parent, controller):
            super().__init__(parent)
            self.controller = controller
            self.config(bg='white')

            self.main = CTkFrame(self, fg_color="#6a9bc3", width=50, corner_radius=0)
            self.main.pack(side="left", fill="y", pady=(0, 0))  # Sticks to the left, fills Y
            parent.pack_propagate(False)

            self.main_desc = CTkFrame(self, fg_color="#84a8db", height=50, corner_radius=0)
            self.main_desc.pack(side="top", fill="x", padx=(0, 0), pady=(0, 10))  # Sticks to the top, fills X

            novus_logo = Image.open('C:/capstone/labels/novus_logo1.png')
            novus_logo = novus_logo.resize((50, 50))
            self.novus_photo = CTkImage(novus_logo, size=(50, 50))

            logging.basicConfig(filename='C:/capstone/log_f/actions.log', level=logging.INFO,
                                format='%(asctime)s - %(levelname)s - %(message)s')

            #Buttons Images
            self.clients_btn = self._images_buttons('C:/capstone/labels/client_btn.png', size=(100,100))
            self.inv_btn = self._images_buttons('C:/capstone/labels/inventory.png', size=(100,100))
            self.order_btn = self._images_buttons('C:/capstone/labels/order.png', size=(100,100))
            self.supply_btn = self._images_buttons('C:/capstone/labels/supply.png', size=(100,100))
            self.logout_btn = self._images_buttons('C:/capstone/labels/logout.png', size=(100,100))
            self.mrp_btn = self._images_buttons('C:/capstone/labels/mrp_btn.png', size=(100,100))
            self.settings_btn = self._images_buttons('C:/capstone/labels/settings.png', size=(100,100))
            self.user_logs_btn = self._images_buttons('C:/capstone/labels/action.png', size=(100,100))
            self.mails_btn = self._images_buttons('C:/capstone/labels/mail.png', size=(100,100))


            #User Type
            user_type = self.controller.session.get('usertype')

            # Add Products navigation button below Inventory on the left sidebar
            try:
                self.products_nav_btn = CTkButton(self.main, text="Products", fg_color="#3498db", hover_color="#2980b9",
                    text_color="white", width=100, corner_radius=10, command=self.open_products_crud)
                self.products_nav_btn.pack(side="top", padx=5, pady=5)
            except Exception:
                pass


            # Crud Buttons
            self.search_entry = ctk.CTkEntry(self, placeholder_text="Search...")
            self.search_entry.pack(side="left", anchor="n", padx=(15, 20), ipadx=60)

            order_stat_search = CTkFrame(self, fg_color='white')
            order_stat_search.pack(side="left", anchor="n", padx=(15, 15), pady=(5, 0), fill='x')

            CTkLabel(order_stat_search,
                    text="STATUS:",
                    font=('Futura', 15, 'bold'),
                    width=100,
                    anchor="w").pack(side="left")

            self.order_stat_var = tk.StringVar(value="None")
            self.order_stat_dd = CTkComboBox(order_stat_search,
                                            variable=self.order_stat_var,
                                            values=["All Status","Approved", "Pending", "Delivered", "Cancelled"],
                                            width=100,
                                            height=25,
                                            border_width=1,
                                            corner_radius=6)
            self.order_stat_dd.pack(side="left", padx=5) 


            # Add Approve, Cancel for Status
            self.srch_btn = self.add_del_upd('SEARCH', '#5dade2',command=self.upd_srch_order)
            self.add_btn = self.add_del_upd('ADD', '#2ecc71', command=self.add_orders)
            self.approve_order_btn = self.add_del_upd('APPROVE', '#27ae60',command=self.approve_order)
            self.deliver_order_btn = self.add_del_upd('DELIVERED', '#3498db', command=self.order_done)
            self.cancel_order_btn = self.add_del_upd('CANCEL', '#95a5a6', command=self.cancel_order)
            self.del_btn = self.add_del_upd('DELETE', '#e74c3c', command=self.del_order)
            self.excel_btn = self.add_del_upd('UPDATE', '#f39c12', command=self.upd_order)

            # Treeview style
            style = ttk.Style(self)
            style.theme_use("default")
            style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=('Arial', 11), bordercolor="#cccccc", borderwidth=1)
            style.configure("Treeview.Heading", background="#007acc", foreground="white", font=('futura', 13, 'bold'))
            style.map("Treeview", background=[('selected', '#b5d9ff')])

            tree_frame = tk.Frame(self)
            tree_frame.place(x=120, y=105, width=1100, height=475)

            self.order_tree = ttk.Treeview(        
            tree_frame,
                columns=('order_id', 'order_name', 'product_id', 'client_id', 
                        'order_amount', 'order_date', 'order_dl','mats_need', 'status_quo'),
                show='headings',
                style='Treeview'
            )
            self.order_tree.bind("<Double-1>", self.show_materials_popup)

            # Configure column headings (assuming _column_heads does this)
            self._column_heads('order_id', 'ORDER ID')
            self._column_heads('order_name', 'ORDER NAME')
            self._column_heads('product_id', 'PRODUCT')
            self._column_heads('client_id', 'CLIENT ID')
            self._column_heads('order_amount', 'VOLUME')
            self._column_heads('order_date', 'ORDER DATE')
            self._column_heads('order_dl', 'DEADLINE')
            self._column_heads('mats_need', 'TOTAL MATERIALS')
            self._column_heads('status_quo', 'STATUS')

            # Configure column widths and stretching
            for col in self.order_tree['columns']:
                self.order_tree.column(col, width=300, stretch=False)  # Disable stretch for proper scrolling

            # Scrollbars
            self.scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.order_tree.yview)
            self.h_scrollbar = tk.Scrollbar(tree_frame, orient="horizontal", command=self.order_tree.xview)
            self.order_tree.configure(yscrollcommand=self.scrollbar.set, xscrollcommand=self.h_scrollbar.set)

            # Use grid for proper layout
            self.order_tree.grid(row=0, column=0, sticky="nsew")
            self.scrollbar.grid(row=0, column=1, sticky="w")
            self.h_scrollbar.grid(row=1, column=0, sticky="ew")

            # Configure weight for proper resizing
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            self.load_orders_from_db()

    def open_products_crud(self):
        try:
            top = tk.Toplevel(self)
            top.title("Products Management")
            top.geometry("1300x700")
            top.minsize(1100, 600)
            top.transient(self)
            top.grab_set()
            container = tk.Frame(top, bg='white')
            container.pack(fill='both', expand=True)
            page = ProductsPage(container, self.controller)
            page.pack(fill='both', expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Products CRUD: {e}")

    def upd_srch_order(self):
        search_order = self.search_entry.get().strip()
        order_status = ["Approved", "Pending", "Delivered", "Cancelled"]

        if search_order == "":
            order_stat = self.order_stat_var.get().strip()

            if order_stat != "None" and order_stat != "All Status" and order_stat in order_status:
                try:
                    conn = sqlite3.connect('main.db')
                    c = conn.cursor()
                    all_order_stat = c.execute('SELECT * FROM orders WHERE status_quo = ?', (order_stat,)).fetchall()

                    for i in self.order_tree.get_children():
                        self.order_tree.delete(i)
                    
                    if all_order_stat:
                        for i in all_order_stat:
                            self.order_tree.insert("", "end", values=i)
                    else:
                        messagebox.showerror("No Orders", f"No Orders with Status: {order_stat}")
                        self.load_orders_from_db()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", str(e))
                    return
                finally:
                    if conn:
                        conn.close()
                        
            elif order_stat == "All Status":
                try:
                    conn = sqlite3.connect('main.db')
                    c = conn.cursor()
                    all_orders = c.execute('SELECT * FROM orders').fetchall()

                    for i in self.order_tree.get_children():
                        self.order_tree.delete(i)
                    
                    if all_orders:
                        for i in all_orders:
                            self.order_tree.insert("", "end", values=i)
                    else:
                        messagebox.showerror("No Orders", "No orders found.")
                        self.load_orders_from_db()

                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", str(e))
                    self.load_orders_from_db()
                finally:
                    if conn:
                        conn.close()
            else:
                print('Working Properly')
                pass

        elif search_order:
            try:
                conn = sqlite3.connect('main.db')
                c = conn.cursor()
                # Search across multiple columns
                query = '''
                    SELECT * FROM orders
                    WHERE order_id LIKE ?
                    OR order_name LIKE ?
                    OR product_id LIKE ?
                    OR client_id LIKE ?
                    OR quantity LIKE ?
                    OR deadline LIKE ?
                    OR mats_need LIKE ?
                    OR status_quo LIKE ?
                    ORDER BY order_id
                '''
                like_val = f'%{search_order}%'
                orders = c.execute(query, (like_val,)*8).fetchall()

                for i in self.order_tree.get_children():
                    self.order_tree.delete(i)
                
                if orders:
                    for order in orders:
                        self.order_tree.insert("", "end", values=order)
                else:
                    messagebox.showerror("No Orders", f"No orders found matching: {search_order}")
                    self.load_orders_from_db()

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
                self.load_orders_from_db()
            finally:
                if conn:
                    conn.close()

    def add_orders(self):
        # Open the Order Management UI in a separate top-level window
        top = tk.Toplevel(self)
        top.title("Order Management")
        top.geometry("900x600")
        top.minsize(700, 500)
        top.transient(self)
        top.grab_set()
        top.configure(bg='white')

        container = tk.Frame(top, bg='#f8f9fa')
        container.pack(fill='both', expand=True)

        # Initialize a DatabaseManager reusing the current session if available
        try:
            session = getattr(self.controller, 'session', {}) if hasattr(self.controller, 'session') else {}
        except Exception:
            session = {}

        db_manager = DatabaseManager(session=session) if session else DatabaseManager()

        order_ui = OrderManagementUI(
            parent_frame=container,
            db_manager=db_manager,
            session=session,
            controller=self.controller,
            parent_window=top
        )
        order_ui.setup()

    def approve_order(self):
        if (user_type := self.controller.session.get('usertype')) not in ('admin', 'owner', 'manager', 'supplier'):

            messagebox.showwarning("Access Denied", "You do not have permission to approve orders.")
            return
    
        try:
            with open('C:/capstone/json_f/order_mats_ttl.json', 'r') as f:
                try:
                    ttl_mats_list = json.load(f)
                except json.JSONDecodeError:
                    print("❌ JSON file is empty or invalid.")
                    ttl_mats_list = []
        except FileNotFoundError:
            messagebox.showerror("File Error", "Could not find 'order_mats_ttl.json'.")
            return

        selected = self.order_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an order to approve.")
            return

        values = self.order_tree.item(selected, 'values')
        order_id = values[0]

        conn = None
        try:
            conn = sqlite3.connect('main.db')
            c = conn.cursor()
            order_info = c.execute("""
                SELECT o.order_id, o.status_quo, p.product_id, p.status_quo
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.order_id = ?
            """, (order_id,)).fetchone()

            if not order_info:
                messagebox.showerror("Not Found", f"Order ID: {order_id} cannot be found")
                return

            searched_order_id, order_status, prod_id, prod_status = order_info[0],  order_info[1], order_info[2], order_info[3]

            if order_status == "Pending" and prod_status == "Approved":
                selected_order = next((order for order in ttl_mats_list if order['order_id'] == order_id), None)
                if not selected_order:
                    messagebox.showerror('Error', f'Order ID: {order_id} not found in JSON data')
                    return

                mats_need = selected_order['mats_need']

                insufficient = []
                mats_stock = {}

                # First, check all materials
                for mat_name, mat_qty_needed in mats_need.items():
                    mats_fetch = c.execute("""
                        SELECT mat_id, mat_name, mat_volume
                        FROM raw_mats WHERE mat_name = ?
                    """, (mat_name,)).fetchone()

                    if not mats_fetch:
                        insufficient.append(f"{mat_name}: Not found in inventory.")
                        continue

                    mat_id, _, current_qty = mats_fetch
                    mats_stock[mat_name] = (mat_id, current_qty)

                    if current_qty < mat_qty_needed:
                        insufficient.append(f"{mat_name}: Need {mat_qty_needed}, Have {current_qty}")

                if insufficient:
                    messagebox.showerror("Insufficient Materials", "Order cannot be approved:\n" + "\n".join(insufficient))
                    return

                # All materials are sufficient, proceed to deduct and approve
                for mat_name, mat_qty_needed in mats_need.items():
                    mat_id, current_qty = mats_stock[mat_name]
                    deducted_val = current_qty - mat_qty_needed
                    c.execute("UPDATE raw_mats SET mat_volume = ? WHERE mat_id = ?", (deducted_val, mat_id))

                new_status = "Approved"
                c.execute('UPDATE orders SET status_quo = ? WHERE order_id = ?', (new_status, searched_order_id))
                messagebox.showinfo("Success", f"Order ID: {searched_order_id} Approved!")

            elif prod_status == "Pending":
                messagebox.showinfo("Pending Product", f"Order ID: {searched_order_id}, Product ID {prod_id} Status: {prod_status}")
            elif prod_status == "Cancelled":
                messagebox.showwarning("Cancelled Product", f"Order ID: {searched_order_id}, Product ID {prod_id} Status: {prod_status}")
            elif order_status == "Approved":
                messagebox.showinfo("Already Approved", f"Order ID: {order_id} has been already approved.")
            elif order_status == "Cancelled":
                if messagebox.askyesno('Order Cancelled', 'Order has been cancelled. Do you want to approve?'):
                    # Optionally, repeat the same check/deduction logic here if you want to allow approval after cancellation
                    selected_order = next((order for order in ttl_mats_list if order['order_id'] == order_id), None)
                    if not selected_order:
                        messagebox.showerror('Error', f'Order ID: {order_id} not found in JSON data')
                        return

                    mats_need = selected_order['mats_need']
                    insufficient = []
                    mats_stock = {}

                    for mat_name, mat_qty_needed in mats_need.items():
                        mats_fetch = c.execute("""
                            SELECT mat_id, mat_name, mat_volume
                            FROM raw_mats WHERE mat_name = ?
                        """, (mat_name,)).fetchone()

                        if not mats_fetch:
                            insufficient.append(f"{mat_name}: Not found in inventory.")
                            continue

                        mat_id, _, current_qty = mats_fetch
                        mats_stock[mat_name] = (mat_id, current_qty)

                        if current_qty < mat_qty_needed:
                            insufficient.append(f"{mat_name}: Need {mat_qty_needed}, Have {current_qty}")

                    if insufficient:
                        messagebox.showerror("Insufficient Materials", "Order cannot be approved:\n" + "\n".join(insufficient))
                        return

                    for mat_name, mat_qty_needed in mats_need.items():
                        mat_id, current_qty = mats_stock[mat_name]
                        deducted_val = current_qty - mat_qty_needed
                        c.execute("UPDATE raw_mats SET mat_volume = ? WHERE mat_id = ?", (deducted_val, mat_id))

                    new_status = "Approved"
                    c.execute('UPDATE orders SET status_quo = ? WHERE order_id = ?', (new_status, searched_order_id))
                    messagebox.showinfo("Success", f"Order ID: {searched_order_id} Approved!")

            conn.commit()

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            messagebox.showerror("Database Error", f"{e}")
            print(e)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            try:
                self.load_orders_from_db()
            except Exception as e:
                print("Error reloading orders:", e)

    def cancel_order(self):
        if (user_type := self.controller.session.get('usertype')) not in ('admin', 'owner', 'manager', 'supplier'):
            messagebox.showwarning("Access Denied", "You do not have permission to cancel orders.")
            return

        selected = self.order_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an order to approve.")
            return
        
        values = self.order_tree.item(selected, 'values')
        order_id = values[0]
        order_stat = values[7]

        status = 'Cancelled'

        conn = sqlite3.connect('main.db')
        c = conn.cursor()

        c.execute("UPDATE orders SET status_quo = ? WHERE order_id = ?", (status, order_id))
        messagebox.showinfo("Success", f"Order ID '{order_id}' has been cancelled.")

        conn.commit()
        conn.close()
        self.load_orders_from_db()

    def del_order(self):
        if (user_type := self.controller.session.get('usertype')) not in ('admin', 'owner', 'manager', 'supplier'):
            messagebox.showwarning("Access Denied", "You do not have permission to deny orders.")
            return
        #Hard Deletion
        selected = self.order_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select a order to delete.")
            return

        try:
            values = self.order_tree.item(selected, 'values')
            order_id = values[0]  # Assuming client_id is the first column

            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete order ID '{order_id}'?")
            if not confirm:
                return

            conn = sqlite3.connect('main.db')
            c = conn.cursor()
            c.execute("SELECT * FROM orders WHERE order_id =  ?", (order_id,))
            row = c.fetchone()

            if row:
                c.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
                conn.commit()
                messagebox.showinfo("Deleted", f"Order ID '{order_id}' has been deleted.")
                self.load_orders_from_db()
            else:
                messagebox.showinfo("Not Found", f"No Orders found with ID '{order_id}'")

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()

    def upd_order(self):
        if (user_type := self.controller.session.get('usertype')) not in ('admin', 'owner', 'manager', 'supplier'):
            messagebox.showwarning("Access Denied", "You do not have permission to update orders.")
            return
        selected = self.order_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item to update.")
            return

        values = self.order_tree.item(selected, 'values')
        original_id = values[0]

        top = tk.Toplevel(self)
        top.title("Update Order")
        top.geometry("500x500")
        top.config(bg="white")

        fields = ['Order ID', "Order Name", 'Product', "Order Date", 'Deadline', "Order Volume", "Client ID"]
        db_cols = ['order_id', 'order_name', 'product_id', 'order_date', 'order_dl', 'order_amount', 'client_id']
        entries = []

        read_only_fields = ['Order ID', 'Order Date', 'Product', 'Client ID']

        for i, (label, value) in enumerate(zip(fields, values)):
            lbl = CTkLabel(top, text=label + ":", font=('Futura', 13, 'bold'))
            lbl.grid(row=i, column=0, padx=15, pady=10, sticky='e')
            entry = CTkEntry(top, height=28, width=220, border_width=2, border_color='#6a9bc3')
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky='w')
            if label in read_only_fields:
                entry.configure(state='readonly')
            entries.append(entry)

        def update_field(idx):
            new_value = entries[idx].get().strip()
            if not new_value:
                messagebox.showerror("Input Error", f"{fields[idx]} cannot be empty.")
                return

            col = db_cols[idx]
            if fields[idx] in read_only_fields:
                messagebox.showinfo("Info", f"{fields[idx]} cannot be changed here.")
                return

            try:
                conn = sqlite3.connect('main.db')
                c = conn.cursor()
                c.execute(f"UPDATE orders SET {col} = ? WHERE order_id = ?", (new_value, original_id))
                conn.commit()
                messagebox.showinfo("Success", f"{fields[idx]} updated!")
                self.load_orders_from_db()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        # Add an update button for each editable field
        for i, label in enumerate(fields):
            if label not in read_only_fields:
                btn = CTkButton(top, text="Update", width=70, command=lambda idx=i: update_field(idx))
                btn.grid(row=i, column=2, padx=5, pady=10)

        def update_all():
            all_values = [entry.get().strip() for entry in entries]
            if not all(all_values):
                messagebox.showerror("Input Error", "All fields are required.")
                return

            try:
                conn = sqlite3.connect('main.db')
                c = conn.cursor()
                c.execute('''
                    UPDATE orders
                    SET order_name=?, order_dl=?, order_amount=?, mats_used=?
                    WHERE order_id=?
                ''', (all_values[1], all_values[4], all_values[5], all_values[6], original_id))
                conn.commit()
                messagebox.showinfo("Success", "All editable fields updated!")
                self.load_orders_from_db()
                top.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        # "Update All" button at the bottom
        update_all_btn = CTkButton(top, text="Update All", width=120, fg_color="#6a9bc3", command=update_all)
        update_all_btn.grid(row=len(fields), column=0, columnspan=3, pady=20)

    def load_orders_from_db(self):
        try:
            conn = sqlite3.connect("main.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders")
            rows = cursor.fetchall()

            # Enumerate loop for getting every single client in the DB & inseting data in each column represented
            for i in self.order_tree.get_children():
                self.order_tree.delete(i)

            for row in rows:
                self.order_tree.insert("", "end", values=row)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()

    #
    def order_done(self):
        if (user_type := self.controller.session.get('usertype')) not in ('admin', 'owner', 'manager', 'supplier'):
            messagebox.showwarning("Access Denied", "You do not have permission to approve orders.")
            return
        selected = self.order_tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select an order to mark as delivered.")
            return  

        try:
            user_id = self.controller.session.get('user_id')

            if not user_id:
                messagebox.showerror("Session Error", "User  not logged in.")
                return

            timestamp = datetime.now(pytz.timezone('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
            values = self.order_tree.item(selected, 'values')
            order_id = values[0]

            conn = sqlite3.connect('main.db')
            c = conn.cursor()

            order_info = c.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()


            if not order_info:
                messagebox.showerror("Not Found", f'Order ID: {order_id} cannot be found')
                return
            
            selected_id, client_id, order_status = order_info[0], order_info[3], order_info[8]

            existing_order = c.execute('SELECT * FROM order_history WHERE order_id = ?', (selected_id,)).fetchone()

            if existing_order:
                messagebox.showerror("Order Already Delivered", f"Order ID: {selected_id} has already been marked as delivered.")
                return

            # If there is any sort of confirmation from the customer that the item is delivered.
            if order_status != "Approved":
                messagebox.showerror("Order Status Error", f"Order ID: {selected_id} is not approved yet.")
                return
            else:    
                delivery_status = "Delivered"
                notes = f"Order ID {selected_id} has been delivered to Client: {client_id}"
                c.execute('INSERT INTO order_history (order_id, status, changed_by, notes, timestamp) VALUES (?, ?, ?, ?, ?)',
                        (selected_id, delivery_status, user_id, notes, timestamp))
                logging.info(f"Order ID {selected_id} marked as delivered by User ID {user_id} at {timestamp}")
                c.execute('UPDATE orders SET status_quo = ? WHERE order_id = ?', (delivery_status, selected_id))
                messagebox.showinfo("Success", f"Order ID: {selected_id} has been marked as delivered.")
                self.load_orders_from_db()

                print(f"Order ID: {selected_id} has been marked as delivered by User ID {user_id} at {timestamp}")


            conn.commit()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            return
        finally:
            conn.close()

    def show_materials_popup(self, event):
        selected = self.order_tree.focus()
        if not selected:
            return
        values = self.order_tree.item(selected, 'values')
        order_id = values[0]
        mats_used = values[7]  # Assuming this is still relevant

        try:
            conn = sqlite3.connect('main.db')
            c = conn.cursor()

            # Fetch all order history entries for the selected order
            order_history = c.execute("SELECT status, changed_by, notes, timestamp FROM order_history WHERE order_id = ? ORDER BY timestamp DESC", (order_id,)).fetchall()

            if not order_history:
                popup_info = tk.Toplevel(self)
                popup_info.title("Order Information")
                popup_info.geometry("400x200")

                info_frame = tk.Frame(popup_info)
                info_frame.pack(expand=True, fill='both', padx=10, pady=10)

                info_txt = tk.Text(info_frame, wrap='word', font=('Arial', 12))
                scrollbar = tk.Scrollbar(info_frame, command=info_txt.yview)
                info_txt.configure(yscrollcommand=scrollbar.set)

                scrollbar.pack(side='right', fill='y')
                info_txt.pack(side='left', expand=True, fill='both')

                info_txt.insert('end', f'This is order from: {order_id} has no history yet.\n')
                info_txt.insert('end', f'Materials Used: {mats_used}.\n')
                info_txt.configure(state='disabled')

                btn_close = tk.Button(popup_info, text="Close", command=popup_info.destroy)
                btn_close.pack(pady=5)
                
            else:
                # Create the popup window
                popup = tk.Toplevel(self)
                popup.title(f"Order History - ID: {order_id}")
                popup.geometry("600x400")

                frame = tk.Frame(popup)
                frame.pack(expand=True, fill='both', padx=10, pady=10)

                txt = tk.Text(frame, wrap='word', font=('Arial', 10))
                scrollbar = tk.Scrollbar(frame, command=txt.yview)
                txt.configure(yscrollcommand=scrollbar.set)

                scrollbar.pack(side='right', fill='y')
                txt.pack(side='left', expand=True, fill='both')

                # Insert materials used and order history entries
                txt.insert('end', f"Materials Used for Order ID: {order_id}\n")
                txt.insert('end', "="*50 + "\n")
                txt.insert('end', f"{mats_used}\n\n")
                txt.insert('end', "Order History:\n")
                txt.insert('end', "="*50 + "\n\n")

                for entry in order_history:
                    status, changed_by, notes, timestamp = entry
                    txt.insert('end', f"Status: {status}\n")
                    txt.insert('end', f"Changed by: {changed_by}\n")
                    txt.insert('end', f"Timestamp: {timestamp}\n")
                    txt.insert('end', f"Notes: {notes}\n")
                    txt.insert('end', "-"*50 + "\n\n")

                # Make text read-only
                txt.configure(state='disabled')

                # Close button
                btn_close = tk.Button(popup, text="Close", command=popup.destroy)
                btn_close.pack(pady=5)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return
        finally:
            conn.close()

    def add_del_upd(self, text, fg_color, command):
        button = CTkButton(self, text=text, fg_color=fg_color, width=80, command=command)
        button.pack(side="left", anchor="n", padx=5)
        return button

    def _column_heads(self, columns, text):
        self.order_tree.heading(columns, text=text)
        self.order_tree.column(columns, width=175)
        if text == 'MATERIALS':
            self.order_tree.column(columns, width=100)

    def _main_buttons(self, parent, image, text, command):
        button = CTkButton(parent, image=image, text=text, bg_color="#6a9bc3", fg_color="#6a9bc3", hover_color="white",
        width=100, border_color="white", corner_radius=10, border_width=2, command=command)
        button.pack(side="top", padx=5, pady=15)

    def _images_buttons(self, image_path, size=(40, 40)):
        image = Image.open(image_path)
        size = size
        return CTkImage(image)

    def _add_order(self, label_text, y):

        label = CTkLabel(self.add_order, text=label_text, font=('Futura', 15, 'bold'))
        label.pack(pady=(5, 0))
        entry = CTkEntry(self.add_order, height=20, width=250, border_width=2, border_color='black')
        entry.pack(pady=(0, 10))
        return entry
    
    def on_show(self):
        on_show(self)  # Calls the shared sidebar logic

    def handle_logout(self):
        handle_logout(self) 