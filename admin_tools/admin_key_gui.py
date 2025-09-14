#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin Key Generator GUI
Modern GUI tool for generating license keys using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox
import json
import os
from pathlib import Path
from simple_key_generator import SimpleKeyGenerator

# Set appearance mode and color theme like main_window.py
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AdminKeyGUI:
    def __init__(self):
        self.generator = SimpleKeyGenerator()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the modern GUI interface"""
        self.root = ctk.CTk()
        self.root.title("ClausoNet 4.0 Pro - Admin Key Generator")
        self.root.geometry("1000x700")
        
        # Title header
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(title_frame, text="🔑 ClausoNet 4.0 Pro - Admin Key Generator",
                    font=ctk.CTkFont(size=20, weight="bold")).pack()
        
        # Main tabview like main_window.py
        self.tabview = ctk.CTkTabview(self.root, width=980, height=620)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Add tabs
        self.tabview.add("Generate Keys")
        self.tabview.add("View Keys")
        self.tabview.add("Statistics")
        
        # Set active tab
        self.tabview.set("Generate Keys")
        
        # Create tab contents
        self.create_generate_tab()
        self.create_view_tab()
        self.create_stats_tab()
        
    def create_generate_tab(self):
        """Create key generation tab"""
        generate_frame = self.tabview.tab("Generate Keys")
        
        # Input frame
        input_frame = ctk.CTkFrame(generate_frame)
        input_frame.pack(fill="x", padx=20, pady=20)
        
        # Input frame title
        ctk.CTkLabel(input_frame, text="📝 Key Generation Details", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))
        
        # Customer name
        customer_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        customer_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(customer_frame, text="Customer Name:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.customer_entry = ctk.CTkEntry(customer_frame, width=400, placeholder_text="Enter customer name...")
        self.customer_entry.pack(fill="x", pady=(5, 0))
        
        # License duration
        duration_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        duration_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(duration_frame, text="License Duration:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        # Radio buttons frame
        radio_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        radio_frame.pack(fill="x", pady=(5, 0))
        
        self.duration_var = ctk.StringVar(value="30")
        
        # Row 1: Quick options
        row1_frame = ctk.CTkFrame(radio_frame, fg_color="transparent")
        row1_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkRadioButton(row1_frame, text="3 days (Quick Trial)", 
                          variable=self.duration_var, value="3").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(row1_frame, text="7 days (Short Trial)", 
                          variable=self.duration_var, value="7").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(row1_frame, text="30 days (Trial)", 
                          variable=self.duration_var, value="30").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(row1_frame, text="90 days (Quarterly)", 
                          variable=self.duration_var, value="90").pack(side="left")
        
        # Row 2: Extended options
        row2_frame = ctk.CTkFrame(radio_frame, fg_color="transparent")
        row2_frame.pack(fill="x")
        
        ctk.CTkRadioButton(row2_frame, text="365 days (Yearly)", 
                          variable=self.duration_var, value="365").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(row2_frame, text="♾️ Permanent (99999 days)", 
                          variable=self.duration_var, value="99999").pack(side="left")
        
        # Custom duration
        custom_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        custom_frame.pack(fill="x", pady=(5, 0))
        
        custom_radio_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        custom_radio_frame.pack(side="left")
        
        ctk.CTkRadioButton(custom_radio_frame, text="Custom:", 
                          variable=self.duration_var, value="custom").pack(side="left")
        self.custom_days_entry = ctk.CTkEntry(custom_radio_frame, width=80, placeholder_text="Days")
        self.custom_days_entry.pack(side="left", padx=(10, 5))
        ctk.CTkLabel(custom_radio_frame, text="days").pack(side="left")
        
        # Notes
        notes_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        notes_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(notes_frame, text="Notes:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.notes_entry = ctk.CTkEntry(notes_frame, width=400, placeholder_text="Enter notes or description...")
        self.notes_entry.pack(fill="x", pady=(5, 0))
        
        # Generate button
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        generate_btn = ctk.CTkButton(button_frame, text="🔑 Generate License Key", 
                                   command=self.generate_key, height=40,
                                   font=ctk.CTkFont(size=14, weight="bold"))
        generate_btn.pack(pady=(0, 10))
        
        # Quick copy button
        quick_copy_btn = ctk.CTkButton(button_frame, text="📋 Copy Last Generated Key", 
                                     command=self.copy_key, height=35, width=200,
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     fg_color="#6c757d", hover_color="#5a6268")
        quick_copy_btn.pack()
        
        # Result frame
        result_frame = ctk.CTkFrame(generate_frame)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Result frame title
        ctk.CTkLabel(result_frame, text="📄 Generated License Key", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.result_text = ctk.CTkTextbox(result_frame, height=150, wrap="word")
        self.result_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # Copy button - Make it more visible
        copy_btn = ctk.CTkButton(result_frame, text="📋 Copy Key to Clipboard", 
                               command=self.copy_key, height=40, width=200,
                               font=ctk.CTkFont(size=13, weight="bold"),
                               fg_color="#17a2b8", hover_color="#138496")
        copy_btn.pack(pady=(0, 15))
        
    def create_view_tab(self):
        """Create key viewing tab"""
        view_frame = self.tabview.tab("View Keys")
        
        # Filters frame
        filter_frame = ctk.CTkFrame(view_frame)
        filter_frame.pack(fill="x", padx=20, pady=20)
        
        # Filter title
        ctk.CTkLabel(filter_frame, text="📊 License Keys Database", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Filter controls
        filter_controls = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_controls.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(filter_controls, text="Show:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        self.filter_var = ctk.StringVar(value="active")
        ctk.CTkRadioButton(filter_controls, text="Active Only", variable=self.filter_var, 
                          value="active", command=self.refresh_keys_list).pack(side="left", padx=(10, 20))
        ctk.CTkRadioButton(filter_controls, text="All Keys", variable=self.filter_var, 
                          value="all", command=self.refresh_keys_list).pack(side="left")
        
        # Keys list frame
        list_frame = ctk.CTkFrame(view_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # List title
        ctk.CTkLabel(list_frame, text="📋 Generated Keys", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        # Keys textbox (simplified display)
        self.keys_textbox = ctk.CTkTextbox(list_frame, height=300)
        self.keys_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Instruction label
        instruction_label = ctk.CTkLabel(list_frame, 
                                       text="💡 Tip: Copy any license key and paste it in the delete field below",
                                       font=ctk.CTkFont(size=11), 
                                       text_color=("gray60", "gray40"))
        instruction_label.pack(pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(view_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Refresh button
        refresh_btn = ctk.CTkButton(buttons_frame, text="🔄 Refresh List", 
                                  command=self.refresh_keys_list, height=35)
        refresh_btn.pack(side="left", padx=(0, 10))
        
        # Delete key button
        delete_btn = ctk.CTkButton(buttons_frame, text="🗑️ Delete Selected Key", 
                                 command=self.delete_key, height=35,
                                 fg_color="red", hover_color="darkred")
        delete_btn.pack(side="left", padx=(0, 10))
        
        # Entry for key to delete
        ctk.CTkLabel(buttons_frame, text="Key to delete:").pack(side="left", padx=(20, 5))
        self.delete_key_entry = ctk.CTkEntry(buttons_frame, width=300, placeholder_text="Enter license key (CNPRO-YYYYMMDD-XXXXX-YYYYY)...")
        self.delete_key_entry.pack(side="left", padx=(5, 10))
        
        # Quick copy button for last generated key
        copy_last_btn = ctk.CTkButton(buttons_frame, text="📋 Copy Last Key", 
                                    command=self.copy_last_key_to_delete, height=35, width=120)
        copy_last_btn.pack(side="left")
        
    def create_stats_tab(self):
        """Create statistics tab"""
        stats_frame = self.tabview.tab("Statistics")
        
        # Stats container
        stats_container = ctk.CTkFrame(stats_frame)
        stats_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(stats_container, text="📈 Database Statistics", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))
        
        # Stats display
        self.stats_text = ctk.CTkTextbox(stats_container, height=400, wrap="word")
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Refresh stats button
        refresh_stats_btn = ctk.CTkButton(stats_container, text="🔄 Refresh Statistics", 
                                        command=self.refresh_stats, height=35)
        refresh_stats_btn.pack(pady=(0, 10))
        
    def generate_key(self):
        """Generate a new license key"""
        try:
            # Get inputs
            customer_name = self.customer_entry.get().strip()
            notes = self.notes_entry.get().strip()
            
            # Determine duration
            duration_str = self.duration_var.get()
            if duration_str == "custom":
                try:
                    duration_days = int(self.custom_days_entry.get())
                    if duration_days <= 0:
                        raise ValueError("Duration must be positive")
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number of days")
                    return
            else:
                duration_days = int(duration_str)
            
            # Confirmation for permanent keys
            if duration_days >= 99999:
                confirm = messagebox.askyesno("Xác nhận tạo Key Vĩnh Viễn", 
                                            "⚠️ BẠN ĐANG TẠO LICENSE KEY VĨNH VIỄN\n\n"
                                            "♾️ Key này sẽ không bao giờ hết hạn!\n"
                                            "💰 Chỉ dành cho khách hàng Premium\n\n"
                                            "🔐 Bạn có chắc chắn muốn tạo key vĩnh viễn?")
                if not confirm:
                    return
                
            # Generate key
            license_key = self.generator.generate_license_key(
                duration_days, customer_name, notes
            )
            
            if license_key:
                # Determine display text for duration
                if duration_days >= 99999:
                    duration_display = "Permanent (Lifetime)"
                    email_duration = "Permanent (Never Expires)"
                else:
                    duration_display = f"{duration_days} days"
                    email_duration = f"{duration_days} days"
                
                # Display result
                result = f"""
