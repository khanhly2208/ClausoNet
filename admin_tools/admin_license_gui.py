#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin License Management GUI
Professional interface for license key management
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import time
from datetime import datetime, timedelta
import os
import sys
import re

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ Warning: pandas not installed. Excel export will be disabled.")

# Try to import pyperclip for clipboard operations
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("⚠️ Warning: pyperclip not installed. Using tkinter clipboard.")

# Import the license generator
try:
    from license_key_generator import LicenseKeyGenerator
except ImportError:
    print("❌ Error: license_key_generator.py not found in the same directory")
    sys.exit(1)

# Import email request handler
try:
    from email_request_handler import EmailRequestHandler
    EMAIL_HANDLER_AVAILABLE = True
except ImportError:
    EMAIL_HANDLER_AVAILABLE = False
    print("⚠️ Warning: email_request_handler.py not found. Email request processing will be disabled.")

class AdminLicenseGUI:
    def __init__(self):
        # Initialize the license generator
        try:
            self.generator = LicenseKeyGenerator()
            print("✅ License generator initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing license generator: {e}")
            # Create basic generator anyway
            try:
                self.generator = LicenseKeyGenerator()
            except:
                print("❌ Critical error: Cannot initialize license system")
                return

        # Initialize email request handler
        self.email_handler = None
        if EMAIL_HANDLER_AVAILABLE:
            try:
                self.email_handler = EmailRequestHandler()
                print("✅ Email request handler initialized successfully")
            except Exception as e:
                print(f"⚠️ Warning: Email request handler initialization failed: {e}")

        # Setup main window
        self.setup_main_window()
        self.create_interface()

        # Safely refresh data
        try:
            self.refresh_data()
            print("✅ Interface loaded successfully")
        except Exception as e:
            print(f"⚠️ Warning: Some data refresh failed: {e}")
            # Continue anyway with empty interface

    def setup_main_window(self):
        """Setup main window"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("🎯 ClausoNet 4.0 Pro - License Admin")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Set window icon and taskbar properties
        try:
            # Set window icon if available - check multiple paths
            icon_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico"),  # ../assets/icon.ico
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico"),             # ../icon.ico
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "gv.ico"),               # ../gv.ico
                os.path.join(os.path.dirname(__file__), "icon.ico"),                              # admin_tools/icon.ico
            ]

            icon_set = False
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    print(f"✅ Set window icon: {icon_path}")
                    icon_set = True
                    break

            if not icon_set:
                print(f"⚠️ No icon file found, using default")
                # Create a simple icon from text if no icon file exists
                self.create_default_icon()
        except Exception as e:
            print(f"⚠️ Warning: Could not set window icon: {e}")

        # Ensure window appears on taskbar and gets focus
        self.root.attributes('-topmost', True)  # Temporarily on top
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Remove topmost after showing

        # Force window to appear on taskbar
        self.root.lift()
        self.root.focus_force()

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (900 // 2)
        self.root.geometry(f"1400x900+{x}+{y}")

        # Bind keyboard shortcuts
        self.root.bind('<Control-c>', lambda e: self.copy_key_only())
        self.root.bind('<Control-Shift-C>', lambda e: self.copy_key_full_info())
        self.root.bind('<Control-s>', lambda e: self.save_key_to_file())
        self.root.bind('<F5>', lambda e: self.refresh_data())

    def create_default_icon(self):
        """Create a default icon using tkinter only"""
        try:
            # For Windows, try to set a default system icon
            if os.name == 'nt':  # Windows
                import ctypes
                # Set window to show in taskbar properly
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ClausoNet.AdminTools.1.0")

            # Set window title properly for taskbar
            self.root.title("🎯 ClausoNet 4.0 Pro - License Admin")

            print("✅ Applied default taskbar settings")
        except Exception as e:
            print(f"⚠️ Warning: Could not set default icon/taskbar: {e}")
            # Fallback - just ensure window title is set
            self.root.title("ClausoNet 4.0 Pro - License Admin")

    def create_interface(self):
        """Create the main interface"""
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎯 ClausoNet 4.0 Pro - License Management System",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_key_generation_tab()
        self.create_customer_management_tab()
        self.create_key_management_tab()
        self.create_email_requests_tab()
        self.create_statistics_tab()
        self.create_settings_tab()

    def create_key_generation_tab(self):
        """Tab for generating license keys"""
        # Create tab frame
        key_gen_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(key_gen_frame, text="🔑 Generate Keys")

        # Content frame with scrollable
        content_frame = ctk.CTkScrollableFrame(key_gen_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Trial Key Section
        trial_section = ctk.CTkFrame(content_frame)
        trial_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(trial_section, text="🔍 Trial Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        trial_input_frame = ctk.CTkFrame(trial_section)
        trial_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(trial_input_frame, text="Duration (days):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.trial_days_entry = ctk.CTkEntry(trial_input_frame, placeholder_text="7 (minimum)")
        self.trial_days_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(trial_input_frame, text="(Min: 7 days)", font=ctk.CTkFont(size=10), text_color="gray").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        ctk.CTkButton(
            trial_input_frame,
            text="Generate Trial Key",
            command=self.generate_trial_key,
            fg_color="#FF6B35"
        ).grid(row=0, column=3, padx=20, pady=5)

        # Monthly Key Section
        monthly_section = ctk.CTkFrame(content_frame)
        monthly_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(monthly_section, text="📅 Monthly Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        monthly_input_frame = ctk.CTkFrame(monthly_section)
        monthly_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(monthly_input_frame, text="Months:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.monthly_months_entry = ctk.CTkEntry(monthly_input_frame, placeholder_text="1")
        self.monthly_months_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(monthly_input_frame, text="Price ($):").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.monthly_price_entry = ctk.CTkEntry(monthly_input_frame, placeholder_text="29.99")
        self.monthly_price_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkButton(
            monthly_input_frame,
            text="Generate Monthly Key",
            command=self.generate_monthly_key,
            fg_color="#4ECDC4"
        ).grid(row=0, column=4, padx=20, pady=5)

        # Quarterly Key Section
        quarterly_section = ctk.CTkFrame(content_frame)
        quarterly_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(quarterly_section, text="📅 Quarterly Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        quarterly_input_frame = ctk.CTkFrame(quarterly_section)
        quarterly_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(quarterly_input_frame, text="Quarters:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.quarterly_quarters_entry = ctk.CTkEntry(quarterly_input_frame, placeholder_text="1")
        self.quarterly_quarters_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(quarterly_input_frame, text="Price ($):").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.quarterly_price_entry = ctk.CTkEntry(quarterly_input_frame, placeholder_text="79.99")
        self.quarterly_price_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkButton(
            quarterly_input_frame,
            text="Generate Quarterly Key",
            command=self.generate_quarterly_key,
            fg_color="#45B7D1"
        ).grid(row=0, column=4, padx=20, pady=5)

        # Lifetime Key Section
        lifetime_section = ctk.CTkFrame(content_frame)
        lifetime_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(lifetime_section, text="🎯 Lifetime Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        lifetime_input_frame = ctk.CTkFrame(lifetime_section)
        lifetime_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(lifetime_input_frame, text="Price ($):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.lifetime_price_entry = ctk.CTkEntry(lifetime_input_frame, placeholder_text="299.99")
        self.lifetime_price_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkButton(
            lifetime_input_frame,
            text="Generate Lifetime Key",
            command=self.generate_lifetime_key,
            fg_color="#F7DC6F"
        ).grid(row=0, column=2, padx=20, pady=5)

        # Multi-Device Key Section
        multi_section = ctk.CTkFrame(content_frame)
        multi_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(multi_section, text="🖥️ Multi-Device Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        multi_input_frame = ctk.CTkFrame(multi_section)
        multi_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(multi_input_frame, text="Max Devices:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.multi_devices_entry = ctk.CTkEntry(multi_input_frame, placeholder_text="6")
        self.multi_devices_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(multi_input_frame, text="Duration (days):").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.multi_days_entry = ctk.CTkEntry(multi_input_frame, placeholder_text="365")
        self.multi_days_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkLabel(multi_input_frame, text="Price ($):").grid(row=0, column=4, padx=10, pady=5, sticky="w")
        self.multi_price_entry = ctk.CTkEntry(multi_input_frame, placeholder_text="499.99")
        self.multi_price_entry.grid(row=0, column=5, padx=10, pady=5)

        ctk.CTkButton(
            multi_input_frame,
            text="Generate Multi-Device Key",
            command=self.generate_multi_device_key,
            fg_color="#E74C3C"
        ).grid(row=0, column=6, padx=20, pady=5)

        # Generated Key Display
        self.generated_key_frame = ctk.CTkFrame(content_frame)
        self.generated_key_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(self.generated_key_frame, text="🔑 Generated Key", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Add shortcut info
        shortcut_info = ctk.CTkLabel(
            self.generated_key_frame,
            text="💡 Shortcuts: Double-click/Ctrl+C (Copy Key), Right-click (Menu), Ctrl+Shift+C (Copy All), Ctrl+S (Save), F5 (Refresh)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        shortcut_info.pack(pady=(0, 5))

        self.generated_key_display = ctk.CTkTextbox(self.generated_key_frame, height=100)
        self.generated_key_display.pack(fill="x", padx=20, pady=10)

        # Bind double-click to copy key
        self.generated_key_display.bind("<Double-Button-1>", lambda e: self.copy_key_only())

        # Create context menu for textbox
        self.create_context_menu()

        # Copy Key Buttons Section
        copy_buttons_frame = ctk.CTkFrame(self.generated_key_frame)
        copy_buttons_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            copy_buttons_frame,
            text="📋 Copy Key Only",
            command=self.copy_key_only,
            fg_color="#17A2B8",
            width=150
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            copy_buttons_frame,
            text="📋 Copy Full Info",
            command=self.copy_key_full_info,
            fg_color="#6C757D",
            width=150
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            copy_buttons_frame,
            text="💾 Save to File",
            command=self.save_key_to_file,
            fg_color="#28A745",
            width=150
        ).pack(side="left", padx=10)

        # Copy status label
        self.copy_status_label = ctk.CTkLabel(copy_buttons_frame, text="", font=ctk.CTkFont(size=12))
        self.copy_status_label.pack(side="right", padx=10)

        # Send to Customer Section
        self.send_customer_frame = ctk.CTkFrame(content_frame)
        self.send_customer_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(self.send_customer_frame, text="📧 Send Key to Customer", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        send_input_frame = ctk.CTkFrame(self.send_customer_frame)
        send_input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(send_input_frame, text="Customer Email:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.send_email_entry = ctk.CTkEntry(send_input_frame, placeholder_text="customer@example.com", width=250)
        self.send_email_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(send_input_frame, text="Customer Name:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.send_name_entry = ctk.CTkEntry(send_input_frame, placeholder_text="Customer Name", width=200)
        self.send_name_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkButton(
            send_input_frame,
            text="📤 Send Key via Email",
            command=self.send_key_to_customer,
            fg_color="#3498DB",
            width=150
        ).grid(row=0, column=4, padx=20, pady=5)

        # Email status display
        self.email_status_label = ctk.CTkLabel(self.send_customer_frame, text="", font=ctk.CTkFont(size=12))
        self.email_status_label.pack(pady=5)

    def create_customer_management_tab(self):
        """Tab for customer management"""
        customer_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(customer_frame, text="👤 Customers")

        # Top section - Add Customer
        add_customer_frame = ctk.CTkFrame(customer_frame)
        add_customer_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(add_customer_frame, text="➕ Add New Customer", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        customer_input_frame = ctk.CTkFrame(add_customer_frame)
        customer_input_frame.pack(fill="x", padx=20, pady=10)

        # Customer input fields
        ctk.CTkLabel(customer_input_frame, text="Email:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.customer_email_entry = ctk.CTkEntry(customer_input_frame, placeholder_text="customer@example.com", width=200)
        self.customer_email_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(customer_input_frame, text="Name:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.customer_name_entry = ctk.CTkEntry(customer_input_frame, placeholder_text="John Doe", width=150)
        self.customer_name_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkLabel(customer_input_frame, text="Phone:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.customer_phone_entry = ctk.CTkEntry(customer_input_frame, placeholder_text="+1234567890", width=150)
        self.customer_phone_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(customer_input_frame, text="Company:").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.customer_company_entry = ctk.CTkEntry(customer_input_frame, placeholder_text="Company Inc.", width=150)
        self.customer_company_entry.grid(row=1, column=3, padx=10, pady=5)

        ctk.CTkButton(
            customer_input_frame,
            text="Add Customer",
            command=self.add_customer,
            fg_color="#2ECC71"
        ).grid(row=1, column=4, padx=20, pady=5)

        # Customer list
        list_frame = ctk.CTkFrame(customer_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(list_frame, text="👥 Customer List", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # Create treeview for customers
        columns = ("Email", "Name", "Phone", "Company", "Keys", "Total Spent", "Last Contact")
        self.customer_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=120)

        # Scrollbar for treeview
        customer_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=customer_scrollbar.set)

        self.customer_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        customer_scrollbar.pack(side="right", fill="y", pady=10)

    def create_key_management_tab(self):
        """Tab for key management"""
        key_mgmt_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(key_mgmt_frame, text="🔐 Key Management")

        # Top controls
        controls_frame = ctk.CTkFrame(key_mgmt_frame)
        controls_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(controls_frame, text="🔍 Search & Actions", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        search_frame = ctk.CTkFrame(controls_frame)
        search_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(search_frame, text="Search Key:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.search_key_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter license key", width=200)
        self.search_key_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.search_key,
            fg_color="#3498DB"
        ).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkButton(
            search_frame,
            text="Refresh List",
            command=self.refresh_key_list,
            fg_color="#95A5A6"
        ).grid(row=0, column=3, padx=10, pady=5)

        # Key assignment section
        assign_frame = ctk.CTkFrame(controls_frame)
        assign_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(assign_frame, text="Assign Key:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.assign_key_entry = ctk.CTkEntry(assign_frame, placeholder_text="License key", width=150)
        self.assign_key_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(assign_frame, text="To Email:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.assign_email_entry = ctk.CTkEntry(assign_frame, placeholder_text="customer@email.com", width=200)
        self.assign_email_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkButton(
            assign_frame,
            text="Assign Key",
            command=self.assign_key,
            fg_color="#E67E22"
        ).grid(row=0, column=4, padx=10, pady=5)

        ctk.CTkButton(
            assign_frame,
            text="Send Email",
            command=self.send_key_email,
            fg_color="#9B59B6"
        ).grid(row=0, column=5, padx=10, pady=5)

        # Keys list
        keys_list_frame = ctk.CTkFrame(key_mgmt_frame)
        keys_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(keys_list_frame, text="🔑 License Keys", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # Create treeview for keys
        key_columns = ("Key", "Type", "Status", "Customer", "Created", "Expires", "Price", "Devices")
        self.keys_tree = ttk.Treeview(keys_list_frame, columns=key_columns, show="headings", height=15)

        for col in key_columns:
            self.keys_tree.heading(col, text=col)
            self.keys_tree.column(col, width=120)

        # Scrollbar for keys treeview
        keys_scrollbar = ttk.Scrollbar(keys_list_frame, orient="vertical", command=self.keys_tree.yview)
        self.keys_tree.configure(yscrollcommand=keys_scrollbar.set)

        self.keys_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        keys_scrollbar.pack(side="right", fill="y", pady=10)

    def create_statistics_tab(self):
        """Tab for statistics and reports"""
        stats_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")

        # Stats overview
        overview_frame = ctk.CTkFrame(stats_frame)
        overview_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(overview_frame, text="📈 Overview", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        self.stats_display = ctk.CTkTextbox(overview_frame, height=200)
        self.stats_display.pack(fill="x", padx=20, pady=10)

        # Reports section
        reports_frame = ctk.CTkFrame(stats_frame)
        reports_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(reports_frame, text="📊 Detailed Report", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        report_controls = ctk.CTkFrame(reports_frame)
        report_controls.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            report_controls,
            text="Generate Report",
            command=self.generate_report,
            fg_color="#16A085"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            report_controls,
            text="Export to Excel",
            command=self.export_to_excel,
            fg_color="#27AE60"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            report_controls,
            text="Refresh Stats",
            command=self.refresh_statistics,
            fg_color="#3498DB"
        ).pack(side="left", padx=10)

        self.report_display = ctk.CTkTextbox(reports_frame, height=300)
        self.report_display.pack(fill="both", expand=True, padx=20, pady=10)

    def create_settings_tab(self):
        """Tab for settings"""
        settings_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")

        # Email settings
        email_frame = ctk.CTkFrame(settings_frame)
        email_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(email_frame, text="📧 Email Configuration", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        email_config_frame = ctk.CTkFrame(email_frame)
        email_config_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(email_config_frame, text="SMTP Server:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.smtp_server_entry = ctk.CTkEntry(email_config_frame, placeholder_text="smtp.gmail.com")
        self.smtp_server_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(email_config_frame, text="SMTP Port:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.smtp_port_entry = ctk.CTkEntry(email_config_frame, placeholder_text="587")
        self.smtp_port_entry.grid(row=0, column=3, padx=10, pady=5)

        ctk.CTkLabel(email_config_frame, text="Admin Email:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.admin_email_entry = ctk.CTkEntry(email_config_frame, placeholder_text="admin@clausonet.com", width=200)
        self.admin_email_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(email_config_frame, text="Password:").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.admin_password_entry = ctk.CTkEntry(email_config_frame, placeholder_text="Password", show="*")
        self.admin_password_entry.grid(row=1, column=3, padx=10, pady=5)

        ctk.CTkButton(
            email_config_frame,
            text="Save Email Settings",
            command=self.save_email_settings,
            fg_color="#E74C3C"
        ).grid(row=2, column=1, columnspan=2, padx=10, pady=20)

        # Database management
        db_frame = ctk.CTkFrame(settings_frame)
        db_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(db_frame, text="🗄️ Database Management", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        db_controls_frame = ctk.CTkFrame(db_frame)
        db_controls_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            db_controls_frame,
            text="Backup Database",
            command=self.backup_database,
            fg_color="#F39C12"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            db_controls_frame,
            text="Restore Database",
            command=self.restore_database,
            fg_color="#8E44AD"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            db_controls_frame,
            text="Clear All Data",
            command=self.clear_database,
            fg_color="#E74C3C"
        ).pack(side="left", padx=10)

    def generate_trial_key(self):
        """Generate trial key"""
        try:
            input_value = self.trial_days_entry.get()

            # ✅ VALIDATION: Kiểm tra input có phải số không
            try:
                days = int(input_value or "7")
            except ValueError:
                messagebox.showerror("Input Error",
                    f"Vui lòng nhập số ngày hợp lệ!\n"
                    f"Bạn đã nhập: '{input_value}'\n\n"
                    f"Ví dụ: 7, 14, 30")
                return

            # ✅ VALIDATION: Chỉ cho phép tạo trial key từ 7 ngày trở lên
            if days < 7:
                messagebox.showerror("Validation Error",
                    f"Trial key phải có tối thiểu 7 ngày!\n"
                    f"Bạn đã nhập: {days} ngày\n\n"
                    f"Vui lòng nhập số ngày >= 7")
                return

            # ✅ VALIDATION: Giới hạn tối đa hợp lý (tránh tạo key quá dài)
            if days > 365:
                messagebox.showerror("Validation Error",
                    f"Trial key không nên quá 365 ngày!\n"
                    f"Bạn đã nhập: {days} ngày\n\n"
                    f"Sử dụng các loại key khác cho thời gian dài hơn.")
                return

            # 🐛 DEBUG: Print actual input and parsed values
            print(f"🐛 DEBUG Trial Key Generation:")
            print(f"   Raw input: '{input_value}'")
            print(f"   Parsed days: {days}")

            key_data = self.generator.generate_trial_key(days)

            # 🐛 DEBUG: Print generated key data
            print(f"   Generated key: {key_data['key']}")
            print(f"   Key duration: {key_data['duration_days']} days")
            print(f"   Key type: {key_data['type']}")

            self.display_generated_key(key_data)
            self.refresh_data()
            messagebox.showinfo("Success", f"Trial key generated: {key_data['key']} ({key_data['duration_days']} days)")

        except Exception as e:
            print(f"🐛 DEBUG Trial Key Error: {e}")
            messagebox.showerror("Error", f"Failed to generate trial key: {e}")

    def generate_monthly_key(self):
        """Generate monthly key"""
        try:
            months = int(self.monthly_months_entry.get() or "1")
            price = float(self.monthly_price_entry.get() or "29.99")
            key_data = self.generator.generate_monthly_key(months, price)

            self.display_generated_key(key_data)
            self.refresh_data()
            messagebox.showinfo("Success", f"Monthly key generated: {key_data['key']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate monthly key: {e}")

    def generate_quarterly_key(self):
        """Generate quarterly key"""
        try:
            quarters = int(self.quarterly_quarters_entry.get() or "1")
            price = float(self.quarterly_price_entry.get() or "79.99")
            key_data = self.generator.generate_quarterly_key(quarters, price)

            self.display_generated_key(key_data)
            self.refresh_data()
            messagebox.showinfo("Success", f"Quarterly key generated: {key_data['key']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate quarterly key: {e}")

    def generate_lifetime_key(self):
        """Generate lifetime key"""
        try:
            price = float(self.lifetime_price_entry.get() or "299.99")
            key_data = self.generator.generate_lifetime_key(price)

            self.display_generated_key(key_data)
            self.refresh_data()
            messagebox.showinfo("Success", f"Lifetime key generated: {key_data['key']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate lifetime key: {e}")

    def generate_multi_device_key(self):
        """Generate multi-device key"""
        try:
            devices = int(self.multi_devices_entry.get() or "6")
            days = int(self.multi_days_entry.get() or "365")
            price = float(self.multi_price_entry.get() or "499.99")
            key_data = self.generator.generate_multi_device_key(devices, days, price)

            self.display_generated_key(key_data)
            self.refresh_data()
            messagebox.showinfo("Success", f"Multi-device key generated: {key_data['key']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate multi-device key: {e}")

    def display_generated_key(self, key_data):
        """Display generated key information"""
        # 🐛 DEBUG: Print key data being displayed
        print(f"🐛 DEBUG Display Key:")
        print(f"   Key: {key_data['key']}")
        print(f"   Type: {key_data['type']}")
        print(f"   Duration: {key_data['duration_days']} days")
        print(f"   Price: ${key_data['price']:.2f}")

        self.generated_key_display.delete("0.0", "end")

        key_info = f"""
