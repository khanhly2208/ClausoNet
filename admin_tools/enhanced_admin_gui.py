#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Enhanced Admin GUI
Complete customer management and license distribution system
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import datetime
from pathlib import Path
import threading
import webbrowser

# Import the enhanced admin system
from enhanced_admin_system import EnhancedAdminLicenseSystem
from license_key_generator import LicenseKeyGenerator

class EnhancedAdminGUI:
    """
    🎯 Enhanced Admin GUI
    Complete customer management and license distribution interface
    """

    def __init__(self):
        self.admin_system = EnhancedAdminLicenseSystem()
        self.license_generator = LicenseKeyGenerator()

        # Setup main window
        self.setup_main_window()
        self.setup_tabs()
        self.setup_styles()

        # Load initial data
        self.refresh_all_data()

    def setup_main_window(self):
        """Setup main application window"""
        self.root = ctk.CTk()
        self.root.title("🎯 ClausoNet 4.0 Pro - Enhanced Admin Panel")
        self.root.geometry("1400x900")

        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎯 ClausoNet 4.0 Pro - Enhanced Admin Panel",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=15)

        # Status frame
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="System Status: Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        self.refresh_button = ctk.CTkButton(
            self.status_frame,
            text="🔄 Refresh All",
            command=self.refresh_all_data,
            width=120
        )
        self.refresh_button.pack(side="right", padx=10, pady=5)

    def setup_tabs(self):
        """Setup tabbed interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab frames
        self.customer_tab = ttk.Frame(self.notebook)
        self.license_tab = ttk.Frame(self.notebook)
        self.activation_tab = ttk.Frame(self.notebook)
        self.email_tab = ttk.Frame(self.notebook)
        self.analytics_tab = ttk.Frame(self.notebook)

        # Add tabs
        self.notebook.add(self.customer_tab, text="👥 Customer Management")
        self.notebook.add(self.license_tab, text="🔑 License Management")
        self.notebook.add(self.activation_tab, text="⚡ Activation Control")
        self.notebook.add(self.email_tab, text="📧 Email System")
        self.notebook.add(self.analytics_tab, text="📊 Analytics")

        # Setup individual tabs
        self.setup_customer_tab()
        self.setup_license_tab()
        self.setup_activation_tab()
        self.setup_email_tab()
        self.setup_analytics_tab()

    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure treeview colors for dark theme
        style.configure("Treeview",
                       background="#2b2b2b",
                       foreground="white",
                       rowheight=25,
                       fieldbackground="#2b2b2b")
        style.map('Treeview', background=[('selected', '#22559b')])

        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       relief="flat")
        style.map("Treeview.Heading", background=[('active', '#225086')])

    def setup_customer_tab(self):
        """Setup customer management tab"""
        # Customer management frame
        customer_frame = ctk.CTkFrame(self.customer_tab)
        customer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Customer controls
        customer_controls = ctk.CTkFrame(customer_frame)
        customer_controls.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(customer_controls, text="👥 Customer Management",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(customer_controls, text="➕ Add Customer",
                     command=self.add_customer_dialog, width=120).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(customer_controls, text="✏️ Edit Customer",
                     command=self.edit_customer_dialog, width=120).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(customer_controls, text="📧 Send Email",
                     command=self.send_customer_email, width=120).pack(side="right", padx=5, pady=10)

        # Customer treeview
        columns = ("ID", "Name", "Email", "Company", "Total Spent", "Keys", "Status", "Created")
        self.customer_tree = ttk.Treeview(customer_frame, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.customer_tree.heading(col, text=col)
            if col == "ID":
                self.customer_tree.column(col, width=80)
            elif col in ["Total Spent", "Keys"]:
                self.customer_tree.column(col, width=100)
            elif col == "Status":
                self.customer_tree.column(col, width=80)
            else:
                self.customer_tree.column(col, width=150)

        # Scrollbars for customer tree
        customer_scrollbar_y = ttk.Scrollbar(customer_frame, orient="vertical", command=self.customer_tree.yview)
        customer_scrollbar_x = ttk.Scrollbar(customer_frame, orient="horizontal", command=self.customer_tree.xview)
        self.customer_tree.configure(yscrollcommand=customer_scrollbar_y.set, xscrollcommand=customer_scrollbar_x.set)

        # Pack customer tree and scrollbars
        self.customer_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        customer_scrollbar_y.pack(side="right", fill="y", pady=5)
        customer_scrollbar_x.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def setup_license_tab(self):
        """Setup license management tab"""
        # License management frame
        license_frame = ctk.CTkFrame(self.license_tab)
        license_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # License controls
        license_controls = ctk.CTkFrame(license_frame)
        license_controls.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(license_controls, text="🔑 License Management",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(license_controls, text="🎯 Generate Key",
                     command=self.generate_license_dialog, width=120).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(license_controls, text="👤 Assign to Customer",
                     command=self.assign_key_dialog, width=140).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(license_controls, text="📤 Send Key",
                     command=self.send_key_dialog, width=120).pack(side="right", padx=5, pady=10)

        # License type frame
        license_type_frame = ctk.CTkFrame(license_frame)
        license_type_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(license_type_frame, text="Quick Generate:",
                    font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=5)

        ctk.CTkButton(license_type_frame, text="📅 Trial (7 days)",
                     command=lambda: self.quick_generate("trial"), width=120).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(license_type_frame, text="📊 Monthly ($29)",
                     command=lambda: self.quick_generate("monthly"), width=120).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(license_type_frame, text="💎 Lifetime ($299)",
                     command=lambda: self.quick_generate("lifetime"), width=130).pack(side="left", padx=5, pady=5)

        # License treeview
        license_columns = ("Key", "Type", "Status", "Customer", "Created", "Expires", "Price", "Devices")
        self.license_tree = ttk.Treeview(license_frame, columns=license_columns, show="headings", height=20)

        # Configure license columns
        for col in license_columns:
            self.license_tree.heading(col, text=col)
            if col == "Key":
                self.license_tree.column(col, width=200)
            elif col in ["Price", "Devices"]:
                self.license_tree.column(col, width=80)
            elif col == "Status":
                self.license_tree.column(col, width=100)
            else:
                self.license_tree.column(col, width=120)

        # Scrollbars for license tree
        license_scrollbar_y = ttk.Scrollbar(license_frame, orient="vertical", command=self.license_tree.yview)
        license_scrollbar_x = ttk.Scrollbar(license_frame, orient="horizontal", command=self.license_tree.xview)
        self.license_tree.configure(yscrollcommand=license_scrollbar_y.set, xscrollcommand=license_scrollbar_x.set)

        # Pack license tree and scrollbars
        self.license_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        license_scrollbar_y.pack(side="right", fill="y", pady=5)
        license_scrollbar_x.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def setup_activation_tab(self):
        """Setup activation control tab"""
        # Activation frame
        activation_frame = ctk.CTkFrame(self.activation_tab)
        activation_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Activation controls
        activation_controls = ctk.CTkFrame(activation_frame)
        activation_controls.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(activation_controls, text="⚡ Activation Control",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(activation_controls, text="🔍 Check Key",
                     command=self.check_key_dialog, width=120).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(activation_controls, text="🔑 Manual Activate",
                     command=self.manual_activate_dialog, width=130).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(activation_controls, text="📋 View Logs",
                     command=self.view_activation_logs, width=120).pack(side="right", padx=5, pady=10)

        # Activation statistics frame
        activation_stats_frame = ctk.CTkFrame(activation_frame)
        activation_stats_frame.pack(fill="x", padx=10, pady=5)

        self.activation_stats_labels = {}
        stats_names = ["Total Activations", "Success Rate", "Failed Attempts", "Active Licenses"]

        for i, stat_name in enumerate(stats_names):
            stat_frame = ctk.CTkFrame(activation_stats_frame)
            stat_frame.pack(side="left", padx=10, pady=10, fill="both", expand=True)

            ctk.CTkLabel(stat_frame, text=stat_name,
                        font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
            self.activation_stats_labels[stat_name] = ctk.CTkLabel(
                stat_frame, text="0",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            self.activation_stats_labels[stat_name].pack(pady=(0, 10))

        # Recent activations
        recent_frame = ctk.CTkFrame(activation_frame)
        recent_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(recent_frame, text="📈 Recent Activations",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Recent activations treeview
        recent_columns = ("Timestamp", "License Key", "Hardware ID", "Status", "Customer")
        self.recent_tree = ttk.Treeview(recent_frame, columns=recent_columns, show="headings", height=10)

        for col in recent_columns:
            self.recent_tree.heading(col, text=col)
            if col == "License Key":
                self.recent_tree.column(col, width=200)
            elif col == "Hardware ID":
                self.recent_tree.column(col, width=180)
            else:
                self.recent_tree.column(col, width=150)

        self.recent_tree.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_email_tab(self):
        """Setup email system tab"""
        # Email frame
        email_frame = ctk.CTkFrame(self.email_tab)
        email_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Email configuration
        email_config_frame = ctk.CTkFrame(email_frame)
        email_config_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(email_config_frame, text="📧 Email Configuration",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # Email settings
        settings_frame = ctk.CTkFrame(email_config_frame)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # SMTP settings grid
        ctk.CTkLabel(settings_frame, text="SMTP Server:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.smtp_server_entry = ctk.CTkEntry(settings_frame, width=200)
        self.smtp_server_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(settings_frame, text="SMTP Port:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.smtp_port_entry = ctk.CTkEntry(settings_frame, width=100)
        self.smtp_port_entry.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(settings_frame, text="Admin Email:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.admin_email_entry = ctk.CTkEntry(settings_frame, width=200)
        self.admin_email_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(settings_frame, text="Password:").grid(row=1, column=2, padx=10, pady=5, sticky="e")
        self.admin_password_entry = ctk.CTkEntry(settings_frame, width=150, show="*")
        self.admin_password_entry.grid(row=1, column=3, padx=10, pady=5, sticky="w")

        # Email buttons
        email_buttons_frame = ctk.CTkFrame(email_config_frame)
        email_buttons_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(email_buttons_frame, text="💾 Save Config",
                     command=self.save_email_config, width=120).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(email_buttons_frame, text="🧪 Test Email",
                     command=self.test_email, width=120).pack(side="left", padx=5, pady=10)

        self.email_enabled_var = ctk.BooleanVar()
        self.email_enabled_checkbox = ctk.CTkCheckBox(
            email_buttons_frame,
            text="Enable Email System",
            variable=self.email_enabled_var
        )
        self.email_enabled_checkbox.pack(side="left", padx=20, pady=10)

        # Email templates
        templates_frame = ctk.CTkFrame(email_frame)
        templates_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(templates_frame, text="📄 Email Templates",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Template text area
        self.email_template_text = tk.Text(templates_frame, height=15, wrap=tk.WORD,
                                          bg="#2b2b2b", fg="white", insertbackground="white")
        self.email_template_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Load email configuration
        self.load_email_config()

    def setup_analytics_tab(self):
        """Setup analytics tab"""
        # Analytics frame
        analytics_frame = ctk.CTkFrame(self.analytics_tab)
        analytics_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Analytics header
        analytics_header = ctk.CTkFrame(analytics_frame)
        analytics_header.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(analytics_header, text="📊 Business Analytics",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(analytics_header, text="📊 Generate Report",
                     command=self.generate_report, width=140).pack(side="right", padx=5, pady=10)
        ctk.CTkButton(analytics_header, text="📈 Export Data",
                     command=self.export_analytics, width=120).pack(side="right", padx=5, pady=10)

        # Statistics grid
        stats_grid_frame = ctk.CTkFrame(analytics_frame)
        stats_grid_frame.pack(fill="x", padx=10, pady=5)

        self.analytics_labels = {}

        # First row of statistics
        row1_frame = ctk.CTkFrame(stats_grid_frame)
        row1_frame.pack(fill="x", padx=10, pady=5)

        stats_row1 = ["Total Revenue", "Total Customers", "Total Licenses", "Activation Rate"]
        for i, stat in enumerate(stats_row1):
            stat_frame = ctk.CTkFrame(row1_frame)
            stat_frame.pack(side="left", padx=5, pady=10, fill="both", expand=True)

            ctk.CTkLabel(stat_frame, text=stat, font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
            self.analytics_labels[stat] = ctk.CTkLabel(
                stat_frame, text="$0.00", font=ctk.CTkFont(size=18, weight="bold")
            )
            self.analytics_labels[stat].pack(pady=(0, 10))

        # Second row of statistics
        row2_frame = ctk.CTkFrame(stats_grid_frame)
        row2_frame.pack(fill="x", padx=10, pady=5)

        stats_row2 = ["Trial Keys", "Monthly Keys", "Lifetime Keys", "Active Users"]
        for i, stat in enumerate(stats_row2):
            stat_frame = ctk.CTkFrame(row2_frame)
            stat_frame.pack(side="left", padx=5, pady=10, fill="both", expand=True)

            ctk.CTkLabel(stat_frame, text=stat, font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
            self.analytics_labels[stat] = ctk.CTkLabel(
                stat_frame, text="0", font=ctk.CTkFont(size=18, weight="bold")
            )
            self.analytics_labels[stat].pack(pady=(0, 10))

        # Analytics chart placeholder
        chart_frame = ctk.CTkFrame(analytics_frame)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(chart_frame, text="📈 Revenue Trends",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.analytics_text = tk.Text(chart_frame, height=10, wrap=tk.WORD,
                                     bg="#2b2b2b", fg="white", insertbackground="white")
        self.analytics_text.pack(fill="both", expand=True, padx=10, pady=5)

    def refresh_all_data(self):
        """Refresh all data in all tabs"""
        self.update_status("Refreshing data...")

        # Refresh in background thread
        def refresh_worker():
            try:
                self.load_customers()
                self.load_licenses()
                self.load_activation_data()
                self.load_analytics_data()
                self.update_status("Data refreshed successfully")
            except Exception as e:
                self.update_status(f"Error refreshing data: {str(e)}")

        threading.Thread(target=refresh_worker, daemon=True).start()

    def update_status(self, message):
        """Update status label"""
        self.status_label.configure(text=f"Status: {message}")
        self.root.update_idletasks()

    def load_customers(self):
        """Load customers into treeview"""
        # Clear existing items
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)

        try:
            customers_file = Path("admin_data/customers_database.json")
            if customers_file.exists():
                with open(customers_file, 'r', encoding='utf-8') as f:
                    customers_db = json.load(f)

                for customer in customers_db.get("customers", []):
                    self.customer_tree.insert("", "end", values=(
                        customer["id"][:8],  # Short ID
                        customer["name"],
                        customer["email"],
                        customer.get("company", ""),
                        f"${customer.get('total_spent', 0):.2f}",
                        len(customer.get("license_keys", [])),
                        customer.get("status", "active"),
                        customer["created_at"][:10]  # Date only
                    ))
        except Exception as e:
            print(f"Error loading customers: {e}")

    def load_licenses(self):
        """Load licenses into treeview"""
        # Clear existing items
        for item in self.license_tree.get_children():
            self.license_tree.delete(item)

        try:
            enhanced_db = self.admin_system.load_enhanced_database()

            for key_data in enhanced_db.get("keys", []):
                self.license_tree.insert("", "end", values=(
                    key_data["key"],
                    key_data["type"].title(),
                    key_data.get("status", "generated"),
                    key_data.get("customer_email", "Unassigned"),
                    key_data["created_at"][:10],
                    key_data["expiry_date"][:10],
                    f"${key_data.get('price', 0):.2f}",
                    f"{len(key_data.get('hardware_ids', []))}/{key_data.get('max_devices', 1)}"
                ))
        except Exception as e:
            print(f"Error loading licenses: {e}")

    def load_activation_data(self):
        """Load activation data"""
        try:
            # Load activation log
            activation_log_file = Path("admin_data/activation_log.json")
            if activation_log_file.exists():
                with open(activation_log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)

                # Update activation statistics
                activations = log_data.get("activations", [])
                failed_attempts = log_data.get("failed_attempts", [])

                total_activations = len(activations)
                total_attempts = total_activations + len(failed_attempts)
                success_rate = (total_activations / total_attempts * 100) if total_attempts > 0 else 0

                self.activation_stats_labels["Total Activations"].configure(text=str(total_activations))
                self.activation_stats_labels["Success Rate"].configure(text=f"{success_rate:.1f}%")
                self.activation_stats_labels["Failed Attempts"].configure(text=str(len(failed_attempts)))

                # Load recent activations
                for item in self.recent_tree.get_children():
                    self.recent_tree.delete(item)

                # Show last 20 activations
                recent_activations = sorted(activations, key=lambda x: x["timestamp"], reverse=True)[:20]

                for activation in recent_activations:
                    self.recent_tree.insert("", "end", values=(
                        activation["timestamp"][:19].replace('T', ' '),
                        activation["license_key"],
                        activation["data"].get("hardware_id", "")[:20] + "...",
                        "Success",
                        activation["data"].get("customer_email", "Unknown")
                    ))

        except Exception as e:
            print(f"Error loading activation data: {e}")

    def load_analytics_data(self):
        """Load analytics data"""
        try:
            stats = self.admin_system.get_license_statistics()

            # Update analytics labels
            self.analytics_labels["Total Revenue"].configure(text=f"${stats.get('total_revenue', 0):.2f}")
            self.analytics_labels["Total Customers"].configure(text=str(stats.get('total_customers', 0)))
            self.analytics_labels["Total Licenses"].configure(text=str(stats.get('total_keys', 0)))
            self.analytics_labels["Activation Rate"].configure(text=f"{stats.get('activation_rate', 0):.1f}%")

            # Update key type statistics
            key_types = stats.get('key_types', {})
            self.analytics_labels["Trial Keys"].configure(text=str(key_types.get('trial', 0)))
            self.analytics_labels["Monthly Keys"].configure(text=str(key_types.get('monthly', 0)))
            self.analytics_labels["Lifetime Keys"].configure(text=str(key_types.get('lifetime', 0)))
            self.analytics_labels["Active Users"].configure(text=str(stats.get('activated_keys', 0)))

            # Update analytics text
            self.analytics_text.delete(1.0, tk.END)
            analytics_report = f"""
