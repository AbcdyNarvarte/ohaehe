import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import json
import traceback


class OrderManagementUI:
    def __init__(self, parent_frame, db_manager, session=None, controller=None, parent_window=None):
        self.parent_frame = parent_frame
        self.db_manager = db_manager
        self.session = session or {}
        self.controller = controller
        self.parent_window = parent_window

        # Tk variables and widgets initialized in setup
        self.order_name_var = None
        self.selected_product_var = None
        self.product_combo = None
        self.selected_client_var = None
        self.client_combo = None
        self.order_quantity_var = None
        self.deadline_tab = None
        self.product_materials_text = None
        self.required_materials_text = None

        # Calculation state
        self.order_materials_data = {}

    # UI setup
    def setup(self):
        main_canvas = tk.Canvas(self.parent_frame, bg='#ffffff', highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.parent_frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg='#ffffff')

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        content_container = tk.Frame(scrollable_frame, bg='#ffffff')
        content_container.pack(fill='both', expand=True, padx=10, pady=5)

        order_section = tk.LabelFrame(content_container, text="  📋 Order Information  ", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=2, padx=10, pady=10)
        order_section.pack(fill='x', pady=(0, 10))

        tk.Label(order_section, text="Order Name:", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))

        self.order_name_var = tk.StringVar()
        order_entry = tk.Entry(order_section, textvariable=self.order_name_var, font=('Segoe UI', 10), relief='solid', bd=2, width=40)
        order_entry.pack(fill='x', pady=(0, 10), ipady=4)

        selection_section = tk.LabelFrame(content_container, text="  🎯 Product & Client Selection  ", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=2, padx=10, pady=10)
        selection_section.pack(fill='x', pady=(0, 10))

        tk.Label(selection_section, text="Select Product:", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))

        self.selected_product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(selection_section, textvariable=self.selected_product_var, state="readonly", font=('Segoe UI', 9), width=40)
        self.product_combo.pack(fill='x', pady=(0, 8), ipady=3)
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_selected)

        tk.Label(selection_section, text="Select Client:", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))

        self.selected_client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(selection_section, textvariable=self.selected_client_var, state="readonly", font=('Segoe UI', 9), width=40)
        self.client_combo.pack(fill='x', pady=(0, 8), ipady=3)

        details_section = tk.LabelFrame(content_container, text="  📊 Order Details  ", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=2, padx=10, pady=10)
        details_section.pack(fill='x', pady=(0, 10))

        details_grid = tk.Frame(details_section, bg='#ffffff')
        details_grid.pack(fill='x', pady=(0, 8))
        details_grid.columnconfigure(1, weight=1)
        details_grid.columnconfigure(3, weight=1)

        tk.Label(details_grid, text="Quantity:", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').grid(row=0, column=0, sticky='w', padx=(0, 8), pady=4)
        self.order_quantity_var = tk.StringVar()
        quantity_entry = tk.Entry(details_grid, textvariable=self.order_quantity_var, font=('Segoe UI', 9), relief='solid', bd=2, width=12)
        quantity_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10), pady=4, ipady=3)
        quantity_entry.bind('<KeyRelease>', self.on_quantity_changed)

        tk.Label(details_grid, text="Deadline:", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').grid(row=0, column=2, sticky='w', padx=(0, 8), pady=4)
        self.deadline_tab = tk.StringVar()
        deadline_entry = DateEntry(details_grid, textvariable=self.deadline_tab, font=('Segoe UI', 9), relief='solid', bd=2, width=12, date_pattern='mm/dd/yyyy', background='#f8f9fa', foreground='#34495e', calendar_background='#f8f9fa')
        deadline_entry.grid(row=0, column=3, sticky='ew', padx=(0, 10), pady=4, ipady=3)

        calc_btn = tk.Button(details_grid, text="🧮 Calculate Materials", command=self.calculate_materials, font=('Segoe UI', 9, 'bold'), bg='#f39c12', fg='white', relief='flat', cursor='hand2', padx=10, pady=4)
        calc_btn.grid(row=0, column=4, padx=(8, 0), pady=4)

        calc_section = tk.LabelFrame(content_container, text="  🔬 Materials Calculation  ", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=2, padx=10, pady=10)
        calc_section.pack(fill='both', expand=True, pady=(0, 10))

        tk.Label(calc_section, text="Product Materials (per unit):", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))
        product_materials_container = tk.Frame(calc_section, bg='#ffffff', relief='solid', bd=2)
        product_materials_container.pack(fill='x', pady=(0, 10))
        self.product_materials_text = tk.Text(product_materials_container, height=3, state='disabled', bg='#f8f9fa', font=('Segoe UI', 9), relief='flat', bd=0, wrap=tk.WORD, width=40)
        product_scrollbar = ttk.Scrollbar(product_materials_container, orient="vertical", command=self.product_materials_text.yview)
        self.product_materials_text.configure(yscrollcommand=product_scrollbar.set)
        self.product_materials_text.pack(side=tk.LEFT, fill='both', expand=True, padx=5, pady=5)
        product_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        tk.Label(calc_section, text="Required Materials (total):", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(5, 5))
        required_materials_container = tk.Frame(calc_section, bg='#ffffff', relief='solid', bd=2)
        required_materials_container.pack(fill='both', expand=True)
        self.required_materials_text = tk.Text(required_materials_container, height=3, state='disabled', bg='#e8f5e8', font=('Segoe UI', 9), relief='flat', bd=0, wrap=tk.WORD, width=40)
        required_scrollbar = ttk.Scrollbar(required_materials_container, orient="vertical", command=self.required_materials_text.yview)
        self.required_materials_text.configure(yscrollcommand=required_scrollbar.set)
        self.required_materials_text.pack(side=tk.LEFT, fill='both', expand=True, padx=5, pady=5)
        required_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        order_action_section = tk.Frame(content_container, bg='#ffffff')
        order_action_section.pack(fill='x', pady=10)
        button_style = {'font': ('Segoe UI', 10, 'bold'), 'relief': 'flat', 'cursor': 'hand2', 'padx': 10, 'pady': 6}

        create_order_btn = tk.Button(order_action_section, text="✅ Create Order", command=self.create_order, bg='#27ae60', fg='white', **button_style)
        create_order_btn.pack(side=tk.LEFT, padx=(0, 8))
        view_orders_btn = tk.Button(order_action_section, text="📋 View All Orders", command=self.show_order_list, bg='#8e44ad', fg='white', **button_style)
        view_orders_btn.pack(side=tk.LEFT)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        def _on_mousewheel_order(event):
            try:
                main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        main_canvas.bind("<MouseWheel>", _on_mousewheel_order)

        self.load_products_and_clients()

    # Event handlers and helpers
    def on_product_selected(self, event=None):
        self.display_product_materials()
        self.calculate_materials()

    def on_quantity_changed(self, event=None):
        self.calculate_materials()

    def display_product_materials(self):
        selected_product = self.selected_product_var.get().strip()
        if not selected_product:
            self.product_materials_text.config(state='normal')
            self.product_materials_text.delete(1.0, tk.END)
            self.product_materials_text.config(state='disabled')
            return

        try:
            product_id = selected_product.split('(')[-1].strip(')')
            materials = self.db_manager.get_product_materials(product_id)
            self.product_materials_text.config(state='normal')
            self.product_materials_text.delete(1.0, tk.END)
            self.product_materials_text.insert(1.0, materials or "No materials found for this product.")
            self.product_materials_text.config(state='disabled')
        except Exception as e:
            self.product_materials_text.config(state='normal')
            self.product_materials_text.delete(1.0, tk.END)
            self.product_materials_text.insert(1.0, f"Error loading materials: {str(e)}")
            self.product_materials_text.config(state='disabled')

    def parse_materials(self, materials_string):
        if not materials_string:
            return {}
        import re
        materials = {}
        items = re.split(r'[;,]', materials_string)
        for item in items:
            item = item.strip()
            if not item:
                continue
            match = re.match(r'(.+?)\s*[-:]\s*(\d+)', item)
            if match:
                material_name = match.group(1).strip()
                quantity = int(match.group(2))
                materials[material_name] = quantity
            else:
                materials[item] = 0
        return materials

    def calculate_materials(self):
        try:
            selected_product = self.selected_product_var.get().strip()
            quantity_str = self.order_quantity_var.get().strip()
            if not selected_product:
                raise ValueError("Please select a product")
            if not quantity_str:
                raise ValueError("Please enter quantity")
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            product_id = selected_product.split('(')[-1].strip(')')
            materials_string = self.db_manager.get_product_materials(product_id)
            if not materials_string:
                raise ValueError("No materials found for this product")
            materials_dict = self.parse_materials(materials_string)
            if not materials_dict:
                raise ValueError("Materials format not recognized")
            self.order_materials_data = {}
            calculation_text = f"For {quantity} units:\n\n"
            for material_name, unit_quantity in materials_dict.items():
                try:
                    unit_qty = float(unit_quantity)
                    total_needed = unit_qty * quantity
                    self.order_materials_data[material_name] = total_needed
                    calculation_text += f"• {material_name}: {total_needed}\n"
                except (TypeError, ValueError):
                    calculation_text += f"• {material_name}: (invalid quantity)\n"
            self.required_materials_text.config(state='normal')
            self.required_materials_text.delete(1.0, tk.END)
            self.required_materials_text.insert(1.0, calculation_text)
            self.required_materials_text.config(state='disabled')
        except ValueError as e:
            self._show_materials_error(str(e))
        except Exception as e:
            self._show_materials_error(f"Calculation error: {str(e)}")
            print(f"Error trace: {traceback.format_exc()}")

    def _show_materials_error(self, message):
        self.required_materials_text.config(state='normal')
        self.required_materials_text.delete(1.0, tk.END)
        self.required_materials_text.insert(1.0, message)
        self.required_materials_text.config(state='disabled')

    # Data loading
    def load_products_and_clients(self):
        try:
            product_options = self.db_manager.get_products_for_dropdown()
            self.product_combo['values'] = product_options
            client_options = self.db_manager.get_clients_for_dropdown()
            self.client_combo['values'] = client_options
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading products and clients: {str(e)}")

    # CRUD: Orders
    def create_order(self):
        from global_func import export_total_amount_mats
        order_name = self.order_name_var.get().strip()
        selected_product = self.selected_product_var.get().strip()
        selected_client = self.selected_client_var.get().strip()
        quantity = self.order_quantity_var.get().strip()
        deadline = self.deadline_tab.get().strip()

        if not order_name:
            messagebox.showerror("Error", "Please enter an order name.")
            return
        if not selected_product:
            messagebox.showerror("Error", "Please select a product.")
            return
        if not selected_client:
            messagebox.showerror("Error", "Please select a client.")
            return
        if not quantity:
            messagebox.showerror("Error", "Please enter quantity.")
            return
        try:
            quantity_int = int(quantity)
            if quantity_int <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive whole number.")
            return
        if not deadline:
            messagebox.showerror("Error", "Please enter a deadline.")
            return
        if not hasattr(self, "order_materials_data") or not self.order_materials_data:
            messagebox.showerror("Error", "Please calculate required materials first.")
            return
        try:
            materials_json = json.dumps(self.order_materials_data)
            product_id = selected_product.split('(')[-1].strip(')')
            client_id = selected_client.split('(')[-1].strip(')')
            order_id = self.db_manager.create_order(order_name, product_id, client_id, quantity_int, deadline, materials_json)

            self.order_name_var.set("")
            self.selected_product_var.set("")
            self.selected_client_var.set("")
            self.order_quantity_var.set("")
            self.deadline_tab.set("")

            self.product_materials_text.config(state='normal')
            self.product_materials_text.delete(1.0, tk.END)
            self.product_materials_text.config(state='disabled')
            self.required_materials_text.config(state='normal')
            self.required_materials_text.delete(1.0, tk.END)
            self.required_materials_text.config(state='disabled')

            # Optional logging to product logger if present in caller
            try:
                import logging
                product_logger = logging.getLogger('product_logger')
                if self.session and 'user_id' in self.session:
                    user_id = self.session.get('user_id')
                    user_name = self.session.get('f_name', self.session.get('username', 'Unknown'))
                    product_logger.info(f"User {user_name} (ID: {user_id}) created order '{order_name}' (ID: {order_id}) for product ID: {product_id}, client ID: {client_id}, quantity: {quantity_int}")
            except Exception:
                pass

            messagebox.showinfo("Success", f"Order '{order_name}' created successfully!\nOrder ID: {order_id}")
        except (TypeError, json.JSONDecodeError) as e:
            messagebox.showerror("Format Error", f"Invalid materials data format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Database Error", f"Error creating order: {str(e)}")
        export_total_amount_mats('main.db', 'C:/capstone/json_f/order_mats_ttl.json')

    def edit_order(self, order_id, order_name, product_id, client_id, quantity, deadline):
        from tkcalendar import DateEntry
        edit_window = tk.Toplevel(self.parent_window or self.parent_frame)
        edit_window.title("Edit Order")
        edit_window.geometry("700x500")
        edit_window.minsize(600, 400)
        edit_window.transient(self.parent_window or self.parent_frame)
        edit_window.grab_set()
        edit_window.configure(bg='#f8f9fa')

        main_frame = tk.Frame(edit_window, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_label = tk.Label(main_frame, text="✏️ Edit Order", font=('Segoe UI', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(pady=(0, 20))

        info_frame = tk.LabelFrame(main_frame, text="Order Information", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=1, padx=20, pady=15)
        info_frame.pack(fill='x', pady=(0, 20))

        tk.Label(info_frame, text="Order Name:", font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))
        edit_order_name_var = tk.StringVar(value=order_name)
        order_name_entry = tk.Entry(info_frame, textvariable=edit_order_name_var, font=('Segoe UI', 11), relief='solid', bd=2, width=50)
        order_name_entry.pack(fill='x', pady=(0, 10), ipady=6)

        tk.Label(info_frame, text="Select Product:", font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))
        edit_product_var = tk.StringVar()
        edit_product_combo = ttk.Combobox(info_frame, textvariable=edit_product_var, state="readonly", font=('Segoe UI', 10), width=60)
        edit_product_combo.pack(fill='x', pady=(0, 10), ipady=6)

        tk.Label(info_frame, text="Select Client:", font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 5))
        edit_client_var = tk.StringVar()
        edit_client_combo = ttk.Combobox(info_frame, textvariable=edit_client_var, state="readonly", font=('Segoe UI', 10), width=60)
        edit_client_combo.pack(fill='x', pady=(0, 10), ipady=6)

        details_frame = tk.LabelFrame(main_frame, text="Order Details", font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#2c3e50', relief='solid', bd=1, padx=20, pady=15)
        details_frame.pack(fill='x', pady=(0, 20))

        details_grid = tk.Frame(details_frame, bg='#ffffff')
        details_grid.pack(fill='x')
        details_grid.columnconfigure(1, weight=1)
        details_grid.columnconfigure(3, weight=1)

        tk.Label(details_grid, text="Quantity:", font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').grid(row=0, column=0, sticky='w', padx=(0, 8), pady=4)
        edit_quantity_var = tk.StringVar(value=str(quantity))
        quantity_entry = tk.Entry(details_grid, textvariable=edit_quantity_var, font=('Segoe UI', 9), relief='solid', bd=2, width=12)
        quantity_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10), pady=4, ipady=3)

        tk.Label(details_grid, text="Deadline:", font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').grid(row=0, column=2, sticky='w', padx=(0, 8), pady=4)
        edit_deadline_var = tk.StringVar(value=deadline)
        deadline_entry = DateEntry(details_grid, textvariable=edit_deadline_var, font=('Segoe UI', 9), relief='solid', bd=2, width=12, date_pattern='mm/dd/yyyy', background='#f8f9fa', foreground='#34495e', calendar_background='#f8f9fa')
        deadline_entry.grid(row=0, column=3, sticky='ew', padx=(0, 10), pady=4, ipady=3)

        try:
            product_options = self.db_manager.get_products_for_dropdown()
            edit_product_combo['values'] = product_options
            for option in product_options:
                if product_id in option:
                    edit_product_var.set(option)
                    break
            client_options = self.db_manager.get_clients_for_dropdown()
            edit_client_combo['values'] = client_options
            for option in client_options:
                if client_id in option:
                    edit_client_var.set(option)
                    break
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading data: {str(e)}")

        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=20)

        def save_order_changes():
            new_order_name = edit_order_name_var.get().strip()
            new_product = edit_product_var.get().strip()
            new_client = edit_client_var.get().strip()
            new_quantity = edit_quantity_var.get().strip()
            new_deadline = edit_deadline_var.get().strip()
            if not new_order_name:
                messagebox.showerror("Error", "Please enter an order name.")
                return
            if not new_product:
                messagebox.showerror("Error", "Please select a product.")
                return
            if not new_client:
                messagebox.showerror("Error", "Please select a client.")
                return
            if not new_quantity:
                messagebox.showerror("Error", "Please enter quantity.")
                return
            try:
                quantity_int = int(new_quantity)
                if quantity_int <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a positive whole number.")
                return
            if not new_deadline:
                messagebox.showerror("Error", "Please enter a deadline.")
                return
            try:
                new_product_id = new_product.split('(')[-1].strip(')')
                new_client_id = new_client.split('(')[-1].strip(')')
                self.db_manager.update_order(order_id, new_order_name, new_product_id, new_client_id, quantity_int, new_deadline)
                try:
                    import logging
                    product_logger = logging.getLogger('product_logger')
                    if self.session and 'user_id' in self.session:
                        user_id = self.session.get('user_id')
                        user_name = self.session.get('f_name', self.session.get('username', 'Unknown'))
                        product_logger.info(f"User {user_name} (ID: {user_id}) updated order '{order_name}' to '{new_order_name}' (ID: {order_id})")
                except Exception:
                    pass
                messagebox.showinfo("Success", "Order updated successfully!")
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Database Error", f"Error updating order: {str(e)}")

        save_btn = tk.Button(button_frame, text="💾 Save Changes", command=save_order_changes, font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", command=edit_window.destroy, font=('Segoe UI', 11, 'bold'), bg='#95a5a6', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT)

    def delete_order(self, order_id, order_name):
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the order '{order_name}'?\n\nThis action cannot be undone."):
            try:
                self.db_manager.delete_order(order_id)
                try:
                    import logging
                    product_logger = logging.getLogger('product_logger')
                    if self.session and 'user_id' in self.session:
                        user_id = self.session.get('user_id')
                        user_name = self.session.get('f_name', self.session.get('username', 'Unknown'))
                        product_logger.info(f"User {user_name} (ID: {user_id}) deleted order '{order_name}' (ID: {order_id})")
                except Exception:
                    pass
                messagebox.showinfo("Success", f"Order '{order_name}' deleted successfully!")
            except Exception as e:
                messagebox.showerror("Database Error", f"Error deleting order: {str(e)}")

    def show_order_list(self):
        popup = tk.Toplevel(self.parent_window or self.parent_frame)
        popup.title("Order List")
        popup.geometry("1300x700")
        popup.minsize(1100, 600)
        popup.transient(self.parent_window or self.parent_frame)
        popup.grab_set()
        popup.configure(bg='#f8f9fa')

        main_frame = tk.Frame(popup, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_label = tk.Label(main_frame, text="📋 Order List", font=('Segoe UI', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(pady=(0, 20))

        tree_frame = tk.Frame(main_frame, bg='#ffffff', relief='solid', bd=1)
        tree_frame.pack(fill='both', expand=True, pady=(0, 20))

        columns = ('ID', 'Name', 'Product', 'Client', 'Quantity', 'Material Needed', 'Deadline', 'Order Date', 'Status Quo')
        order_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        order_tree.heading('ID', text='Order ID')
        order_tree.heading('Name', text='Order Name')
        order_tree.heading('Product', text='Product')
        order_tree.heading('Client', text='Client')
        order_tree.heading('Quantity', text='Quantity')
        order_tree.heading('Material Needed', text='Material Needed')
        order_tree.heading('Deadline', text='Deadline')
        order_tree.heading('Order Date', text='Order Date')
        order_tree.heading('Status Quo', text='Status Quo')

        order_tree.column('ID', width=120, minwidth=100)
        order_tree.column('Name', width=150, minwidth=120)
        order_tree.column('Product', width=150, minwidth=120)
        order_tree.column('Client', width=150, minwidth=120)
        order_tree.column('Quantity', width=80, minwidth=60)
        order_tree.column('Material Needed', width=200, minwidth=150)
        order_tree.column('Deadline', width=120, minwidth=100)
        order_tree.column('Order Date', width=120, minwidth=100)
        order_tree.column('Status Quo', width=100, minwidth=80)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=order_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=order_tree.xview)
        order_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        order_tree.pack(side=tk.LEFT, fill='both', expand=True, padx=10, pady=10)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        def load_orders():
            for item in order_tree.get_children():
                order_tree.delete(item)
            try:
                orders = self.db_manager.get_all_orders()
                for order in orders:
                    order_id, name, product_name, client_name, quantity, mats_need, deadline, order_date, product_id, client_id, status_quo = order
                    formatted_date = order_date
                    try:
                        from datetime import datetime
                        if order_date:
                            try:
                                dt = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S.%f')
                                formatted_date = dt.strftime('%m/%d/%Y')
                            except:
                                dt = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S')
                                formatted_date = dt.strftime('%m/%d/%Y')
                    except Exception:
                        pass
                    order_tree.insert('', 'end', values=(order_id or 'N/A', name or 'N/A', product_name or 'N/A', client_name or 'N/A', quantity or 'N/A', mats_need or 'N/A', deadline or 'N/A', formatted_date or 'N/A', status_quo or 'N/A'), tags=(product_id, client_id))
            except Exception as e:
                messagebox.showerror("Database Error", f"Error loading orders: {str(e)}")

        load_orders()

        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(pady=10)

        def edit_selected_order():
            selection = order_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an order to edit.")
                return
            item = order_tree.item(selection[0])
            values = item['values']
            tags = item['tags']
            order_id = values[0]
            order_name = values[1]
            quantity = values[4]
            deadline = values[5]
            product_id = tags[0] if tags else ""
            client_id = tags[1] if len(tags) > 1 else ""
            self.edit_order(order_id, order_name, product_id, client_id, quantity, deadline)
            load_orders()

        def approved_selected_order():
            selection = order_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an order to Approve.")
                return
            item = order_tree.item(selection[0])
            values = item['values']
            order_id = values[0]
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            try:
                order_info = c.execute("""
                    SELECT o.order_id, o.status_quo, p.product_id, p.status_quo
                    FROM orders o
                    JOIN products p ON o.product_id = p.product_id
                    WHERE o.order_id = ?
                """, (order_id,)).fetchone()
                if not order_info:
                    messagebox.showerror('Not Found', f'Order ID: {order_id} cannot be found')
                    return
                searched_order_id = order_info[0]
                order_status = order_info[1]
                prod_id = order_info[2]
                prod_status = order_info[3]
                if order_status == "Pending" and prod_status == "Approved":
                    self.db_manager.deduct_materials_for_order(order_id)
                    self.db_manager.approve_order(order_id)
                    messagebox.showinfo("Success", f"Order ID: {searched_order_id} Approved!")
                    from global_func import export_materials_to_json
                    export_materials_to_json("main.db", "C:/capstone/json_f/products_materials.json")
                elif prod_status == "Pending":
                    messagebox.showinfo("Info", f"Order ID: {searched_order_id}, Product ID {prod_id} Status: {prod_status}")
                elif prod_status == "Cancelled":
                    messagebox.showwarning("Warning", f"Order ID: {searched_order_id}, Product ID {prod_id} Status: {prod_status}")
                elif order_status == "Approved":
                    messagebox.showinfo("Info", f"Order ID: {order_id} has been already approved.")
                elif order_status == "Cancelled":
                    if messagebox.askyesno('Order has been cancelled. Do you want to approve?'):
                        self.db_manager.deduct_materials_for_order(order_id)
                        self.db_manager.approve_order(order_id)
                        messagebox.showinfo("Success", f"Order ID: {searched_order_id} Approved!")
                        from global_func import export_materials_to_json
                        export_materials_to_json("main.db", "C:/capstone/json_f/products_materials.json")
                conn.commit()
            except Exception as e:
                conn.rollback()
                messagebox.showerror('Database Error', str(e))
                print(e)
            finally:
                conn.close()
            load_orders()

        def cancel_selected_order():
            selection = order_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an order to delete.")
                return
            item = order_tree.item(selection[0])
            values = item['values']
            order_id = values[0]
            status = 'Cancelled'
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            c.execute("UPDATE orders SET status_quo = ? WHERE order_id = ?", (status, order_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Order '{order_id}' has been cancelled successfully!")
            load_orders()

        def delete_selected_order():
            selection = order_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an order to delete.")
                return
            item = order_tree.item(selection[0])
            values = item['values']
            order_id = values[0]
            order_name = values[1]
            self.delete_order(order_id, order_name)
            load_orders()

        def refresh_orders():
            load_orders()
            if hasattr(self, 'controller') and self.controller:
                self.controller.refresh_all_frames()

        edit_btn = tk.Button(button_frame, text="✏️ Edit Selected", command=edit_selected_order, font=('Segoe UI', 11, 'bold'), bg='#f39c12', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        approve_btn = tk.Button(button_frame, text="✅ Approve Selected", command=approved_selected_order, font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        approve_btn.pack(side=tk.LEFT, padx=(0, 10))
        cancel_btn = tk.Button(button_frame, text="✏️ Cancel Selected", command=cancel_selected_order, font=('Segoe UI', 11, 'bold'), bg='#95a5a6', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        delete_btn = tk.Button(button_frame, text="🗑️ Delete Selected", command=delete_selected_order, font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", command=refresh_orders, font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white', relief='flat', cursor='hand2', padx=20, pady=8)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))