🔑 GENERATED LICENSE KEY
Key: {key_data['key']}
Type: {key_data['type'].title()}
Price: ${key_data['price']:.2f}
Duration: {key_data['duration_days']} days
Max Devices: {key_data['max_devices']}
Expires: {key_data['expiry_date'][:10]}

✨ Features:
"""

        for feature in key_data['features']:
            key_info += f"• {feature.replace('_', ' ').title()}\n"

        key_info += f"\n🕒 Created: {key_data['created_at'][:19]}"

        self.generated_key_display.insert("0.0", key_info)

        # 🐛 DEBUG: Print what's actually being displayed
        print(f"🐛 DEBUG Display Text Preview:")
        print(f"   Duration line: Duration: {key_data['duration_days']} days")

    def copy_key_only(self):
        """Copy only the license key to clipboard"""
        try:
            # Get the key text from display
            key_text = self.generated_key_display.get("0.0", "end")
            if not key_text.strip():
                self.copy_status_label.configure(text="❌ No key to copy!", text_color="red")
                messagebox.showwarning("Warning", "No key generated yet!")
                return

            # 🐛 DEBUG: Print the actual text to see the format
            print(f"🐛 DEBUG Copy Key - Text content:")
            print(repr(key_text[:200]))  # Show first 200 chars with escapes

            # Extract key using regex - Updated to match 5-part key format
            key_match = re.search(r'Key: (CNPRO-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9][A-Z0-9]{3})', key_text)
            if not key_match:
                # Try alternative patterns
                key_match = re.search(r'Key: (CNPRO-[A-Z0-9-]+)', key_text)
                if key_match:
                    print(f"🐛 DEBUG: Found key with alternative pattern: {key_match.group(1)}")
                else:
                    print(f"🐛 DEBUG: No key found in text")
                    self.copy_status_label.configure(text="❌ Key not found!", text_color="red")
                    messagebox.showerror("Error", "Cannot find valid license key!")
                    return

            license_key = key_match.group(1)

            # Copy to clipboard with fallback methods
            try:
                if PYPERCLIP_AVAILABLE:
                    pyperclip.copy(license_key)
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(license_key)
                    self.root.update()  # Required for clipboard to work

                self.copy_status_label.configure(text="✅ Key copied!", text_color="green")
                self.clear_copy_status_after_delay()
                messagebox.showinfo("Success", f"License key copied to clipboard:\n{license_key}")
            except Exception as clipboard_error:
                # If clipboard fails, show the key for manual copy
                self.copy_status_label.configure(text="⚠️ Show key for manual copy", text_color="orange")
                messagebox.showinfo("Manual Copy", f"Please copy this key manually:\n\n{license_key}")

        except Exception as e:
            self.copy_status_label.configure(text="❌ Copy failed!", text_color="red")
            self.clear_copy_status_after_delay()
            messagebox.showerror("Error", f"Failed to copy key: {e}")

    def copy_key_full_info(self):
        """Copy full key information to clipboard"""
        try:
            # Get all text from display
            key_text = self.generated_key_display.get("0.0", "end")
            if not key_text.strip():
                self.copy_status_label.configure(text="❌ No info to copy!", text_color="red")
                messagebox.showwarning("Warning", "No key generated yet!")
                return

            # Copy to clipboard with fallback methods
            try:
                if PYPERCLIP_AVAILABLE:
                    pyperclip.copy(key_text.strip())
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(key_text.strip())
                    self.root.update()  # Required for clipboard to work

                self.copy_status_label.configure(text="✅ Full info copied!", text_color="green")
                self.clear_copy_status_after_delay()
                messagebox.showinfo("Success", "Full license information copied to clipboard!")
            except Exception as clipboard_error:
                # If clipboard fails, show info in a text window
                self.copy_status_label.configure(text="⚠️ Manual copy needed", text_color="orange")
                self.show_manual_copy_window("Full License Information", key_text.strip())

        except Exception as e:
            self.copy_status_label.configure(text="❌ Copy failed!", text_color="red")
            self.clear_copy_status_after_delay()
            messagebox.showerror("Error", f"Failed to copy information: {e}")

    def save_key_to_file(self):
        """Save key information to text file"""
        try:
            # Get all text from display
            key_text = self.generated_key_display.get("0.0", "end")
            if not key_text.strip():
                self.copy_status_label.configure(text="❌ No key to save!", text_color="red")
                messagebox.showwarning("Warning", "No key generated yet!")
                return

            # Extract key for filename - Updated to match 5-part key format
            key_match = re.search(r'Key: (CNPRO-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9][A-Z0-9]{3})', key_text)
            if key_match:
                license_key = key_match.group(1)
                default_filename = f"ClausoNet_License_{license_key}.txt"
            else:
                default_filename = f"ClausoNet_License_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title="Save License Key Information",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialname=default_filename
            )

            if file_path:
                # Add header to saved file
                save_content = f"""