📊 BUSINESS ANALYTICS REPORT
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 REVENUE BREAKDOWN:
• Total Revenue: ${stats.get('total_revenue', 0):.2f}
• Trial Keys: {key_types.get('trial', 0)} keys
• Monthly Keys: {key_types.get('monthly', 0)} keys (${key_types.get('monthly', 0) * 29:.2f})
• Lifetime Keys: {key_types.get('lifetime', 0)} keys (${key_types.get('lifetime', 0) * 299:.2f})

👥 CUSTOMER METRICS:
• Total Customers: {stats.get('total_customers', 0)}
• Total Licenses: {stats.get('total_keys', 0)}
• Activated Licenses: {stats.get('activated_keys', 0)}
• Activation Rate: {stats.get('activation_rate', 0):.1f}%

⚡ ACTIVATION PERFORMANCE:
• Total Activations: {stats.get('total_activations', 0)}
• Failed Attempts: {stats.get('failed_activations', 0)}
• Success Rate: {stats.get('success_rate', 0):.1f}%

📈 GROWTH OPPORTUNITIES:
• Focus on converting trial users to paid licenses
• Improve activation success rate
• Implement customer retention strategies
• Consider promotional pricing for monthly licenses
"""
            self.analytics_text.insert(1.0, analytics_report)

        except Exception as e:
            print(f"Error loading analytics: {e}")

    def load_email_config(self):
        """Load email configuration"""
        config = self.admin_system.email_config

        self.smtp_server_entry.insert(0, config.get("smtp_server", ""))
        self.smtp_port_entry.insert(0, str(config.get("smtp_port", "")))
        self.admin_email_entry.insert(0, config.get("admin_email", ""))
        self.admin_password_entry.insert(0, config.get("admin_password", ""))
        self.email_enabled_var.set(config.get("enabled", False))

        # Load default email template
        template = """Dear {customer_name},

