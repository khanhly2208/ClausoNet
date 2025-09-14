#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - License Admin GUI
GUI tool để quản lý license và tạo key theo máy
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, scrolledtext
import json
import hashlib
import secrets
import string
import platform
import subprocess
import psutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import os
import sys

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LicenseAdminGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("ClausoNet 4.0 Pro - License Admin Tool")
        self.root.geometry("1400x900")
        
        # License database
        self.license_db_path = Path("admin_data/license_database.json")
        self.license_db_path.parent.mkdir(exist_ok=True)
        self.license_database = self.load_license_database()
        
        # Hardware info cache
        self.current_hardware_info = None
        
        self.create_widgets()
        self.refresh_license_list()
        
    def create_widgets(self):
        """Tạo giao diện chính"""
        
        # Main tabview
        self.tabview = ctk.CTkTabview(self.root, width=1380, height=860)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("🔑 Generate License")
        self.tabview.add("🖥️ Hardware Scanner") 
        self.tabview.add("📋 License Database")
        self.tabview.add("⚙️ Bulk Operations")
        
        self.create_generate_tab()
        self.create_hardware_tab()
        self.create_database_tab()
        self.create_bulk_tab()
        
    def create_generate_tab(self):
        """Tab tạo license"""
        tab = self.tabview.tab("🔑 Generate License")
        
        # Main frame
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Input form - Make it scrollable
        left_panel = ctk.CTkScrollableFrame(main_frame, width=580, height=800)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        ctk.CTkLabel(left_panel, text="🔑 License Key Generator", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 30))
        
        # Customer Info - Compact
        info_frame = ctk.CTkFrame(left_panel, fg_color="#2b2b2b")
        info_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(info_frame, text="👤 Customer Information", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 8))
        
        # Customer Name
        ctk.CTkLabel(info_frame, text="Customer Name:", anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        self.customer_name = ctk.CTkEntry(info_frame, placeholder_text="Enter customer name")
        self.customer_name.pack(fill="x", padx=15, pady=(0, 10))
        
        # Customer Email
        ctk.CTkLabel(info_frame, text="Customer Email:", anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        self.customer_email = ctk.CTkEntry(info_frame, placeholder_text="customer@company.com")
        self.customer_email.pack(fill="x", padx=15, pady=(0, 10))
        
        # Hardware ID
        ctk.CTkLabel(info_frame, text="Hardware ID (from customer):", anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        self.hardware_id = ctk.CTkEntry(info_frame, placeholder_text="Hardware fingerprint từ máy khách hàng")
        self.hardware_id.pack(fill="x", padx=15, pady=(0, 15))
        
        # License Settings - Compact
        settings_frame = ctk.CTkFrame(left_panel, fg_color="#2b2b2b")
        settings_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(settings_frame, text="⚙️ License Settings", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 8))
        
        # License Type
        ctk.CTkLabel(settings_frame, text="License Type:", anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        self.license_type = ctk.CTkComboBox(settings_frame, 
                                          values=["trial", "professional", "enterprise", "unlimited"],
                                          state="readonly")
        self.license_type.pack(fill="x", padx=15, pady=(0, 10))
        self.license_type.set("professional")
        
        # Duration
        ctk.CTkLabel(settings_frame, text="License Duration:", anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        duration_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        duration_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.duration_value = ctk.CTkEntry(duration_frame, width=100)
        self.duration_value.pack(side="left", padx=(0, 10))
        self.duration_value.insert(0, "365")
        
        self.duration_unit = ctk.CTkComboBox(duration_frame, values=["days", "months", "years"], width=100)
        self.duration_unit.pack(side="left")
        self.duration_unit.set("days")
        
        # Features
        ctk.CTkLabel(settings_frame, text="Features:", anchor="w").pack(fill="x", padx=15, pady=(10, 5))
        
        features_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        features_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.feature_ai = ctk.CTkCheckBox(features_frame, text="AI Video Generation")
        self.feature_ai.pack(anchor="w", pady=2)
        self.feature_ai.select()
        
        self.feature_unlimited = ctk.CTkCheckBox(features_frame, text="Unlimited Workflows")
        self.feature_unlimited.pack(anchor="w", pady=2)
        self.feature_unlimited.select()
        
        self.feature_api = ctk.CTkCheckBox(features_frame, text="API Access")
        self.feature_api.pack(anchor="w", pady=2)
        
        self.feature_priority = ctk.CTkCheckBox(features_frame, text="Priority Support")
        self.feature_priority.pack(anchor="w", pady=2)
        
        # Spacer to separate from features
        ctk.CTkLabel(left_panel, text="", height=20).pack(pady=5)
        
        # Generate Button Section - Highlighted
        generate_section = ctk.CTkFrame(left_panel, fg_color="#1a1a1a", border_width=2, border_color="#ff6b00")
        generate_section.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(generate_section, text="⚡ READY TO GENERATE", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color="#ff6b00").pack(pady=(15, 5))
        
        self.generate_btn = ctk.CTkButton(generate_section, text="🚀 GENERATE LICENSE KEY", 
                                        height=60, font=ctk.CTkFont(size=18, weight="bold"),
                                        fg_color="#ff6b00", hover_color="#e55a00",
                                        command=self.generate_license)
        self.generate_btn.pack(fill="x", padx=15, pady=(5, 20))
        
        # Right panel - Results
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(right_panel, text="📋 Generated License", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 30))
        
        # License Key Display
        key_frame = ctk.CTkFrame(right_panel, fg_color="#2b2b2b")
        key_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(key_frame, text="License Key:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        self.license_key_display = ctk.CTkEntry(key_frame, font=ctk.CTkFont(size=16, weight="bold"),
                                              height=40, justify="center")
        self.license_key_display.pack(fill="x", padx=15, pady=(0, 10))
        
        copy_btn = ctk.CTkButton(key_frame, text="📋 Copy Key", command=self.copy_license_key)
        copy_btn.pack(pady=(0, 15))
        
        # License Details
        details_frame = ctk.CTkFrame(right_panel, fg_color="#2b2b2b")
        details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(details_frame, text="License Details:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        self.license_details = ctk.CTkTextbox(details_frame, font=ctk.CTkFont(family="Consolas"))
        self.license_details.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def create_hardware_tab(self):
        """Tab quét hardware"""
        tab = self.tabview.tab("🖥️ Hardware Scanner")
        
        # Main frame
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="🖥️ Hardware Information Scanner", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 30))
        
        # Control frame
        control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 20))
        
        self.scan_btn = ctk.CTkButton(control_frame, text="🔍 Scan Current Hardware", 
                                    command=self.scan_hardware, width=200, height=40,
                                    font=ctk.CTkFont(size=14, weight="bold"))
        self.scan_btn.pack(side="left", padx=(0, 10))
        
        self.export_hw_btn = ctk.CTkButton(control_frame, text="💾 Export Hardware Info", 
                                         command=self.export_hardware_info, width=200, height=40)
        self.export_hw_btn.pack(side="left", padx=(0, 10))
        
        self.import_hw_btn = ctk.CTkButton(control_frame, text="📁 Import Hardware Info", 
                                         command=self.import_hardware_info, width=200, height=40)
        self.import_hw_btn.pack(side="left")
        
        # Hardware Info Display
        hw_frame = ctk.CTkFrame(main_frame)
        hw_frame.pack(fill="both", expand=True)
        
        self.hardware_info_display = ctk.CTkTextbox(hw_frame, font=ctk.CTkFont(family="Consolas"))
        self.hardware_info_display.pack(fill="both", expand=True, padx=20, pady=20)
        
    def create_database_tab(self):
        """Tab database license"""
        tab = self.tabview.tab("📋 License Database")
        
        # Main frame
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="📋 License Database Management", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 20))
        
        # Control frame
        control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 20))
        
        self.refresh_db_btn = ctk.CTkButton(control_frame, text="🔄 Refresh", 
                                          command=self.refresh_license_list, width=120, height=35)
        self.refresh_db_btn.pack(side="left", padx=(0, 10))
        
        self.export_db_btn = ctk.CTkButton(control_frame, text="💾 Export Database", 
                                         command=self.export_database, width=150, height=35)
        self.export_db_btn.pack(side="left", padx=(0, 10))
        
        self.import_db_btn = ctk.CTkButton(control_frame, text="📁 Import Database", 
                                         command=self.import_database, width=150, height=35)
        self.import_db_btn.pack(side="left", padx=(0, 10))
        
        search_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search licenses...", width=200)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        search_btn = ctk.CTkButton(search_frame, text="🔍", width=40, command=self.search_licenses)
        search_btn.pack(side="left")
        
        # License List
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # Headers
        header_frame = ctk.CTkFrame(list_frame, height=40, fg_color="#404040")
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        headers = ["License Key", "Customer", "Type", "Status", "Expiry", "Hardware ID"]
        header_widths = [200, 150, 100, 80, 120, 200]
        
        for i, (header, width) in enumerate(zip(headers, header_widths)):
            label = ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(weight="bold"))
            label.place(x=sum(header_widths[:i]) + 10, y=10)
        
        # Scrollable license list
        self.license_scrollable = ctk.CTkScrollableFrame(list_frame, height=400)
        self.license_scrollable.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        # License buttons list
        self.license_buttons = []
        
    def create_bulk_tab(self):
        """Tab bulk operations"""
        tab = self.tabview.tab("⚙️ Bulk Operations")
        
        # Main frame
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="⚙️ Bulk License Operations", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 30))
        
        # Bulk Generate Frame
        bulk_frame = ctk.CTkFrame(main_frame)
        bulk_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(bulk_frame, text="🚀 Bulk License Generation", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15))
        
        settings_row = ctk.CTkFrame(bulk_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=20, pady=(0, 15))
        
        # Quantity
        ctk.CTkLabel(settings_row, text="Quantity:").pack(side="left", padx=(0, 10))
        self.bulk_quantity = ctk.CTkEntry(settings_row, width=100)
        self.bulk_quantity.pack(side="left", padx=(0, 20))
        self.bulk_quantity.insert(0, "10")
        
        # Type
        ctk.CTkLabel(settings_row, text="Type:").pack(side="left", padx=(0, 10))
        self.bulk_type = ctk.CTkComboBox(settings_row, values=["trial", "professional", "enterprise"], width=120)
        self.bulk_type.pack(side="left", padx=(0, 20))
        self.bulk_type.set("professional")
        
        # Duration
        ctk.CTkLabel(settings_row, text="Duration (days):").pack(side="left", padx=(0, 10))
        self.bulk_duration = ctk.CTkEntry(settings_row, width=100)
        self.bulk_duration.pack(side="left")
        self.bulk_duration.insert(0, "365")
        
        self.bulk_generate_btn = ctk.CTkButton(bulk_frame, text="🚀 Generate Bulk Licenses", 
                                             command=self.bulk_generate, height=40,
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.bulk_generate_btn.pack(pady=(0, 20))
        
        # Bulk Results
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=20)
        
        ctk.CTkLabel(results_frame, text="📋 Bulk Results", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        self.bulk_results = ctk.CTkTextbox(results_frame, font=ctk.CTkFont(family="Consolas"))
        self.bulk_results.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
    def generate_license_key(self) -> str:
        """Tạo license key format CNPRO-XXXX-XXXX-XXXX-XXXX"""
        def random_segment():
            return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        return f"CNPRO-{random_segment()}-{random_segment()}-{random_segment()}-{random_segment()}"
    
    def get_hardware_components(self) -> dict:
        """Thu thập thông tin hardware"""
        components = {}
        
        try:
            # CPU Info
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            components['cpu_id'] = cpu_info.get('brand_raw', 'UNKNOWN_CPU')
        except:
            components['cpu_id'] = platform.processor()
        
        try:
            # Motherboard Serial
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber', '/format:value'],
                                      capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if 'SerialNumber=' in line:
                        components['motherboard'] = line.split('=')[1].strip() or "UNKNOWN_MB"
                        break
                else:
                    components['motherboard'] = "UNKNOWN_MB"
            else:
                components['motherboard'] = "UNKNOWN_MB"
        except:
            components['motherboard'] = "UNKNOWN_MB"
        
        try:
            # MAC Address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
            components['mac_address'] = mac
        except:
            components['mac_address'] = "UNKNOWN_MAC"
        
        try:
            # Windows Product ID
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'os', 'get', 'SerialNumber', '/format:value'],
                                      capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if 'SerialNumber=' in line:
                        components['windows_id'] = line.split('=')[1].strip() or "UNKNOWN_WIN"
                        break
                else:
                    components['windows_id'] = "UNKNOWN_WIN"
            else:
                components['windows_id'] = "UNKNOWN_WIN"
        except:
            components['windows_id'] = "UNKNOWN_WIN"
        
        try:
            # BIOS Info
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'bios', 'get', 'SerialNumber,Version', '/format:value'],
                                      capture_output=True, text=True, shell=True)
                bios_info = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        bios_info[key.strip()] = value.strip()
                components['bios_info'] = f"{bios_info.get('SerialNumber', 'UNKNOWN')}_{bios_info.get('Version', 'UNKNOWN')}"
            else:
                components['bios_info'] = "UNKNOWN_BIOS"
        except:
            components['bios_info'] = "UNKNOWN_BIOS"
        
        components['platform'] = platform.platform()
        
        return components
    
    def generate_hardware_fingerprint(self, components: dict) -> str:
        """Tạo hardware fingerprint từ components"""
        combined_string = json.dumps(components, sort_keys=True)
        fingerprint = hashlib.sha256(combined_string.encode()).hexdigest()[:32]
        return fingerprint
    
    def generate_license(self):
        """Tạo license mới"""
        # Validate inputs
        customer = self.customer_name.get().strip()
        email = self.customer_email.get().strip()
        hardware_id = self.hardware_id.get().strip()
        
        if not customer or not email or not hardware_id:
            messagebox.showerror("Error", "Please fill in all required fields!\n\nRequired:\n- Customer Name\n- Customer Email\n- Hardware ID")
            # Scroll to top to show missing fields
            self.customer_name.focus()
            return
        
        # Generate license key
        license_key = self.generate_license_key()
        
        # Calculate expiry date
        duration_val = int(self.duration_value.get())
        duration_unit = self.duration_unit.get()
        
        if duration_unit == "days":
            expiry_date = datetime.utcnow() + timedelta(days=duration_val)
        elif duration_unit == "months":
            expiry_date = datetime.utcnow() + timedelta(days=duration_val * 30)
        else:  # years
            expiry_date = datetime.utcnow() + timedelta(days=duration_val * 365)
        
        # Get selected features
        features = []
        if self.feature_ai.get():
            features.append("ai_generation")
        if self.feature_unlimited.get():
            features.append("unlimited_workflows")
        if self.feature_api.get():
            features.append("api_access")
        if self.feature_priority.get():
            features.append("priority_support")
        
        # Create license record
        license_record = {
            'license_key': license_key,
            'customer_name': customer,
            'customer_email': email,
            'hardware_id': hardware_id,
            'license_type': self.license_type.get(),
            'expiry_date': expiry_date.isoformat(),
            'features': features,
            'activation_date': datetime.utcnow().isoformat(),
            'status': 'active',
            'created_by': 'License Admin Tool',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save to database
        self.license_database[license_key] = license_record
        self.save_license_database()
        
        # Display results
        self.license_key_display.delete(0, 'end')
        self.license_key_display.insert(0, license_key)
        
        details = f"""Customer: {customer}
Email: {email}
License Type: {self.license_type.get()}
Hardware ID: {hardware_id}
Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}
Features: {', '.join(features)}

License Key: {license_key}

=== License Record (JSON) ===
{json.dumps(license_record, indent=2, ensure_ascii=False)}
"""
        
        self.license_details.delete("1.0", "end")
        self.license_details.insert("1.0", details)
        
        # Refresh license list
        self.refresh_license_list()
        
        messagebox.showinfo("Success", f"License generated successfully!\nKey: {license_key}")
    
    def scan_hardware(self):
        """Quét hardware hiện tại"""
        self.scan_btn.configure(state="disabled", text="🔍 Scanning...")
        self.hardware_info_display.delete("1.0", "end")
        self.hardware_info_display.insert("1.0", "Scanning hardware components...\n\n")
        
        def scan_thread():
            try:
                components = self.get_hardware_components()
                hardware_id = self.generate_hardware_fingerprint(components)
                
                self.current_hardware_info = {
                    'components': components,
                    'hardware_id': hardware_id,
                    'scan_time': datetime.utcnow().isoformat(),
                    'platform': platform.platform(),
                    'hostname': platform.node()
                }
                
                # Display results
                display_text = f"""🖥️ HARDWARE SCAN RESULTS
{'='*50}

🆔 Hardware Fingerprint: {hardware_id}
🖥️ Hostname: {platform.node()}
🖥️ Platform: {platform.platform()}
⏰ Scan Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

📋 HARDWARE COMPONENTS:
{'='*30}

"""
                
                for key, value in components.items():
                    display_text += f"🔧 {key.upper()}: {value}\n"
                
                display_text += f"\n\n💾 SYSTEM INFORMATION:\n{'='*30}\n"
                display_text += f"🖥️ OS: {platform.system()} {platform.release()}\n"
                display_text += f"🏗️ Architecture: {platform.architecture()[0]}\n"
                display_text += f"🖥️ Machine: {platform.machine()}\n"
                display_text += f"💾 RAM: {psutil.virtual_memory().total // (1024**3)} GB\n"
                display_text += f"💿 CPU Cores: {psutil.cpu_count()}\n"
                
                # Update GUI in main thread
                self.root.after(0, lambda: self.update_hardware_display(display_text))
                
            except Exception as e:
                error_text = f"❌ ERROR during hardware scan:\n{str(e)}"
                self.root.after(0, lambda: self.update_hardware_display(error_text))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def update_hardware_display(self, text):
        """Update hardware display (called from main thread)"""
        self.hardware_info_display.delete("1.0", "end")
        self.hardware_info_display.insert("1.0", text)
        self.scan_btn.configure(state="normal", text="🔍 Scan Current Hardware")
        
        # Auto-fill hardware ID if generate tab is visible
        if self.current_hardware_info:
            self.hardware_id.delete(0, 'end')
            self.hardware_id.insert(0, self.current_hardware_info['hardware_id'])
    
    def export_hardware_info(self):
        """Export hardware info to file"""
        if not self.current_hardware_info:
            messagebox.showwarning("Warning", "Please scan hardware first!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Hardware Info",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_hardware_info, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Hardware info exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def import_hardware_info(self):
        """Import hardware info from file"""
        filename = filedialog.askopenfilename(
            title="Import Hardware Info",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    hardware_info = json.load(f)
                
                self.current_hardware_info = hardware_info
                
                # Display imported info
                display_text = f"""📁 IMPORTED HARDWARE INFO
{'='*50}

🆔 Hardware Fingerprint: {hardware_info['hardware_id']}
🖥️ Hostname: {hardware_info.get('hostname', 'N/A')}
🖥️ Platform: {hardware_info.get('platform', 'N/A')}
⏰ Original Scan Time: {hardware_info.get('scan_time', 'N/A')}

📋 HARDWARE COMPONENTS:
{'='*30}

"""
                
                for key, value in hardware_info['components'].items():
                    display_text += f"🔧 {key.upper()}: {value}\n"
                
                self.hardware_info_display.delete("1.0", "end")
                self.hardware_info_display.insert("1.0", display_text)
                
                # Auto-fill hardware ID
                self.hardware_id.delete(0, 'end')
                self.hardware_id.insert(0, hardware_info['hardware_id'])
                
                messagebox.showinfo("Success", "Hardware info imported successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import:\n{str(e)}")
    
    def copy_license_key(self):
        """Copy license key to clipboard"""
        key = self.license_key_display.get()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("Copied", "License key copied to clipboard!")
    
    def load_license_database(self) -> dict:
        """Load license database"""
        if self.license_db_path.exists():
            try:
                with open(self.license_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_license_database(self):
        """Save license database"""
        try:
            with open(self.license_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.license_database, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save database:\n{str(e)}")
    
    def refresh_license_list(self):
        """Refresh license list display"""
        # Clear existing buttons
        for btn in self.license_buttons:
            btn.destroy()
        self.license_buttons.clear()
        
        # Create new buttons
        for i, (key, license_data) in enumerate(self.license_database.items()):
            # Determine status color
            try:
                expiry = datetime.fromisoformat(license_data['expiry_date'])
                if datetime.utcnow() > expiry:
                    status = "Expired"
                    status_color = "#dc3545"
                else:
                    status = "Active"
                    status_color = "#28a745"
            except:
                status = "Unknown"
                status_color = "#6c757d"
            
            # Create license row frame
            row_frame = ctk.CTkFrame(self.license_scrollable, height=40, fg_color="#2b2b2b")
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)
            
            # License info
            info_text = f"{key} | {license_data.get('customer_name', 'N/A')} | {license_data.get('license_type', 'N/A')}"
            
            info_label = ctk.CTkLabel(row_frame, text=info_text, anchor="w")
            info_label.place(x=10, y=10)
            
            # Status
            status_label = ctk.CTkLabel(row_frame, text=status, text_color=status_color, font=ctk.CTkFont(weight="bold"))
            status_label.place(x=550, y=10)
            
            # Actions
            details_btn = ctk.CTkButton(row_frame, text="📋", width=30, height=25,
                                      command=lambda k=key: self.show_license_details(k))
            details_btn.place(x=620, y=7)
            
            delete_btn = ctk.CTkButton(row_frame, text="🗑️", width=30, height=25,
                                     fg_color="#dc3545", hover_color="#c82333",
                                     command=lambda k=key: self.delete_license(k))
            delete_btn.place(x=660, y=7)
            
            self.license_buttons.append(row_frame)
    
    def show_license_details(self, license_key):
        """Show license details in popup"""
        license_data = self.license_database.get(license_key)
        if not license_data:
            return
        
        details_window = ctk.CTkToplevel(self.root)
        details_window.title(f"License Details - {license_key}")
        details_window.geometry("600x500")
        details_window.transient(self.root)
        details_window.grab_set()
        
        # Center the window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (details_window.winfo_screenheight() // 2) - (500 // 2)
        details_window.geometry(f"600x500+{x}+{y}")
        
        # Content
        ctk.CTkLabel(details_window, text=f"License Details", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        
        details_text = ctk.CTkTextbox(details_window, font=ctk.CTkFont(family="Consolas"))
        details_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Format license details
        details_content = json.dumps(license_data, indent=2, ensure_ascii=False)
        details_text.insert("1.0", details_content)
        
        # Close button
        ctk.CTkButton(details_window, text="Close", command=details_window.destroy).pack(pady=(0, 20))
    
    def delete_license(self, license_key):
        """Delete license from database"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete license:\n{license_key}?"):
            del self.license_database[license_key]
            self.save_license_database()
            self.refresh_license_list()
            messagebox.showinfo("Deleted", "License deleted successfully!")
    
    def search_licenses(self):
        """Search licenses"""
        search_term = self.search_entry.get().lower()
        if not search_term:
            self.refresh_license_list()
            return
        
        # Filter licenses
        filtered_db = {}
        for key, data in self.license_database.items():
            if (search_term in key.lower() or 
                search_term in data.get('customer_name', '').lower() or
                search_term in data.get('customer_email', '').lower() or
                search_term in data.get('license_type', '').lower()):
                filtered_db[key] = data
        
        # Temporarily replace database for display
        original_db = self.license_database
        self.license_database = filtered_db
        self.refresh_license_list()
        self.license_database = original_db
    
    def export_database(self):
        """Export entire database"""
        filename = filedialog.asksaveasfilename(
            title="Export License Database",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.license_database, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Database exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def import_database(self):
        """Import database from file"""
        filename = filedialog.askopenfilename(
            title="Import License Database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_db = json.load(f)
                
                # Merge with existing database
                self.license_database.update(imported_db)
                self.save_license_database()
                self.refresh_license_list()
                
                messagebox.showinfo("Success", f"Imported {len(imported_db)} licenses successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import:\n{str(e)}")
    
    def bulk_generate(self):
        """Generate multiple licenses"""
        try:
            quantity = int(self.bulk_quantity.get())
            license_type = self.bulk_type.get()
            duration = int(self.bulk_duration.get())
            
            if quantity <= 0 or quantity > 1000:
                messagebox.showerror("Error", "Quantity must be between 1 and 1000!")
                return
            
            self.bulk_generate_btn.configure(state="disabled", text="🚀 Generating...")
            self.bulk_results.delete("1.0", "end")
            self.bulk_results.insert("1.0", f"Generating {quantity} licenses...\n\n")
            
            def generate_bulk():
                try:
                    results = []
                    expiry_date = datetime.utcnow() + timedelta(days=duration)
                    
                    for i in range(quantity):
                        license_key = self.generate_license_key()
                        
                        license_record = {
                            'license_key': license_key,
                            'customer_name': f'Bulk Customer {i+1}',
                            'customer_email': f'customer{i+1}@example.com',
                            'hardware_id': 'NOT_ASSIGNED',
                            'license_type': license_type,
                            'expiry_date': expiry_date.isoformat(),
                            'features': ['ai_generation', 'unlimited_workflows'],
                            'activation_date': datetime.utcnow().isoformat(),
                            'status': 'unassigned',
                            'created_by': 'Bulk Generator',
                            'created_at': datetime.utcnow().isoformat()
                        }
                        
                        self.license_database[license_key] = license_record
                        results.append(license_key)
                        
                        # Update progress
                        progress = f"Generated {i+1}/{quantity}: {license_key}\n"
                        self.root.after(0, lambda p=progress: self.bulk_results.insert("end", p))
                    
                    # Save database
                    self.save_license_database()
                    
                    # Show final results
                    final_text = f"\n{'='*50}\n✅ BULK GENERATION COMPLETE!\n{'='*50}\n"
                    final_text += f"Generated {quantity} licenses successfully!\n\n"
                    final_text += "License Keys:\n" + "\n".join(results)
                    
                    self.root.after(0, lambda: self.bulk_results.insert("end", final_text))
                    self.root.after(0, lambda: self.bulk_generate_btn.configure(state="normal", text="🚀 Generate Bulk Licenses"))
                    self.root.after(0, self.refresh_license_list)
                    
                except Exception as e:
                    error_text = f"\n❌ ERROR: {str(e)}\n"
                    self.root.after(0, lambda: self.bulk_results.insert("end", error_text))
                    self.root.after(0, lambda: self.bulk_generate_btn.configure(state="normal", text="🚀 Generate Bulk Licenses"))
            
            threading.Thread(target=generate_bulk, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers!")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main function"""
    app = LicenseAdminGUI()
    app.run()

if __name__ == "__main__":
    main() 