CLAUSONET 4.0 PRO - LICENSE KEY INFORMATION
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

{key_text.strip()}

{'='*50}
ClausoNet 4.0 Pro - AI Video Generation Tool
Support: support@clausonet.com
Website: https://clausonet.com
"""

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(save_content)

                self.copy_status_label.configure(text="✅ Saved to file!", text_color="green")
                self.clear_copy_status_after_delay()
                messagebox.showinfo("Success", f"License information saved to:\n{file_path}")

        except Exception as e:
            self.copy_status_label.configure(text="❌ Save failed!", text_color="red")
            self.clear_copy_status_after_delay()
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def show_manual_copy_window(self, title, content):
        """Show a window with selectable text for manual copying"""
        copy_window = ctk.CTkToplevel(self.root)
        copy_window.title(title)
        copy_window.geometry("600x400")
        copy_window.transient(self.root)
        copy_window.grab_set()

        # Center the window
        copy_window.update_idletasks()
        x = (copy_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (copy_window.winfo_screenheight() // 2) - (400 // 2)
        copy_window.geometry(f"600x400+{x}+{y}")

        label = ctk.CTkLabel(copy_window, text="Select and copy the text below:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=10)

        text_widget = ctk.CTkTextbox(copy_window)
        text_widget.pack(fill="both", expand=True, padx=20, pady=10)
        text_widget.insert("0.0", content)

        # Select all text
        text_widget.tag_add("sel", "0.0", "end")
        text_widget.focus_set()

        close_btn = ctk.CTkButton(copy_window, text="Close", command=copy_window.destroy)
        close_btn.pack(pady=10)

    def clear_copy_status_after_delay(self, delay_seconds=3):
        """Clear copy status message after delay"""
        def clear_status():
            time.sleep(delay_seconds)
            try:
                self.copy_status_label.configure(text="")
            except:
                pass  # Ignore if widget is destroyed

        thread = threading.Thread(target=clear_status)
        thread.daemon = True
        thread.start()

    def create_context_menu(self):
        """Create right-click context menu for key display"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📋 Copy Key Only", command=self.copy_key_only)
        self.context_menu.add_command(label="📋 Copy Full Info", command=self.copy_key_full_info)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💾 Save to File", command=self.save_key_to_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 Refresh Data", command=self.refresh_data)

        # Bind right-click to show context menu
        self.generated_key_display.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu at mouse position"""
        try:
            # Check if there's content to copy
            key_text = self.generated_key_display.get("0.0", "end")
            if key_text.strip():
                # Enable copy options
                self.context_menu.entryconfig("📋 Copy Key Only", state="normal")
                self.context_menu.entryconfig("📋 Copy Full Info", state="normal")
                self.context_menu.entryconfig("💾 Save to File", state="normal")
            else:
                # Disable copy options if no content
                self.context_menu.entryconfig("📋 Copy Key Only", state="disabled")
                self.context_menu.entryconfig("📋 Copy Full Info", state="disabled")
                self.context_menu.entryconfig("💾 Save to File", state="disabled")

            # Show menu at mouse position
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Context menu error: {e}")

    def send_key_to_customer(self):
        """Send generated key to customer via email"""
        try:
            # Get the latest generated key from the display
            key_text = self.generated_key_display.get("0.0", "end")
            if not key_text.strip():
                self.email_status_label.configure(text="❌ No key generated yet!", text_color="red")
                messagebox.showerror("Error", "Please generate a key first!")
                return

            # Extract key from display text - Updated to match 5-part key format
            import re
            key_match = re.search(r'Key: (CNPRO-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9][A-Z0-9]{3})', key_text)
            if not key_match:
                self.email_status_label.configure(text="❌ Cannot find valid key!", text_color="red")
                messagebox.showerror("Error", "Cannot find valid license key in display!")
                return

            license_key = key_match.group(1)

            # Get customer info
            customer_email = self.send_email_entry.get().strip()
            customer_name = self.send_name_entry.get().strip() or "Valued Customer"

            if not customer_email:
                self.email_status_label.configure(text="❌ Customer email required!", text_color="red")
                messagebox.showerror("Error", "Please enter customer email!")
                return

            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, customer_email):
                self.email_status_label.configure(text="❌ Invalid email format!", text_color="red")
                messagebox.showerror("Error", "Please enter a valid email address!")
                return

            # Show sending status
            self.email_status_label.configure(text="📤 Sending email...", text_color="blue")
            self.update()

            # Create customer record if not exists
            try:
                customer = self.generator.create_customer_record(customer_email, customer_name)
                print(f"✅ Customer record created/updated: {customer_email}")
            except Exception as e:
                print(f"⚠️ Customer creation warning: {e}")

            # Assign key to customer
            try:
                assignment_success = self.generator.assign_key_to_customer(license_key, customer_email)
                if assignment_success:
                    print(f"✅ Key {license_key} assigned to {customer_email}")
                else:
                    print(f"⚠️ Key assignment warning for {license_key}")
            except Exception as e:
                print(f"⚠️ Key assignment warning: {e}")

            # Check if email is configured
            if not self.generator.admin_email or not self.generator.admin_password:
                self.email_status_label.configure(text="⚠️ Email not configured! Use Settings tab.", text_color="orange")
                result = messagebox.askyesno(
                    "Email Not Configured",
                    f"SMTP email is not configured.\n\nKey: {license_key}\nCustomer: {customer_email}\n\nWould you like to:\n- Configure email in Settings tab\n- Or copy key manually to send?\n\nClick Yes to go to Settings, No to copy key."
                )
                if result:
                    # Switch to settings tab
                    self.notebook.set("⚙️ Settings")
                else:
                    # Copy key to clipboard
                    try:
                        try:
                            import pyperclip
                            pyperclip.copy(license_key)
                            self.email_status_label.configure(text="📋 Key copied to clipboard!", text_color="green")
                            messagebox.showinfo("Key Copied", f"License key copied to clipboard:\n{license_key}\n\nYou can now paste and send it manually to: {customer_email}")
                        except ImportError:
                            # Fallback if pyperclip not available
                            self.email_status_label.configure(text="📝 Key ready for manual sending", text_color="blue")
                            messagebox.showinfo("Manual Send", f"Please send this key manually:\n\nKey: {license_key}\nTo: {customer_email}")
                    except Exception:
                        self.email_status_label.configure(text="📝 Key ready for manual sending", text_color="blue")
                        messagebox.showinfo("Manual Send", f"Please send this key manually:\n\nKey: {license_key}\nTo: {customer_email}")
                return

            # Try to send email
            try:
                send_result = self.generator.send_key_email(license_key, customer_email, customer_name)

                if send_result:
                    self.email_status_label.configure(text="✅ Email sent successfully!", text_color="green")
                    messagebox.showinfo("Success", f"License key sent successfully!\n\nKey: {license_key}\nTo: {customer_email}")

                    # Clear customer fields after successful send
                    self.send_email_entry.delete(0, "end")
                    self.send_name_entry.delete(0, "end")

                    # Refresh data
                    self.refresh_data()
                else:
                    self.email_status_label.configure(text="❌ Email sending failed!", text_color="red")
                    messagebox.showerror("Email Failed", f"Failed to send email to {customer_email}\n\nKey: {license_key}\n\nPlease check email configuration in Settings tab.")

            except Exception as e:
                self.email_status_label.configure(text="❌ Email error occurred!", text_color="red")
                messagebox.showerror("Email Error", f"Email sending error: {str(e)}\n\nKey: {license_key}\nCustomer: {customer_email}")

        except Exception as e:
            self.email_status_label.configure(text="❌ Unexpected error!", text_color="red")
            messagebox.showerror("Error", f"Unexpected error in send_key_to_customer: {str(e)}")

    def add_customer(self):
        """Add new customer"""
        try:
            email = self.customer_email_entry.get().strip()
            name = self.customer_name_entry.get().strip()
            phone = self.customer_phone_entry.get().strip()
            company = self.customer_company_entry.get().strip()

            if not email:
                messagebox.showerror("Error", "Email is required")
                return

            customer = self.generator.create_customer_record(email, name, phone, company)

            # Clear entries
            self.customer_email_entry.delete(0, "end")
            self.customer_name_entry.delete(0, "end")
            self.customer_phone_entry.delete(0, "end")
            self.customer_company_entry.delete(0, "end")

            self.refresh_customer_list()
            messagebox.showinfo("Success", f"Customer added: {customer['email']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add customer: {e}")

    def assign_key(self):
        """Assign key to customer"""
        try:
            key = self.assign_key_entry.get().strip()
            email = self.assign_email_entry.get().strip()

            if not key or not email:
                messagebox.showerror("Error", "Both key and email are required")
                return

            if self.generator.assign_key_to_customer(key, email):
                self.refresh_data()
                messagebox.showinfo("Success", f"Key {key} assigned to {email}")
            else:
                messagebox.showerror("Error", "Failed to assign key")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to assign key: {e}")

    def send_key_email(self):
        """Send key via email"""
        try:
            key = self.assign_key_entry.get().strip()
            email = self.assign_email_entry.get().strip()

            if not key or not email:
                messagebox.showerror("Error", "Both key and email are required")
                return

            key_info = self.generator.get_key_info(key)
            if not key_info:
                messagebox.showerror("Error", "Key not found")
                return

            # Run email sending in background
            def send_email():
                if self.generator.send_key_email(email, key, key_info['type']):
                    messagebox.showinfo("Success", f"Email sent to {email}")
                else:
                    messagebox.showerror("Error", "Failed to send email")

            threading.Thread(target=send_email, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {e}")

    def search_key(self):
        """Search for specific key"""
        try:
            key = self.search_key_entry.get().strip()
            if not key:
                messagebox.showerror("Error", "Enter a key to search")
                return

            key_info = self.generator.get_key_info(key)
            if key_info:
                # Show key details in a popup
                info_window = ctk.CTkToplevel(self.root)
                info_window.title(f"Key Info: {key}")
                info_window.geometry("600x400")

                info_text = ctk.CTkTextbox(info_window)
                info_text.pack(fill="both", expand=True, padx=20, pady=20)

                info_text.insert("0.0", json.dumps(key_info, indent=2, ensure_ascii=False))
            else:
                messagebox.showinfo("Not Found", "Key not found")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def refresh_data(self):
        """Refresh all data"""
        self.refresh_customer_list()
        self.refresh_key_list()
        self.refresh_statistics()

    def refresh_customer_list(self):
        """Refresh customer list"""
        try:
            # Clear existing items
            for item in self.customer_tree.get_children():
                self.customer_tree.delete(item)

            # Ensure database has customers key
            if 'customers' not in self.generator.database:
                self.generator.database['customers'] = []
                self.generator.save_database()

            # Add customers
            for customer in self.generator.database['customers']:
                self.customer_tree.insert("", "end", values=(
                    customer.get('email', ''),
                    customer.get('name', ''),
                    customer.get('phone', ''),
                    customer.get('company', ''),
                    len(customer.get('keys_purchased', [])),
                    f"${customer.get('total_spent', 0.0):.2f}",
                    customer.get('last_contact', '')[:10] if customer.get('last_contact') else "Never"
                ))
        except Exception as e:
            print(f"Error refreshing customer list: {e}")
            # Create empty database structure if needed
            try:
                self.generator.create_initial_database()
                self.generator.load_license_database()
            except:
                pass

    def refresh_key_list(self):
        """Refresh key list"""
        try:
            # Clear existing items
            for item in self.keys_tree.get_children():
                self.keys_tree.delete(item)

            # Ensure database has keys key
            if 'keys' not in self.generator.database:
                self.generator.database['keys'] = []
                self.generator.save_database()

            # Add keys
            for key in self.generator.database['keys']:
                customer_email = ""
                if key.get('customer_info'):
                    customer_email = key['customer_info'].get('email', '')

                self.keys_tree.insert("", "end", values=(
                    key.get('key', ''),
                    key.get('type', ''),
                    key.get('status', ''),
                    customer_email,
                    key.get('created_at', '')[:10],
                    key.get('expiry_date', '')[:10],
                    f"${key.get('price', 0.0):.2f}",
                    key.get('max_devices', 0)
                ))
        except Exception as e:
            print(f"Error refreshing key list: {e}")
            # Create empty database structure if needed
            try:
                self.generator.create_initial_database()
                self.generator.load_license_database()
            except:
                pass

    def refresh_statistics(self):
        """Refresh statistics"""
        try:
            # Ensure database has statistics key
            if 'statistics' not in self.generator.database:
                self.generator.database['statistics'] = {
                    'total_keys_generated': 0,
                    'trial_keys': 0,
                    'monthly_keys': 0,
                    'quarterly_keys': 0,
                    'lifetime_keys': 0,
                    'multi_device_keys': 0,
                    'keys_activated': 0,
                    'revenue_tracked': 0.0
                }
                self.generator.save_database()

            stats = self.generator.get_statistics()

            stats_text = f"""