Thank you for your purchase of ClausoNet 4.0 Pro!

🔑 YOUR LICENSE KEY: {license_key}

📋 LICENSE DETAILS:
• Type: {license_type}
• Duration: {duration_days} days
• Expires: {expiry_date}
• Price: ${price}

🚀 ACTIVATION INSTRUCTIONS:
1. Download ClausoNet 4.0 Pro
2. Run the application
3. Enter your license key when prompted
4. Enjoy all premium features!

Best regards,
ClausoNet Team"""

        self.email_template_text.insert(1.0, template)

    # Dialog methods
    def add_customer_dialog(self):
        """Show add customer dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("➕ Add New Customer")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Customer form
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="➕ Add New Customer",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Form fields
        fields = {
            "name": ctk.CTkEntry(form_frame, placeholder_text="Customer Name"),
            "email": ctk.CTkEntry(form_frame, placeholder_text="Email Address"),
            "phone": ctk.CTkEntry(form_frame, placeholder_text="Phone Number"),
            "company": ctk.CTkEntry(form_frame, placeholder_text="Company Name")
        }

        for field_name, entry in fields.items():
            ctk.CTkLabel(form_frame, text=field_name.replace("_", " ").title() + ":").pack(anchor="w", padx=20, pady=(10, 5))
            entry.pack(fill="x", padx=20, pady=(0, 10))

        # Notes field
        ctk.CTkLabel(form_frame, text="Notes:").pack(anchor="w", padx=20, pady=(10, 5))
        notes_text = tk.Text(form_frame, height=5, wrap=tk.WORD)
        notes_text.pack(fill="x", padx=20, pady=(0, 10))

        # Buttons
        button_frame = ctk.CTkFrame(form_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        def save_customer():
            customer_data = {}
            for field_name, entry in fields.items():
                customer_data[field_name] = entry.get()
            customer_data["notes"] = notes_text.get(1.0, tk.END).strip()

            if customer_data["name"] and customer_data["email"]:
                customer_id = self.admin_system.add_customer(customer_data)
                if customer_id:
                    messagebox.showinfo("Success", "Customer added successfully!")
                    dialog.destroy()
                    self.load_customers()
                else:
                    messagebox.showerror("Error", "Failed to add customer")
            else:
                messagebox.showerror("Error", "Name and Email are required")

        ctk.CTkButton(button_frame, text="💾 Save Customer", command=save_customer).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="❌ Cancel", command=dialog.destroy).pack(side="right", padx=10)

    def generate_license_dialog(self):
        """Show generate license dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("🎯 Generate License Key")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # License form
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="🎯 Generate License Key",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # License type
        ctk.CTkLabel(form_frame, text="License Type:").pack(anchor="w", padx=20, pady=(10, 5))
        license_type_var = ctk.StringVar(value="trial")
        license_type_menu = ctk.CTkOptionMenu(form_frame, variable=license_type_var,
                                             values=["trial", "monthly", "lifetime"])
        license_type_menu.pack(fill="x", padx=20, pady=(0, 10))

        # Duration (for custom)
        ctk.CTkLabel(form_frame, text="Duration (days):").pack(anchor="w", padx=20, pady=(10, 5))
        duration_entry = ctk.CTkEntry(form_frame, placeholder_text="Auto-calculated")
        duration_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Price
        ctk.CTkLabel(form_frame, text="Price ($):").pack(anchor="w", padx=20, pady=(10, 5))
        price_entry = ctk.CTkEntry(form_frame, placeholder_text="Auto-calculated")
        price_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Max devices
        ctk.CTkLabel(form_frame, text="Max Devices:").pack(anchor="w", padx=20, pady=(10, 5))
        max_devices_entry = ctk.CTkEntry(form_frame, placeholder_text="1")
        max_devices_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Features
        ctk.CTkLabel(form_frame, text="Features:").pack(anchor="w", padx=20, pady=(10, 5))
        features_frame = ctk.CTkFrame(form_frame)
        features_frame.pack(fill="x", padx=20, pady=(0, 10))

        feature_vars = {}
        features = ["video_generation", "batch_processing", "premium_templates", "advanced_ai", "priority_support"]

        for feature in features:
            var = ctk.BooleanVar(value=True)
            feature_vars[feature] = var
            ctk.CTkCheckBox(features_frame, text=feature.replace("_", " ").title(),
                           variable=var).pack(anchor="w", padx=10, pady=2)

        # Buttons
        button_frame = ctk.CTkFrame(form_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        def generate_license():
            license_type = license_type_var.get()

            # Get duration and price
            duration = duration_entry.get()
            if not duration:
                duration_map = {"trial": 7, "monthly": 30, "lifetime": 365*10}
                duration = duration_map.get(license_type, 30)
            else:
                duration = int(duration)

            price = price_entry.get()
            if not price:
                price_map = {"trial": 0, "monthly": 29, "lifetime": 299}
                price = price_map.get(license_type, 29)
            else:
                price = float(price)

            max_devices = int(max_devices_entry.get() or "1")

            # Get selected features
            selected_features = [feature for feature, var in feature_vars.items() if var.get()]

            # Generate license
            license_data = self.license_generator.generate_license_key(
                license_type=license_type,
                duration_days=duration,
                max_devices=max_devices,
                features=selected_features,
                price=price
            )

            if license_data:
                messagebox.showinfo("Success", f"License generated!\nKey: {license_data['key']}")
                dialog.destroy()
                self.load_licenses()
            else:
                messagebox.showerror("Error", "Failed to generate license")

        ctk.CTkButton(button_frame, text="🎯 Generate", command=generate_license).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="❌ Cancel", command=dialog.destroy).pack(side="right", padx=10)

    def quick_generate(self, license_type):
        """Quick generate license of specific type"""
        type_config = {
            "trial": {"duration": 7, "price": 0, "features": ["video_generation"]},
            "monthly": {"duration": 30, "price": 29, "features": ["video_generation", "batch_processing", "premium_templates"]},
            "lifetime": {"duration": 3650, "price": 299, "features": ["video_generation", "batch_processing", "premium_templates", "advanced_ai", "priority_support"]}
        }

        config = type_config[license_type]

        license_data = self.license_generator.generate_license_key(
            license_type=license_type,
            duration_days=config["duration"],
            max_devices=1,
            features=config["features"],
            price=config["price"]
        )

        if license_data:
            messagebox.showinfo("Success", f"{license_type.title()} license generated!\nKey: {license_data['key']}")
            self.load_licenses()
        else:
            messagebox.showerror("Error", "Failed to generate license")

    def assign_key_dialog(self):
        """Show assign key to customer dialog"""
        # Get selected license
        selection = self.license_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a license key first")
            return

        license_key = self.license_tree.item(selection[0])['values'][0]

        # Customer selection dialog
        customer_email = simpledialog.askstring("Assign Key", "Enter customer email:")
        if customer_email:
            if self.admin_system.assign_key_to_customer(license_key, customer_email):
                messagebox.showinfo("Success", "Key assigned successfully!")
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", "Failed to assign key")

    def send_key_dialog(self):
        """Show send key via email dialog"""
        # Get selected license
        selection = self.license_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a license key first")
            return

        license_key = self.license_tree.item(selection[0])['values'][0]
        customer_email = self.license_tree.item(selection[0])['values'][3]

        if customer_email == "Unassigned":
            messagebox.showerror("Error", "Please assign key to customer first")
            return

        # Send email
        if self.admin_system.send_key_to_customer(license_key, customer_email):
            messagebox.showinfo("Success", "Email sent successfully!")
        else:
            messagebox.showerror("Error", "Failed to send email")

    def check_key_dialog(self):
        """Show check key dialog"""
        license_key = simpledialog.askstring("Check Key", "Enter license key to check:")
        if license_key:
            hardware_id = simpledialog.askstring("Hardware ID", "Enter hardware ID (optional):")

            if hardware_id:
                result = self.admin_system.validate_license_for_user(license_key, hardware_id)
            else:
                # Just check if key exists
                enhanced_db = self.admin_system.load_enhanced_database()
                key_data = None
                for key in enhanced_db.get("keys", []):
                    if key["key"] == license_key:
                        key_data = key
                        break

                if key_data:
                    result = {"valid": True, "key_data": key_data}
                else:
                    result = {"valid": False, "error": "Key not found"}

            # Show result
            if result["valid"]:
                key_data = result.get("key_data", {})
                info = f"""