🎉 LICENSE KEY GENERATED SUCCESSFULLY!

License Key: {license_key}
Customer: {customer_name or 'N/A'}
Duration: {duration_display}
Notes: {notes or 'N/A'}
Generated: {self.generator._get_current_time()}

📧 EMAIL TEMPLATE:
Subject: ClausoNet 4.0 Pro - License Key

Dear {customer_name or '[Customer Name]'},

Your ClausoNet 4.0 Pro license key has been generated:

License Key: {license_key}
Valid for: {email_duration}
Support: support@clausonet.com

Thank you for choosing ClausoNet 4.0 Pro!

Best regards,
ClausoNet Team
"""
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", result)
                self.current_key = license_key
                
                # Clear inputs
                self.customer_entry.delete(0, "end")
                self.notes_entry.delete(0, "end")
                
                messagebox.showinfo("Success", f"License key generated successfully!\n\nKey: {license_key}")
                
            else:
                messagebox.showerror("Error", "Failed to generate license key")
                
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {str(e)}")
            
    def copy_key(self):
        """Copy the current key to clipboard"""
        try:
            if hasattr(self, 'current_key') and self.current_key:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.current_key)
                messagebox.showinfo("📋 Key Copied!", 
                                  f"✅ License key copied to clipboard!\n\n🔑 Key: {self.current_key}\n\n📧 Ready to send to customer!")
            else:
                # Try to extract key from result text if available
                result_content = self.result_text.get("1.0", "end-1c")
                if "License Key:" in result_content:
                    # Extract key from result text
                    lines = result_content.split('\n')
                    for line in lines:
                        if line.strip().startswith("License Key:"):
                            key = line.split("License Key:")[1].strip()
                            if key:
                                self.root.clipboard_clear()
                                self.root.clipboard_append(key)
                                messagebox.showinfo("📋 Key Copied!", 
                                                  f"✅ License key copied to clipboard!\n\n🔑 Key: {key}")
                                return
                
                messagebox.showwarning("⚠️ No Key Found", "🔍 No license key available to copy!\n\n💡 Generate a key first, then copy it.")
        except Exception as e:
            messagebox.showerror("❌ Copy Failed", f"Failed to copy key to clipboard:\n\n{str(e)}")
    
    def delete_key(self):
        """Delete a license key"""
        try:
            key_to_delete = self.delete_key_entry.get().strip()
            if not key_to_delete:
                messagebox.showwarning("Warning", "Please enter a license key to delete")
                return
                
            # Validate key format
            if not key_to_delete.startswith("CNPRO-") or len(key_to_delete.split("-")) != 4:
                messagebox.showerror("Error", "Invalid license key format!\n\nExpected format: CNPRO-YYYYMMDD-XXXXX-YYYYY")
                return
                
            # Check if key exists first
            keys_list = self.generator.list_generated_keys(show_expired=True)
            key_exists = any(k['license_key'] == key_to_delete for k in keys_list)
            
            if not key_exists:
                messagebox.showerror("Error", f"License key not found in database:\n\n{key_to_delete}")
                return
                
            # Confirm deletion
            confirm = messagebox.askyesno("Confirm Deletion", 
                                        f"⚠️ DELETE LICENSE KEY\n\nKey: {key_to_delete}\n\n❌ This action cannot be undone!\n\nAre you sure you want to delete this key?")
            
            if not confirm:
                return
                
            # Delete from database (with fallback)
            success = self._delete_license_key_manual(key_to_delete)
            
            if success:
                messagebox.showinfo("✅ Deletion Successful", 
                                  f"License key deleted successfully!\n\n🔑 Key: {key_to_delete}\n\n📊 Database updated automatically.")
                self.delete_key_entry.delete(0, "end")
                self.refresh_keys_list()
                self.refresh_stats()
            else:
                messagebox.showerror("❌ Deletion Failed", 
                                   f"Failed to delete license key:\n\n{key_to_delete}\n\nPlease check the database file permissions.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Deletion failed: {str(e)}")
    
    def _delete_license_key_manual(self, license_key: str) -> bool:
        """Manual deletion method - fallback if main method not available"""
        try:
            # Try main method first
            if hasattr(self.generator, 'delete_license_key'):
                return self.generator.delete_license_key(license_key)
            
            # Fallback: manual deletion
            with open(self.generator.key_database, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if license_key not in data["keys"]:
                return False
                
            # Remove the key
            del data["keys"][license_key]
            data["metadata"]["total_keys"] = len(data["keys"])
            
            from datetime import datetime
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.generator.key_database, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"Manual delete error: {e}")
            return False
    
    def copy_last_key_to_delete(self):
        """Copy the most recent key to delete field"""
        try:
            keys_list = self.generator.list_generated_keys(show_expired=True)
            if keys_list:
                # Get the most recent key (first in list)
                last_key = keys_list[0]['license_key']
                self.delete_key_entry.delete(0, "end")
                self.delete_key_entry.insert(0, last_key)
                messagebox.showinfo("📋 Key Copied", f"Most recent key copied to delete field:\n\n{last_key}")
            else:
                messagebox.showwarning("Warning", "No license keys found in database")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy key: {str(e)}")
            
    def refresh_keys_list(self):
        """Refresh the keys list"""
        try:
            # Clear existing content
            self.keys_textbox.delete("1.0", "end")
                
            # Get keys
            show_expired = (self.filter_var.get() == "all")
            keys_list = self.generator.list_generated_keys(show_expired)
            
            if not keys_list:
                self.keys_textbox.insert("1.0", "No license keys found.\n\nGenerate some keys in the 'Generate Keys' tab!")
                return
            
            # Build display text
            display_text = f"📋 TOTAL KEYS: {len(keys_list)}\n"
            display_text += "=" * 80 + "\n\n"
            
            for i, key_info in enumerate(keys_list, 1):
                # Determine type based on duration
                duration = key_info['duration_days']
                if duration <= 3:
                    key_type = "3-Day Trial"
                elif duration <= 7:
                    key_type = "Short Trial"
                elif duration <= 30:
                    key_type = "Trial"
                elif duration <= 90:
                    key_type = "Quarterly"
                elif duration <= 365:
                    key_type = "Yearly"
                elif duration >= 99999:
                    key_type = "♾️ Permanent"
                else:
                    key_type = "Extended"
                
                # Status
                if key_info['is_expired']:
                    status = "❌ EXPIRED"
                elif duration >= 99999:
                    status = "♾️ Active (Permanent - Never Expires)"
                else:
                    status = f"✅ Active ({key_info['days_left']} days left)"
                
                # Format each key
                display_text += f"{i}. 🔑 {key_info['license_key']}\n"
                display_text += f"   👤 Customer: {key_info['customer_name'] or 'N/A'}\n"
                display_text += f"   📅 Created: {key_info['created_date']}\n"
                display_text += f"   ⏰ Expires: {key_info['expiry_date']}\n"
                display_text += f"   📊 Type: {key_type} ({duration} days)\n"
                display_text += f"   🚦 Status: {status}\n"
                display_text += f"   📝 Notes: {key_info.get('notes', 'N/A')}\n"
                display_text += "-" * 80 + "\n\n"
            
            self.keys_textbox.insert("1.0", display_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh list: {str(e)}")
            
    def refresh_stats(self):
        """Refresh statistics display"""
        try:
            stats = self.generator.get_database_stats()
            keys_list = self.generator.list_generated_keys(show_expired=True)
            
            # Create detailed statistics
            stats_text = f"""