📊 CLAUSONET 4.0 PRO - LICENSE STATISTICS
Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 OVERVIEW:
• Total Keys Generated: {stats.get('total_keys_generated', 0)}
• Active Keys: {stats.get('active_keys', 0)}
• Expired Keys: {stats.get('expired_keys', 0)}
• Total Customers: {stats.get('total_customers', 0)}

🔑 KEY BREAKDOWN:
• Trial Keys: {stats.get('trial_keys', 0)}
• Monthly Keys: {stats.get('monthly_keys', 0)}
• Quarterly Keys: {stats.get('quarterly_keys', 0)}
• Lifetime Keys: {stats.get('lifetime_keys', 0)}
• Multi-Device Keys: {stats.get('multi_device_keys', 0)}

💰 REVENUE:
• Total Revenue: ${stats.get('revenue_tracked', 0.0):.2f}
• Average per Customer: ${stats.get('revenue_tracked', 0.0) / max(stats.get('total_customers', 1), 1):.2f}
• Activation Rate: {(stats.get('keys_activated', 0) / max(stats.get('total_keys_generated', 1), 1) * 100):.1f}%
"""

            self.stats_display.delete("0.0", "end")
            self.stats_display.insert("0.0", stats_text)

        except Exception as e:
            print(f"Error refreshing statistics: {e}")
            # Create empty database structure if needed
            try:
                self.generator.create_initial_database()
                self.generator.load_license_database()
                # Retry once
                self.refresh_statistics()
            except:
                # Show empty stats
                empty_stats = """