Key: {license_key}
Type: {key_data.get('type', 'Unknown')}
Status: {key_data.get('status', 'Unknown')}
Customer: {key_data.get('customer_email', 'Unassigned')}
Created: {key_data.get('created_at', 'Unknown')[:10]}
Expires: {key_data.get('expiry_date', 'Unknown')[:10]}
Devices: {len(key_data.get('hardware_ids', []))}/{key_data.get('max_devices', 1)}
Price: ${key_data.get('price', 0):.2f}
"""
                messagebox.showinfo("Key Information", info)
            else:
                messagebox.showerror("Invalid Key", result.get("error", "Unknown error"))

    def manual_activate_dialog(self):
        """Show manual activation dialog"""
        license_key = simpledialog.askstring("Manual Activation", "Enter license key:")
        if license_key:
            hardware_id = simpledialog.askstring("Hardware ID", "Enter hardware ID:")
            if hardware_id:
                result = self.admin_system.activate_license_for_user(license_key, hardware_id)

                if result["valid"]:
                    messagebox.showinfo("Success", "License activated successfully!")
                    self.refresh_all_data()
                else:
                    messagebox.showerror("Error", result.get("error", "Activation failed"))

    def view_activation_logs(self):
        """Show activation logs window"""
        logs_window = ctk.CTkToplevel(self.root)
        logs_window.title("📋 Activation Logs")
        logs_window.geometry("1000x600")

        # Logs text area
        logs_text = tk.Text(logs_window, wrap=tk.WORD, bg="#2b2b2b", fg="white")
        logs_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Load and display logs
        try:
            activation_log_file = Path("admin_data/activation_log.json")
            if activation_log_file.exists():
                with open(activation_log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)

                logs_content = "📋 ACTIVATION LOGS\n" + "="*50 + "\n\n"

                # Successful activations
                logs_content += "✅ SUCCESSFUL ACTIVATIONS:\n"
                for activation in log_data.get("activations", []):
                    logs_content += f"• {activation['timestamp'][:19]} - Key: {activation['license_key']}\n"
                    logs_content += f"  Hardware: {activation['data'].get('hardware_id', '')[:30]}...\n\n"

                logs_content += "\n❌ FAILED ATTEMPTS:\n"
                for failed in log_data.get("failed_attempts", []):
                    logs_content += f"• {failed['timestamp'][:19]} - Key: {failed['license_key']}\n"
                    logs_content += f"  Error: {failed['data'].get('error', 'Unknown')}\n\n"

                logs_text.insert(1.0, logs_content)
        except Exception as e:
            logs_text.insert(1.0, f"Error loading logs: {e}")

    def save_email_config(self):
        """Save email configuration"""
        config = {
            "smtp_server": self.smtp_server_entry.get(),
            "smtp_port": int(self.smtp_port_entry.get() or "587"),
            "admin_email": self.admin_email_entry.get(),
            "admin_password": self.admin_password_entry.get(),
            "enabled": self.email_enabled_var.get()
        }

        if self.admin_system.save_email_config(config):
            messagebox.showinfo("Success", "Email configuration saved!")
        else:
            messagebox.showerror("Error", "Failed to save configuration")

    def test_email(self):
        """Test email configuration"""
        test_email = simpledialog.askstring("Test Email", "Enter test email address:")
        if test_email:
            # Send test email
            success = self.admin_system.send_key_to_customer(
                "TEST-KEY-123", test_email, "Test User"
            )

            if success:
                messagebox.showinfo("Success", "Test email sent successfully!")
            else:
                messagebox.showerror("Error", "Failed to send test email")

    def edit_customer_dialog(self):
        """Show edit customer dialog"""
        # Get selected customer
        selection = self.customer_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a customer first")
            return

        messagebox.showinfo("Feature", "Customer editing feature coming soon!")

    def send_customer_email(self):
        """Send email to selected customer"""
        # Get selected customer
        selection = self.customer_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a customer first")
            return

        customer_email = self.customer_tree.item(selection[0])['values'][2]

        # Simple email dialog
        message = simpledialog.askstring("Send Email", f"Message for {customer_email}:")
        if message:
            messagebox.showinfo("Feature", "Custom email feature coming soon!")

    def generate_report(self):
        """Generate business report"""
        messagebox.showinfo("Feature", "Advanced reporting feature coming soon!")

    def export_analytics(self):
        """Export analytics data"""
        messagebox.showinfo("Feature", "Data export feature coming soon!")

    def run(self):
        """Run the admin GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnhancedAdminGUI()
    app.run()