📊 DATABASE STATISTICS
{'='*50}

📈 Overview:
• Total Keys Generated: {stats['total_keys']}
• Active Keys: {stats['active_keys']}
• Expired Keys: {stats['expired_keys']}
• Database Created: {stats['database_created']}

📋 Key Types Breakdown:
"""
            
            # Count by type
            day3_trial_count = sum(1 for k in keys_list if k['duration_days'] <= 3)
            short_trial_count = sum(1 for k in keys_list if 3 < k['duration_days'] <= 7)
            trial_count = sum(1 for k in keys_list if 7 < k['duration_days'] <= 30)
            quarterly_count = sum(1 for k in keys_list if 30 < k['duration_days'] <= 90)
            yearly_count = sum(1 for k in keys_list if 90 < k['duration_days'] <= 365)
            extended_count = sum(1 for k in keys_list if 365 < k['duration_days'] < 99999)
            permanent_count = sum(1 for k in keys_list if k['duration_days'] >= 99999)
            
            stats_text += f"• 3-Day Trial (≤3 days): {day3_trial_count}\n"
            stats_text += f"• Short Trial (4-7 days): {short_trial_count}\n"
            stats_text += f"• Trial (8-30 days): {trial_count}\n"
            stats_text += f"• Quarterly (31-90 days): {quarterly_count}\n"
            stats_text += f"• Yearly (91-365 days): {yearly_count}\n"
            stats_text += f"• Extended (366-99998 days): {extended_count}\n"
            stats_text += f"• ♾️ Permanent (≥99999 days): {permanent_count}\n"
            
            # Recent keys
            stats_text += f"\n📅 Recent Keys (Last 5):\n"
            for i, key_info in enumerate(keys_list[:5]):
                status = "EXPIRED" if key_info['is_expired'] else f"{key_info['days_left']} days left"
                stats_text += f"{i+1}. {key_info['license_key']} - {key_info['customer_name']} ({status})\n"
                
            # Database location
            stats_text += f"\n📁 Database File:\n{self.generator.key_database}\n"
            
            self.stats_text.delete("1.0", "end")
            self.stats_text.insert("1.0", stats_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh stats: {str(e)}")
            
    def run(self):
        """Run the GUI application"""
        # Load initial data
        self.refresh_keys_list()
        self.refresh_stats()
        
        # Start GUI
        self.root.mainloop()

# Add helper method to SimpleKeyGenerator
def _get_current_time(self):
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Monkey patch the method  
SimpleKeyGenerator._get_current_time = _get_current_time

if __name__ == "__main__":
    app = AdminKeyGUI()
    app.run() 