📊 CLAUSONET 4.0 PRO - LICENSE STATISTICS
Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 OVERVIEW:
• Total Keys Generated: 0
• Active Keys: 0
• Expired Keys: 0
• Total Customers: 0

🔑 KEY BREAKDOWN:
• Trial Keys: 0
• Monthly Keys: 0
• Quarterly Keys: 0
• Lifetime Keys: 0
• Multi-Device Keys: 0

💰 REVENUE:
• Total Revenue: $0.00
• Average per Customer: $0.00
• Activation Rate: 0.0%
"""
                self.stats_display.delete("0.0", "end")
                self.stats_display.insert("0.0", empty_stats)

    def generate_report(self):
        """Generate detailed report"""
        try:
            report = self.generator.generate_admin_report()

            self.report_display.delete("0.0", "end")
            self.report_display.insert("0.0", report)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def export_to_excel(self):
        """Export data to Excel"""
        if not PANDAS_AVAILABLE:
            messagebox.showerror("Error", "pandas not installed. Install with: pip install pandas openpyxl")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Excel Report"
            )

            if file_path:
                # Create Excel data
                customers_df = pd.DataFrame(self.generator.database.get('customers', []))
                keys_df = pd.DataFrame(self.generator.database.get('keys', []))
                stats_df = pd.DataFrame([self.generator.get_statistics()])

                with pd.ExcelWriter(file_path) as writer:
                    customers_df.to_excel(writer, sheet_name='Customers', index=False)
                    keys_df.to_excel(writer, sheet_name='License Keys', index=False)
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)

                messagebox.showinfo("Success", f"Data exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def save_email_settings(self):
        """Save email settings"""
        try:
            self.generator.smtp_server = self.smtp_server_entry.get() or "smtp.gmail.com"
            self.generator.smtp_port = int(self.smtp_port_entry.get() or "587")
            self.generator.admin_email = self.admin_email_entry.get() or "admin@clausonet.com"
            self.generator.admin_password = self.admin_password_entry.get() or ""

            messagebox.showinfo("Success", "Email settings saved")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save email settings: {e}")

    def backup_database(self):
        """Backup database"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Backup Database"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.generator.database, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"Database backed up to {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {e}")

    def restore_database(self):
        """Restore database"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json")],
                title="Restore Database"
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.generator.database = json.load(f)

                self.generator.save_database()
                self.refresh_data()
                messagebox.showinfo("Success", f"Database restored from {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {e}")

    def clear_database(self):
        """Clear all database"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data? This cannot be undone!"):
            try:
                self.generator.create_initial_database()
                self.generator.load_license_database()
                self.refresh_data()
                messagebox.showinfo("Success", "Database cleared")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database: {e}")

    def create_email_requests_tab(self):
        """Tab for email request processing"""
        # Create tab frame
        email_req_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(email_req_frame, text="📧 Email Requests")

        # Content frame with scrollable
        content_frame = ctk.CTkScrollableFrame(email_req_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Email Request Processing Section
        request_section = ctk.CTkFrame(content_frame)
        request_section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(request_section, text="📧 Email Request Processing", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        if not EMAIL_HANDLER_AVAILABLE:
            # Warning if email handler not available
            warning_frame = ctk.CTkFrame(request_section)
            warning_frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(
                warning_frame,
                text="⚠️ Email Request Handler not available. Please check email_request_handler.py",
                text_color="orange"
            ).pack(pady=10)
            return

        # Email Configuration Section
        config_section = ctk.CTkFrame(request_section)
        config_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(config_section, text="📧 Email Configuration", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        config_input_frame = ctk.CTkFrame(config_section)
        config_input_frame.pack(fill="x", padx=10, pady=10)

        # Email credentials inputs
        ctk.CTkLabel(config_input_frame, text="Email Address:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.email_address_entry = ctk.CTkEntry(config_input_frame, placeholder_text="your.email@gmail.com", width=250)
        self.email_address_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(config_input_frame, text="App Password:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.email_password_entry = ctk.CTkEntry(config_input_frame, placeholder_text="16-character app password", show="*", width=250)
        self.email_password_entry.grid(row=1, column=1, padx=10, pady=5)

        # Test email connection button
        ctk.CTkButton(
            config_input_frame,
            text="Test Email Connection",
            command=self.test_email_connection,
            fg_color="#4ECDC4"
        ).grid(row=0, column=2, padx=20, pady=5, rowspan=2)

        # Auto Processing Section
        auto_section = ctk.CTkFrame(request_section)
        auto_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(auto_section, text="🔄 Auto Processing", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        auto_controls_frame = ctk.CTkFrame(auto_section)
        auto_controls_frame.pack(fill="x", padx=10, pady=10)

        # Processing status
        self.processing_status_label = ctk.CTkLabel(auto_controls_frame, text="Status: Not Started", font=ctk.CTkFont(size=12))
        self.processing_status_label.pack(pady=5)

        # Control buttons
        button_frame = ctk.CTkFrame(auto_controls_frame)
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Start Auto Processing",
            command=self.start_email_processing,
            fg_color="#27AE60"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Check Now",
            command=self.check_emails_now,
            fg_color="#3498DB"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Stop Processing",
            command=self.stop_email_processing,
            fg_color="#E74C3C"
        ).pack(side="left", padx=10)

        # Statistics Section
        stats_section = ctk.CTkFrame(request_section)
        stats_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(stats_section, text="📊 Processing Statistics", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        stats_frame = ctk.CTkFrame(stats_section)
        stats_frame.pack(fill="x", padx=10, pady=10)

        # Statistics labels
        self.emails_processed_label = ctk.CTkLabel(stats_frame, text="Emails Processed: 0")
        self.emails_processed_label.pack(anchor="w", padx=10, pady=2)

        self.keys_generated_label = ctk.CTkLabel(stats_frame, text="Keys Generated: 0")
        self.keys_generated_label.pack(anchor="w", padx=10, pady=2)

        self.success_rate_label = ctk.CTkLabel(stats_frame, text="Success Rate: 0%")
        self.success_rate_label.pack(anchor="w", padx=10, pady=2)

        # Processed Requests Log Section
        log_section = ctk.CTkFrame(request_section)
        log_section.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(log_section, text="📋 Recent Processed Requests", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # Log text widget
        self.request_log = ctk.CTkTextbox(log_section, height=200)
        self.request_log.pack(fill="both", expand=True, padx=10, pady=10)

        # Help Section
        help_section = ctk.CTkFrame(content_frame)
        help_section.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(help_section, text="💡 How Email Request Processing Works", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        help_text = """
🔍 EMAIL DETECTION:
• System monitors your email inbox for license requests
• Automatically detects keywords: 'trial', 'lifetime', 'monthly', etc.
• Extracts customer information (name, phone, company)

🔑 AUTO KEY GENERATION:
• 'trial', 'test', 'thử' → Trial Key (30 days)
• 'lifetime', 'vĩnh viễn' → Lifetime Key ($299.99)
• 'monthly', 'tháng' → Monthly Key ($29.99)
• 'quarterly', 'quý' → Quarterly Key ($79.99)

📧 AUTO RESPONSE:
• Creates customer record automatically
• Generates appropriate license key
• Sends professional license email
• Updates database and statistics

📋 SETUP REQUIREMENTS:
1. Enable IMAP access in your email account
2. Create Gmail/Outlook app password
3. Enter credentials above
4. Start auto processing
        """

        help_label = ctk.CTkLabel(help_section, text=help_text, justify="left", font=ctk.CTkFont(size=11))
        help_label.pack(padx=20, pady=10)

        # Initialize email processing status
        self.email_processing_active = False
        self.email_processing_thread = None

    def test_email_connection(self):
        """Test email connection"""
        if not EMAIL_HANDLER_AVAILABLE:
            messagebox.showerror("Error", "Email handler not available")
            return

        email_address = self.email_address_entry.get().strip()
        password = self.email_password_entry.get().strip()

        if not email_address or not password:
            messagebox.showerror("Error", "Please enter email address and password")
            return

        def test_connection():
            try:
                self.processing_status_label.configure(text="Status: Testing connection...")

                mail = self.email_handler.connect_to_email(email_address, password)
                if mail:
                    mail.close()
                    mail.logout()

                    self.processing_status_label.configure(text="Status: Connection successful!")
                    messagebox.showinfo("Success", "Email connection test successful!")
                else:
                    self.processing_status_label.configure(text="Status: Connection failed")
                    messagebox.showerror("Error", "Email connection failed. Check credentials.")

            except Exception as e:
                self.processing_status_label.configure(text="Status: Connection error")
                messagebox.showerror("Error", f"Connection test failed: {e}")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=test_connection)
        thread.daemon = True
        thread.start()

    def start_email_processing(self):
        """Start automatic email processing"""
        if not EMAIL_HANDLER_AVAILABLE:
            messagebox.showerror("Error", "Email handler not available")
            return

        if self.email_processing_active:
            messagebox.showinfo("Info", "Email processing is already running")
            return

        email_address = self.email_address_entry.get().strip()
        password = self.email_password_entry.get().strip()

        if not email_address or not password:
            messagebox.showerror("Error", "Please enter email credentials first")
            return

        self.email_processing_active = True
        self.processing_status_label.configure(text="Status: Starting auto processing...")

        def process_emails_continuously():
            """Continuously process emails"""
            while self.email_processing_active:
                try:
                    self.processing_status_label.configure(text="Status: Checking for new emails...")

                    # Process emails
                    success = self.email_handler.auto_process_emails(email_address, password)

                    if success:
                        self.processing_status_label.configure(text="Status: Auto processing active")
                        self.update_processing_stats()
                    else:
                        self.processing_status_label.configure(text="Status: Processing error")

                    # Wait 5 minutes before next check
                    import time
                    for _ in range(300):  # 5 minutes = 300 seconds
                        if not self.email_processing_active:
                            break
                        time.sleep(1)

                except Exception as e:
                    self.processing_status_label.configure(text=f"Status: Error - {e}")
                    break

            self.processing_status_label.configure(text="Status: Stopped")

        # Start processing thread
        self.email_processing_thread = threading.Thread(target=process_emails_continuously)
        self.email_processing_thread.daemon = True
        self.email_processing_thread.start()

        messagebox.showinfo("Started", "Auto email processing started. Checking every 5 minutes.")

    def check_emails_now(self):
        """Check emails immediately"""
        if not EMAIL_HANDLER_AVAILABLE:
            messagebox.showerror("Error", "Email handler not available")
            return

        email_address = self.email_address_entry.get().strip()
        password = self.email_password_entry.get().strip()

        if not email_address or not password:
            messagebox.showerror("Error", "Please enter email credentials first")
            return

        def check_now():
            try:
                self.processing_status_label.configure(text="Status: Checking emails now...")

                success = self.email_handler.auto_process_emails(email_address, password)

                if success:
                    self.processing_status_label.configure(text="Status: Check completed")
                    self.update_processing_stats()
                    messagebox.showinfo("Complete", "Email check completed")
                else:
                    self.processing_status_label.configure(text="Status: Check failed")
                    messagebox.showerror("Error", "Email check failed")

            except Exception as e:
                self.processing_status_label.configure(text="Status: Check error")
                messagebox.showerror("Error", f"Check failed: {e}")

        # Run in thread
        thread = threading.Thread(target=check_now)
        thread.daemon = True
        thread.start()

    def stop_email_processing(self):
        """Stop automatic email processing"""
        self.email_processing_active = False
        self.processing_status_label.configure(text="Status: Stopping...")
        messagebox.showinfo("Stopped", "Email processing stopped")

    def update_processing_stats(self):
        """Update processing statistics"""
        try:
            # Load processed requests log
            if os.path.exists('processed_requests.json'):
                with open('processed_requests.json', 'r') as f:
                    logs = json.load(f)

                total_processed = len(logs)
                total_keys = len([log for log in logs if 'license_key' in log])
                success_rate = (total_keys / total_processed * 100) if total_processed > 0 else 0

                self.emails_processed_label.configure(text=f"Emails Processed: {total_processed}")
                self.keys_generated_label.configure(text=f"Keys Generated: {total_keys}")
                self.success_rate_label.configure(text=f"Success Rate: {success_rate:.1f}%")

                # Update log display
                log_text = ""
                for log in logs[-10:]:  # Show last 10 requests
                    timestamp = log.get('timestamp', '')[:19]
                    customer = log.get('customer_email', 'Unknown')
                    key_type = log.get('license_type', 'Unknown')
                    log_text += f"{timestamp} - {customer} - {key_type}\n"

                self.request_log.delete("1.0", "end")
                self.request_log.insert("1.0", log_text)

        except Exception as e:
            print(f"Error updating stats: {e}")

    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main function"""
    app = AdminLicenseGUI()
    app.run()


if __name__ == "__main__":
    main()
