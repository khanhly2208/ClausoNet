#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Main GUI Window
Giao diện chính sử dụng CustomTkinter giống hệt như ảnh mẫu
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import asyncio
import json
import os
import time
import datetime
import hashlib
import platform
import subprocess
import psutil
import uuid
import queue
import logging
import pyperclip
import gc
from pathlib import Path
from typing import Dict, Any, List
from threading import Lock, RLock
from contextlib import contextmanager

# Import backend components
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.engine import AIEngine, ProcessingRequest
from core.content_generator import ContentGenerator
# from utils.license_wizard import LicenseWizard  # OLD LICENSE SYSTEM - REMOVED
# from admin_tools.license_key_generator import LicenseKeyGenerator  # COMPLEX ADMIN SYSTEM - REMOVED
from core.simple_license_system import SimpleLicenseSystem  # SIMPLIFIED USER SYSTEM
from utils.profile_manager import ChromeProfileManager
from utils.veo_automation import VeoAutomation, create_video_from_prompts
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import yaml
import time

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class StatusManager:
    """
    🔒 THREAD-SAFE STATUS MANAGER
    Xử lý status updates từ worker threads an toàn
    """

    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.status_queue = queue.Queue()
        self._running = False

    def start(self):
        """Start processing status updates"""
        if not self._running:
            self._running = True
            self.process_status_updates()

    def stop(self):
        """Stop processing status updates"""
        self._running = False

    def update_status(self, message):
        """Thread-safe status update"""
        if self._running:
            self.status_queue.put(message)

    def process_status_updates(self):
        """Process status updates in GUI thread"""
        if not self._running:
            return

        try:
            # Check if GUI still exists
            if not hasattr(self.gui, 'root') or not self.gui.root.winfo_exists():
                self._running = False
                return

            # Process all pending messages
            messages_processed = 0
            while messages_processed < 10:  # Limit per cycle to avoid GUI blocking
                try:
                    message = self.status_queue.get_nowait()
                    if hasattr(self.gui, 'status_var') and self.gui.status_var:
                        self.gui.status_var.set(message)
                    messages_processed += 1
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Status update error: {e}")
            self._running = False
            return

        # Schedule next processing cycle
        if self._running and hasattr(self.gui, 'root') and self.gui.root.winfo_exists():
            try:
                self.gui.root.after(100, self.process_status_updates)
            except Exception as e:
                print(f"Error scheduling status update: {e}")
                self._running = False

class ProgressTracker:
    """
    📊 PROGRESS TRACKING SYSTEM
    Track step-by-step progress cho Phase 3
    """

    def __init__(self, total_steps, callback=None):
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.step_details = []
        self._lock = Lock()

    def update(self, step_name, success=None, details=None):
        """Update progress with thread safety"""
        with self._lock:
            self.current_step += 1
            percentage = (self.current_step / self.total_steps) * 100

            step_info = {
                'step': self.current_step,
                'name': step_name,
                'percentage': percentage,
                'success': success,
                'details': details,
                'timestamp': time.time()
            }

            self.step_details.append(step_info)

            if self.callback:
                self.callback(step_info)

    def get_progress(self):
        """Get current progress safely"""
        with self._lock:
            return {
                'current_step': self.current_step,
                'total_steps': self.total_steps,
                'percentage': (self.current_step / self.total_steps) * 100,
                'details': self.step_details.copy()
            }

class VeoWorkflowEngine:
    """
    🎬 THREAD-SAFE VEO 3 WORKFLOW ENGINE
    Enhanced với thread safety và progress tracking
    """

    def __init__(self, gui_instance):
        self.gui = gui_instance  # Reference to main GUI
        self.driver = None
        self.wait = None
        self.current_element = None

        # 🔒 Thread safety
        self._lock = RLock()
        self._driver_lock = Lock()
        self._is_running = False

        # 🎯 ENHANCED CONFIGURATION: Triệt để fix timeout và session issues
        self.config = {
            'wait_timeout': 10,  # Increased from 5
            'retry_attempts': 5,  # Increased from 3
            'fast_mode': True,
            'prompt_retry_attempts': 5,  # Increased from 3
            'video_detection_retries': 5,  # Increased from 3
            'download_retry_attempts': 5,  # Increased from 3
            'session_recovery_attempts': 3,  # Increased from 2
            'retry_delay': 5,
            'video_generation_timeout': 600,  # 10 minutes for video generation
            'session_check_interval': 30,  # Check session every 30s
            'extended_timeout_for_complex_videos': 900,  # 15 minutes for complex videos
            'session_recovery_delay': 5  # Wait after session recovery
        }

        # 🔒 Thread-safe video tracking
        self._video_lock = Lock()
        self.downloaded_videos = set()
        self.current_session_videos = set()
        self.video_cache = {}
        
        # 🔢 Video counter for sequential naming (1_1, 1_2, 1_3...)
        self.video_counter = 0

        # 📊 Progress tracking
        self.progress_tracker = None

        # 🔒 Thread-safe status manager
        self.status_manager = None
        if hasattr(gui_instance, 'status_manager'):
            self.status_manager = gui_instance.status_manager

    def update_status(self, message):
        """Thread-safe status update - Legacy method, prefer update_status_with_log"""
        print(f"[VeoEngine] {message}")  # Console output with prefix
        if hasattr(self.gui, 'log_to_workflow'):
            # Use new log system if available
            self.gui.log_to_workflow(message, level='info')
        elif self.status_manager:
            self.status_manager.update_status(message)
        elif hasattr(self.gui, 'status_var'):
            # Fallback to direct update với root.after
            self.gui.root.after(0, lambda: self.gui.status_var.set(message))

    def update_status_with_log(self, message, level='info'):
        """Enhanced status update with log system"""
        print(f"[VeoEngine] {message}")  # Console output with prefix
        if hasattr(self.gui, 'update_status_with_log'):
            self.gui.update_status_with_log(message, level)
        else:
            # Fallback to legacy update
            self.update_status(message)

    @contextmanager
    def chrome_session(self, profile_name):
        """Context manager for Chrome session với automatic cleanup"""
        driver = None
        try:
            with self._driver_lock:
                self.update_status_with_log("🚀 Setting up Chrome session...")

                # 🎯 FIX: Use ProductionChromeDriverManager for exe compatibility
                try:
                    from utils.production_chrome_manager import ProductionChromeDriverManager
                    from utils.resource_manager import resource_manager
                    
                    chrome_manager = ProductionChromeDriverManager(resource_manager)
                    
                    # Get profile path from ProfileManager
                    profile_manager = self.gui.profile_manager
                    profile_path = str(profile_manager.base_profile_dir / profile_name)
                    
                    # Create driver using production manager
                    driver = chrome_manager.create_webdriver(
                        profile_path=profile_path,
                        headless=False,
                        debug_port=9222
                    )
                    
                    self.update_status_with_log("✅ Chrome session established with ProductionChromeManager")
                    
                except ImportError as e:
                    self.update_status_with_log(f"⚠️ Production manager not available, using fallback: {e}")
                    
                    # Fallback to original method
                    profile_manager = self.gui.profile_manager
                    profile_path = profile_manager.base_profile_dir / profile_name

                    options = Options()
                    options.add_argument(f"--user-data-dir={str(profile_path.absolute())}")
                    options.add_argument("--profile-directory=Default")
                    options.add_argument("--no-first-run")
                    options.add_argument("--no-default-browser-check")
                    options.add_argument("--disable-default-apps")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--no-sandbox")

                    # Create driver
                    driver = webdriver.Chrome(options=options)

                driver.implicitly_wait(2)
                self.driver = driver
                self.wait = WebDriverWait(driver, self.config['wait_timeout'])
                self.update_status_with_log("✅ Chrome session ready")

                yield driver

        except Exception as e:
            self.update_status_with_log(f"❌ Chrome setup failed: {e}", level='error')
            raise
        finally:
            # Cleanup
            if driver:
                try:
                    driver.quit()
                    self.update_status_with_log("🔒 Chrome session closed")
                except Exception as e:
                    self.update_status_with_log(f"⚠️ Chrome cleanup warning: {e}", level='warning')

            self.driver = None
            self.wait = None

    def setup_chrome_for_gui(self, profile_name):
        """Legacy method - use chrome_session context manager instead"""
        self.update_status("🚀 Setting up Chrome for Veo workflow...")

        try:
            with self._driver_lock:
                # 🎯 FIX: Use ProductionChromeDriverManager for exe compatibility
                try:
                    from utils.production_chrome_manager import ProductionChromeDriverManager
                    from utils.resource_manager import resource_manager
                    
                    chrome_manager = ProductionChromeDriverManager(resource_manager)
                    
                    # Get profile path from ProfileManager
                    profile_manager = self.gui.profile_manager
                    profile_path = str(profile_manager.base_profile_dir / profile_name)
                    
                    # Create driver using production manager
                    self.driver = chrome_manager.create_webdriver(
                        profile_path=profile_path,
                        headless=False,
                        debug_port=9222
                    )
                    
                    self.update_status("✅ Chrome setup complete with ProductionChromeManager")
                    
                except ImportError as e:
                    self.update_status(f"⚠️ Production manager not available, using fallback: {e}")
                    
                    # Fallback to original method
                    profile_manager = self.gui.profile_manager
                    profile_path = profile_manager.base_profile_dir / profile_name

                    options = Options()
                    options.add_argument(f"--user-data-dir={str(profile_path.absolute())}")
                    options.add_argument("--profile-directory=Default")
                    options.add_argument("--no-first-run")
                    options.add_argument("--no-default-browser-check")
                    options.add_argument("--disable-default-apps")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-popup-blocking")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")

                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        from selenium.webdriver.chrome.service import Service
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=options)
                    except ImportError:
                        self.driver = webdriver.Chrome(options=options)

                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.update_status("✅ Chrome setup complete!")

                self.wait = WebDriverWait(self.driver, self.config['wait_timeout'])
                return True

        except Exception as e:
            self.update_status(f"❌ Chrome setup failed: {e}")
            return False

    def navigate_to_veo(self):
        """Navigate to Google Veo"""
        self.update_status_with_log("🌐 Navigating to Google Veo...")

        try:
            veo_url = "https://labs.google/fx/vi/tools/flow"
            self.driver.get(veo_url)

            # Wait for page load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            self.update_status_with_log("✅ Navigated to Veo successfully")
            return True

        except Exception as e:
            self.update_status_with_log(f"❌ Navigation failed: {e}", level='error')
            return False

    def find_new_project_button(self):
        """Tìm nút tạo dự án mới"""
        self.update_status_with_log("🔍 Finding New Project button...")

        selectors = [
            "//button[contains(text(), 'Dự án mới')]",
            "//button[contains(text(), 'New project')]",
            "//button[contains(text(), 'Tạo')]",
            "//button[contains(., 'add') and contains(text(), 'Dự án')]",
            "//header//button[1]",
            "//nav//button[contains(text(), 'Dự án')]"
        ]

        for selector in selectors:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if element and element.is_displayed():
                    self.update_status_with_log("✅ Found New Project button")
                    return element
            except TimeoutException:
                continue

        self.update_status_with_log("❌ New Project button not found", level='error')
        return None

    def safe_click(self, element, element_name="element"):
        """Click element với multiple fallback methods"""
        if not element:
            self.update_status_with_log(f"❌ Cannot click {element_name}: element is None", level='error')
            return False

        methods = [
            ("Regular Click", lambda: element.click()),
            ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains Click", lambda: ActionChains(self.driver).move_to_element(element).click().perform())
        ]

        for method_name, click_func in methods:
            try:
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)

                click_func()
                time.sleep(1)
                self.update_status_with_log(f"✅ {element_name} clicked using {method_name}")
                return True

            except Exception as e:
                continue

        self.update_status_with_log(f"❌ All click methods failed for {element_name}", level='error')
        return False

    def safe_click_send_button(self, element):
        """🎯 SPECIAL: Enhanced send button click với comprehensive verification"""
        if not element:
            self.update_status("❌ Cannot click send button: element is None")
            return False

        self.update_status("🎯 ENHANCED: Clicking send button with verification...")
        
        # Pre-click validation
        pre_validation = self._validate_send_button(element)
        if not pre_validation['is_valid']:
            self.update_status(f"❌ Pre-click validation failed: {pre_validation['reason']}")
            return False
        
        self.update_status(f"✅ Pre-click validation passed: {pre_validation['reason']}")
        
        # Enhanced click methods for send button
        methods = [
            ("Regular Click", lambda: element.click()),
            ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains Click", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
            ("Force Focus + Click", lambda: self._force_focus_click(element)),
            ("Event Dispatch Click", lambda: self._event_dispatch_click(element))
        ]

        for method_name, click_func in methods:
            try:
                self.update_status(f"🔧 Trying {method_name}...")
                
                # Scroll to element and ensure visibility
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)

                # Store state before click
                pre_click_url = self.driver.current_url
                
                # Perform click
                click_func()
                time.sleep(2)  # Wait for action to process
                
                # Post-click verification
                post_click_verification = self._verify_send_button_action()
                
                if post_click_verification['success']:
                    self.update_status(f"✅ Send button clicked successfully using {method_name}")
                    self.update_status(f"✅ Post-click verification: {post_click_verification['reason']}")
                    return True
                else:
                    self.update_status(f"⚠️ {method_name} clicked but no send action detected: {post_click_verification['reason']}")
                    continue

            except Exception as e:
                self.update_status(f"⚠️ {method_name} failed: {e}")
                continue

        self.update_status("❌ All send button click methods failed")
        return False

    def _force_focus_click(self, element):
        """Force focus and click"""
        self.driver.execute_script("""
            var elem = arguments[0];
            elem.focus();
            elem.click();
        """, element)

    def _event_dispatch_click(self, element):
        """Dispatch click event directly"""
        self.driver.execute_script("""
            var elem = arguments[0];
            var event = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true
            });
            elem.dispatchEvent(event);
        """, element)

    def _verify_send_button_action(self):
        """Verify that send button click actually triggered the expected action"""
        try:
            # Wait a moment for UI to react
            time.sleep(1)
            
            # Check for signs that prompt was sent
            verification_indicators = [
                # 1. URL change (navigation to generation page)
                lambda: self._check_url_change(),
                
                # 2. Loading/generation indicators
                lambda: self._check_loading_indicators(),
                
                # 3. UI state changes
                lambda: self._check_ui_state_change(),
                
                # 4. Send button state change
                lambda: self._check_send_button_disabled()
            ]
            
            for indicator in verification_indicators:
                try:
                    result = indicator()
                    if result['positive']:
                        return {'success': True, 'reason': result['reason']}
                except:
                    continue
            
            return {'success': False, 'reason': 'No positive indicators of send action detected'}
            
        except Exception as e:
            return {'success': False, 'reason': f'Verification error: {e}'}

    def _check_url_change(self):
        """Check if URL changed indicating navigation"""
        current_url = self.driver.current_url
        if 'loading' in current_url or 'generate' in current_url or 'processing' in current_url:
            return {'positive': True, 'reason': f'URL changed to: {current_url[-50:]}'}
        return {'positive': False, 'reason': 'No URL change detected'}

    def _check_loading_indicators(self):
        """Check for loading/generation indicators"""
        loading_selectors = [
            "[class*='loading']", "[class*='spinner']", "[class*='progress']",
            "//*[contains(text(), 'Generating')]", "//*[contains(text(), 'Processing')]",
            "//*[contains(text(), 'Đang tạo')]", "//*[contains(text(), 'Đang xử lý')]"
        ]
        
        for selector in loading_selectors:
            try:
                if selector.startswith('//'):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if any(elem.is_displayed() for elem in elements):
                    return {'positive': True, 'reason': f'Loading indicator found: {selector}'}
            except:
                continue
        
        return {'positive': False, 'reason': 'No loading indicators found'}

    def _check_ui_state_change(self):
        """Check for significant UI state changes"""
        try:
            # Check if prompt input is now disabled/hidden
            prompt_inputs = self.driver.find_elements(By.XPATH, "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']")
            if prompt_inputs:
                prompt_input = prompt_inputs[0]
                if not prompt_input.is_enabled() or not prompt_input.is_displayed():
                    return {'positive': True, 'reason': 'Prompt input disabled/hidden after send'}
            
            # Check page title change
            title = self.driver.title
            if any(keyword in title.lower() for keyword in ['generating', 'processing', 'đang tạo']):
                return {'positive': True, 'reason': f'Page title indicates processing: {title}'}
            
            return {'positive': False, 'reason': 'No significant UI state change detected'}
        except:
            return {'positive': False, 'reason': 'UI state check failed'}

    def _check_send_button_disabled(self):
        """Check if send button is now disabled"""
        try:
            # Re-find potential send buttons and check if disabled
            send_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'arrow_forward') or @type='submit']")
            disabled_count = len([btn for btn in send_buttons if btn.is_displayed() and not btn.is_enabled()])
            
            if disabled_count > 0:
                return {'positive': True, 'reason': f'{disabled_count} send buttons now disabled'}
            
            return {'positive': False, 'reason': 'Send buttons still enabled'}
        except:
            return {'positive': False, 'reason': 'Send button state check failed'}

    def find_prompt_input(self):
        """Enhanced prompt input detection với UI settlement"""
        self.update_status("🔍 Finding prompt input...")
        
        # 🎯 ENHANCED: Wait for UI to fully settle
        self.update_status("⏳ Waiting for UI to fully settle...")
        time.sleep(2)
        
        # 🎯 ENHANCED: Multiple scroll attempts to find prompt input
        scroll_attempts = [
            "window.scrollTo(0, 0);",  # Top of page
            "window.scrollTo(0, document.body.scrollHeight/4);",  # Quarter down
            "window.scrollTo(0, document.body.scrollHeight/3);",  # Third down  
            "window.scrollTo(0, document.body.scrollHeight/2);",  # Half down
        ]
        
        for i, scroll_script in enumerate(scroll_attempts):
            self.update_status(f"📜 Scroll attempt {i+1}: Positioning viewport...")
            self.driver.execute_script(scroll_script)
            time.sleep(1)
            
            # Quick check if prompt input is now visible
            try:
                quick_check = self.driver.find_elements(By.XPATH, "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']")
                if quick_check and quick_check[0].is_displayed():
                    self.update_status(f"✅ Prompt input visible after scroll {i+1}")
                    break
            except:
                pass

        selectors = [
            "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
            "//textarea[contains(@placeholder, 'Tạo một video bằng văn bản')]",
            "//textarea[contains(@placeholder, 'Nhập vào ô nhập câu lệnh')]", 
            "//textarea[contains(@placeholder, 'prompt')]",
            "//textarea[contains(@placeholder, 'video')]",
            "//textarea[not(@disabled)]"
        ]

        for i, selector in enumerate(selectors):
            try:
                self.update_status(f"🔍 Trying selector {i+1}/{len(selectors)}...")
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                
                # 🎯 ENHANCED: Verify element is truly clickable
                if element and element.is_displayed() and element.is_enabled():
                    # 🎯 ENHANCED: More flexible intercept detection
                    is_clickable = self.driver.execute_script("""
                        var elem = arguments[0];
                        var rect = elem.getBoundingClientRect();
                        
                        // Check multiple points to be more flexible
                        var points = [
                            {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2},  // Center
                            {x: rect.left + 10, y: rect.top + 10},  // Top-left corner
                            {x: rect.right - 10, y: rect.top + 10},  // Top-right corner
                            {x: rect.left + 10, y: rect.bottom - 10},  // Bottom-left corner
                            {x: rect.right - 10, y: rect.bottom - 10}  // Bottom-right corner
                        ];
                        
                        for (var i = 0; i < points.length; i++) {
                            var point = points[i];
                            var elementAtPoint = document.elementFromPoint(point.x, point.y);
                            
                            // If we find the element or its child at any point, it's clickable
                            if (elementAtPoint === elem || elem.contains(elementAtPoint) || 
                                (elementAtPoint && elementAtPoint.tagName === 'TEXTAREA')) {
                                return true;
                            }
                        }
                        
                        // Final check: is element in viewport and not hidden?
                        return rect.width > 0 && rect.height > 0 && 
                               elem.offsetParent !== null &&
                               rect.top < window.innerHeight && rect.bottom > 0;
                    """, element)
                    
                    if is_clickable:
                        self.update_status("✅ Found accessible prompt input")
                        return element
                    else:
                        self.update_status(f"⚠️ Element found but intercepted, trying next...")
                        
            except TimeoutException:
                continue
            except Exception as e:
                self.update_status(f"⚠️ Selector {i+1} failed: {e}")
                continue

        # 🎯 FALLBACK: Aggressive prompt input detection
        self.update_status("⚠️ All selectors failed, trying aggressive detection...")
        
        try:
            # Method 1: Find any textarea and force it to be prompt input
            all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in all_textareas:
                if textarea.is_displayed():
                    # Force scroll element into view and try to make it accessible
                    self.driver.execute_script("""
                        var elem = arguments[0];
                        elem.scrollIntoView({behavior: 'smooth', block: 'center'});
                        
                        // Remove any overlaying elements
                        var overlays = document.querySelectorAll('[style*="position: absolute"], [style*="position: fixed"]');
                        overlays.forEach(function(overlay) {
                            if (overlay.style.zIndex > 100) {
                                overlay.style.display = 'none';
                            }
                        });
                        
                        // Focus the element
                        elem.focus();
                        elem.click();
                    """, textarea)
                    
                    time.sleep(2)
                    
                    # Test if it's now accessible
                    try:
                        textarea.send_keys("")  # Test input
                        self.update_status("✅ Found accessible textarea via aggressive method")
                        return textarea
                    except:
                        continue
                        
        except Exception as e:
            self.update_status(f"⚠️ Aggressive detection failed: {e}")
        
        # Method 2: JavaScript injection to create/find prompt input
        try:
            self.update_status("🔧 Final attempt: JavaScript prompt input injection...")
            prompt_element = self.driver.execute_script("""
                // Find any element that looks like a prompt input
                var candidates = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
                
                for (var i = 0; i < candidates.length; i++) {
                    var elem = candidates[i];
                    if (elem.offsetHeight > 0 && elem.offsetWidth > 0) {
                        // Make sure it's visible and accessible
                        elem.style.display = 'block';
                        elem.style.visibility = 'visible';
                        elem.style.position = 'relative';
                        elem.style.zIndex = '9999';
                        
                        // Focus and return
                        elem.focus();
                        return elem;
                    }
                }
                return null;
            """)
            
            if prompt_element:
                self.update_status("✅ JavaScript injection found prompt input")
                return prompt_element
                
        except Exception as e:
            self.update_status(f"⚠️ JavaScript injection failed: {e}")

        self.update_status("❌ All methods exhausted - prompt input not accessible")
        return None



    def type_prompt_enhanced_with_send_verification(self, element, prompt_text, max_attempts=3):
        """🎯 SIMPLIFIED: Single paste method for prompt input"""
        self.update_status(f"📋 PASTE METHOD: Pasting prompt from clipboard...")
        
        try:
            # Method: Simple paste using Ctrl+V
            return self._paste_method_simple(element, prompt_text)
            
        except Exception as e:
            self.update_status(f"❌ Paste method failed: {e}")
            return False

    def _paste_method_simple(self, element, prompt_text):
        """📋 SIMPLE PASTE: Copy to clipboard and paste with Ctrl+V"""
        import pyperclip
        from selenium.webdriver.common.keys import Keys
        
        # Copy to clipboard and paste
        pyperclip.copy(prompt_text)
        
        # Focus and paste
        try:
            element.click()
            element.clear()
            self.driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.2)  # Reduced delay
        except Exception as e:
            pass  # Continue anyway
        
        # Paste using Ctrl+V
        element.send_keys(Keys.CONTROL + "v")
        
        # Trigger input events
        self.driver.execute_script("""
            var elem = arguments[0];
            elem.dispatchEvent(new Event('input', {bubbles: true}));
            elem.dispatchEvent(new Event('change', {bubbles: true}));
        """, element)
        
        time.sleep(0.5)  # Reduced wait time
        
        # Wait for send button to appear
        send_button_found = self._wait_for_send_button_appearance(timeout=5)
        
        if send_button_found:
            self.update_status("✅ PASTE SUCCESSFUL - Send button appeared!")
            return True
        else:
            self.update_status("⚠️ Send button not found after paste")
            return False

# Old complex methods removed - now using simple paste method only





    def _wait_for_send_button_appearance(self, timeout=10):
        """Wait for send button to appear after prompt input"""
        # Scanning for send button (silent for speed)
        
        start_time = time.time()
        
        # Enhanced send button selectors based on user description of white arrow
        send_button_selectors = [
            # 🎯 WHITE ARROW BUTTON (specific from user description - "nút sent pormt hình mũi trên trắng")
            "//button[.//*[local-name()='svg' and contains(@fill, 'white')]]",
            "//button[.//*[local-name()='svg' and contains(@stroke, 'white')]]", 
            "//button[.//*[local-name()='path' and contains(@fill, '#fff')]]",
            "//button[.//*[local-name()='path' and contains(@fill, 'white')]]",
            "//button[contains(@style, 'color: white') or contains(@style, 'color:#fff')]",
            
            # Arrow-specific patterns
            "//button[contains(., 'arrow_forward')]",
            "//button[contains(., '→')]", 
            "//button[contains(., '▶')]",
            "//button[contains(., '►')]",
            "//button[.//*[contains(@d, 'M') and contains(@d, 'L')]]", # SVG path for arrows
            
            # Send button patterns
            "//button[contains(@aria-label, 'Send') or contains(@aria-label, 'submit')]",
            "//button[contains(@title, 'Send') or contains(@title, 'Gửi')]",
            "//button[contains(@class, 'send')]",
            
            # Position-based (near textarea)
            "//textarea/..//button[not(@disabled)]",
            "//textarea/following-sibling::*//button[not(@disabled)]",
            "//textarea/parent::*/following-sibling::*//button[not(@disabled)]",
            
            # Submit patterns
            "//button[@type='submit' and not(@disabled)]",
            "//input[@type='submit' and not(@disabled)]"
        ]
        
        while time.time() - start_time < timeout:
            for selector in send_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # Additional verification - check if it's actually a send button
                            button_text = button.get_attribute('textContent') or ''
                            button_aria = button.get_attribute('aria-label') or ''
                            button_title = button.get_attribute('title') or ''
                            
                            # Check for send-related attributes
                            is_send_button = any(keyword in (button_text + button_aria + button_title).lower() 
                                               for keyword in ['send', 'gửi', 'submit', 'arrow'])
                            
                            # 🎯 ENHANCED: Check for white arrow icon (user's specific description)
                            has_white_icon = self.driver.execute_script("""
                                var btn = arguments[0];
                                
                                // Check SVGs, paths, and icons
                                var elements = btn.querySelectorAll('svg, path, i, span, div');
                                for (var i = 0; i < elements.length; i++) {
                                    var elem = elements[i];
                                    var style = window.getComputedStyle(elem);
                                    
                                    // Check fill colors
                                    if (style.fill === '#ffffff' || style.fill === 'white' || 
                                        style.fill === '#fff' || style.fill.toLowerCase() === 'white') {
                                        return true;
                                    }
                                    
                                    // Check stroke colors (for outline arrows)
                                    if (style.stroke === '#ffffff' || style.stroke === 'white' || 
                                        style.stroke === '#fff' || style.stroke.toLowerCase() === 'white') {
                                        return true;
                                    }
                                    
                                    // Check text color
                                    if (style.color === '#ffffff' || style.color === 'white' || 
                                        style.color === '#fff' || style.color.toLowerCase() === 'white') {
                                        return true;
                                    }
                                    
                                    // Check background color (for colored arrow backgrounds)
                                    if (style.backgroundColor === '#ffffff' || style.backgroundColor === 'white') {
                                        return true;
                                    }
                                }
                                
                                // Check button style itself
                                var btnStyle = window.getComputedStyle(btn);
                                if (btnStyle.color === '#ffffff' || btnStyle.color === 'white' || 
                                    btnStyle.fill === '#ffffff' || btnStyle.fill === 'white') {
                                    return true;
                                }
                                
                                // Check for arrow unicode characters
                                var text = btn.textContent || btn.innerHTML || '';
                                if (text.includes('→') || text.includes('▶') || text.includes('►') || 
                                    text.includes('arrow_forward') || text.includes('send')) {
                                    return true;
                                }
                                
                                return false;
                            """, button)
                            
                            if is_send_button or has_white_icon:
                                self.update_status(f"✅ Found send button: {selector}")
                                return True
                                
                except Exception as e:
                    continue
            
            # Update status every 2 seconds with button scan info
            elapsed = int(time.time() - start_time)
            if elapsed % 2 == 0 and elapsed > 0:
                # Debug: Count visible buttons
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    visible_buttons = [btn for btn in all_buttons if btn.is_displayed() and btn.is_enabled()]
                    self.update_status(f"⏳ Still waiting for send button... ({elapsed}s elapsed) - {len(visible_buttons)} buttons visible")
                except:
                    self.update_status(f"⏳ Still waiting for send button... ({elapsed}s elapsed)")
            
            time.sleep(0.5)
        
        # 🎯 DEBUG: If send button not found, show what buttons ARE available
        try:
            self.update_status("🔍 DEBUG: Send button not found, scanning all available buttons...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            visible_buttons = []
            
            for i, btn in enumerate(all_buttons):
                if btn.is_displayed() and btn.is_enabled():
                    btn_text = (btn.get_attribute('textContent') or '')[:30]
                    btn_aria = (btn.get_attribute('aria-label') or '')[:20]
                    btn_class = (btn.get_attribute('class') or '')[:20]
                    visible_buttons.append(f"[{i}] '{btn_text}' aria='{btn_aria}' class='{btn_class}'")
            
            self.update_status(f"📋 Found {len(visible_buttons)} visible buttons:")
            for btn_info in visible_buttons[:5]:  # Show first 5
                self.update_status(f"   {btn_info}")
                
            if len(visible_buttons) > 5:
                self.update_status(f"   ... and {len(visible_buttons) - 5} more buttons")
                
        except Exception as e:
            self.update_status(f"⚠️ Debug scan failed: {e}")
        
        self.update_status("❌ Send button did not appear within timeout")
        return False

    def _clear_prompt_input(self, element):
        """Clear prompt input completely"""
        try:
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.value = '';
                elem.innerHTML = '';
                elem.textContent = '';
                elem.dispatchEvent(new Event('input', {bubbles: true}));
                elem.dispatchEvent(new Event('change', {bubbles: true}));
            """, element)
        except:
            pass

    def type_prompt_enhanced(self, element, prompt_text):
        """📋 SIMPLIFIED: Redirect to paste method"""
        return self.type_prompt_enhanced_with_send_verification(element, prompt_text)

    def find_send_button(self):
        """🎯 DIAGNOSTIC: Enhanced send button detection với comprehensive validation"""
        self.update_status("🔍 Finding send button...")

        # Skip verbose UI diagnostic for speed

        # Reduced wait time for speed
        time.sleep(1)

        selectors = [
            "//button[contains(., 'arrow_forward')]",
            "//button[contains(., '→')]",
            "//button[contains(., '▶')]",
            "//button[contains(., 'send')]",
            "//button[@type='submit'][contains(., 'arrow_forward')]",
            "//button[@type='submit'][not(@disabled)]",
            "//button[contains(text(), 'Tạo')]",
            "//button[contains(text(), 'Create')]",
            "//button[contains(text(), 'Generate')]"
        ]

        # Enhanced: Scan all buttons and score them
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            send_candidates = []

            for btn in all_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    text = btn.text.strip()
                    innerHTML = btn.get_attribute('innerHTML') or ''

                    # Check for send-like characteristics
                    is_send_candidate = (
                        'arrow' in innerHTML.lower() or
                        '→' in innerHTML or '▶' in innerHTML or
                        'send' in text.lower() or 'tạo' in text.lower() or
                        'create' in text.lower() or 'generate' in text.lower() or
                        btn.get_attribute('type') == 'submit'
                    )

                    if is_send_candidate:
                        send_candidates.append({
                            'element': btn,
                            'text': text,
                            'innerHTML': innerHTML[:100],
                            'type': btn.get_attribute('type')
                        })

            if send_candidates:
                # Score and find best candidate
                best_candidate = None
                best_score = -1

                for candidate in send_candidates:
                    score = 0
                    text = candidate['text'].lower()
                    innerHTML = candidate['innerHTML'].lower()

                    # Scoring system
                    if 'arrow_forward' in innerHTML and 'tạo' in text:
                        score += 100
                    elif 'arrow_forward' in innerHTML and len(text) < 10:
                        score += 90
                    elif candidate['type'] == 'submit' and 'arrow' in innerHTML:
                        score += 80
                    elif any(word in text for word in ['tạo', 'create', 'send', 'generate']):
                        score += 60

                    # Penalties
                    if len(text) > 20:
                        score -= 30
                    if any(avoid in text for avoid in ['chỉnh sửa', 'edit', 'help', 'ultra']):
                        score -= 50

                    if score > best_score:
                        best_score = score
                        best_candidate = candidate

                if best_candidate:
                    # 🎯 ENHANCED VALIDATION: Verify this is actually a functional send button
                    validation_result = self._validate_send_button(best_candidate['element'])
                    if validation_result['is_valid']:
                        self.update_status("✅ Send button found")
                        return best_candidate['element']
                    else:
                        self.update_status(f"⚠️ Best candidate failed validation (score: {best_score}) - {validation_result['reason']}")
                        # Continue to fallback selectors

        except Exception as e:
            self.update_status(f"⚠️ Enhanced scan failed: {e}")

        # Fallback to original selectors
        for selector in selectors:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if element and element.is_displayed() and element.is_enabled():
                    self.update_status("✅ Found send button (fallback)")
                    return element
            except TimeoutException:
                continue

        self.update_status("❌ Send button not found")
        return None

    def wait_for_video_generation(self, timeout=None):
        """Enhanced wait with session recovery và progressive timeout"""
        # 🎯 USE CONFIG VALUES
        if timeout is None:
            timeout = self.config['video_generation_timeout']
        
        session_check_interval = self.config['session_check_interval']
        
        self.update_status("⏳ Waiting for video generation to complete...")

        start_time = time.time()
        last_session_check = time.time()

        while time.time() - start_time < timeout:
            try:
                # 🎯 SESSION RECOVERY: Check session alive every 30s
                current_time = time.time()
                if current_time - last_session_check > session_check_interval:
                    if not self.is_session_alive():
                        self.update_status("⚠️ Session disconnected, attempting recovery...")
                        if self.recover_session():
                            self.update_status("✅ Session recovered successfully")
                        else:
                            self.update_status("❌ Session recovery failed")
                            return False
                    last_session_check = current_time

                # Check for completion indicators
                completion_selectors = [
                    "//video[@src and @src!='' and (contains(@src, 'blob:') or contains(@src, 'http'))]",
                    "//button[contains(text(), 'Tải xuống') or contains(text(), 'Download')]",
                    "//button[contains(@aria-label, 'download') or contains(@aria-label, 'Download')]",
                    "//*[contains(text(), 'hoàn thành') or contains(text(), 'completed')]",
                    "//*[contains(text(), 'sẵn sàng') or contains(text(), 'ready')]",
                    "//div[contains(@class, 'video-complete') or contains(@class, 'generation-complete')]"
                ]

                for selector in completion_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    visible_elements = [e for e in elements if e.is_displayed()]

                    if visible_elements:
                        if "video[@src" in selector:
                            for video_elem in visible_elements:
                                src = video_elem.get_attribute('src')
                                if src and len(src) > 20:
                                    self.update_status("✅ Video generation completed!")
                                    return True
                        else:
                            self.update_status("✅ Video generation completed!")
                            return True

                # Update status periodically với progressive timeouts
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0:  # Update every 30s instead of 10s
                    if elapsed < 120:
                        self.update_status(f"⏳ Still generating... ({elapsed}s elapsed) - Normal timing")
                    elif elapsed < 300:
                        self.update_status(f"⏳ Still generating... ({elapsed}s elapsed) - Complex video processing")
                    else:
                        self.update_status(f"⏳ Still generating... ({elapsed}s elapsed) - Extended processing (max: {timeout}s)")

                time.sleep(10)  # Check every 10s instead of 5s

            except Exception as e:
                error_msg = str(e)
                if "invalid session id" in error_msg.lower() or "session deleted" in error_msg.lower():
                    self.update_status("⚠️ Session lost during wait, attempting recovery...")
                    if self.recover_session():
                        self.update_status("✅ Session recovered, continuing wait...")
                        continue
                    else:
                        self.update_status("❌ Session recovery failed during video wait")
                        return False
                else:
                    self.update_status(f"⚠️ Error while waiting: {e}")
                    time.sleep(10)

        self.update_status(f"⏰ Timeout reached ({timeout}s). Video may still be generating.")
        return False

    def is_session_alive(self):
        """Check if Chrome session is still alive"""
        try:
            # Simple check - try to get page title
            self.driver.title
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['invalid session', 'session deleted', 'disconnected', 'no such window']):
                return False
            return True

    def recover_session(self):
        """Recover Chrome session sau khi bị disconnect"""
        self.update_status("🔄 Attempting session recovery...")
        
        try:
            # Try to reconnect to existing session first
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                
            # Wait for cleanup with config delay
            time.sleep(self.config['session_recovery_delay'])
            
            # Re-establish Chrome session directly
            self.update_status("🔄 Creating new Chrome session...")
            
            # Import necessary modules
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Get profile path from GUI
            profile_name = self.gui.veo_profile_var.get()
            if not profile_name:
                self.update_status("❌ No Veo profile selected for recovery")
                return False
                
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-data-dir={self.gui.profile_manager.get_profile_dir(profile_name)}")
            
            try:
                # Create new driver
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, self.config['wait_timeout'])
                
                # Navigate back to Veo
                self.update_status("🌐 Navigating back to Google Veo...")
                self.driver.get("https://labs.google.com/veo")
                time.sleep(5)
                
                # Verify we're back on the page
                if "veo" in self.driver.current_url.lower():
                    self.update_status("✅ Successfully recovered session and navigated to Veo")
                    return True
                else:
                    self.update_status("❌ Failed to navigate to Veo after recovery")
                    return False
                    
            except Exception as recovery_error:
                self.update_status(f"❌ Failed to create new session: {recovery_error}")
                return False
                    
        except Exception as e:
            self.update_status(f"❌ Session recovery failed: {e}")
            return False

    def run_basic_workflow(self, prompt_text, progress_callback=None):
        """Enhanced basic workflow với progress tracking và dynamic GUI values"""
        with self._lock:
            if self._is_running:
                self.update_status_with_log("⚠️ Workflow already running")
                return False
            self._is_running = True

        try:
            # Reset video counter for new workflow
            self.reset_video_counter()
            self.update_status_with_log("🎬 Starting enhanced Veo workflow...")

            # 🎯 GET DYNAMIC VALUES FROM GUI
            selected_model = self.gui.model_var.get()
            selected_count = int(self.gui.video_count_var.get() or "1")

            # Map GUI model selection to automation parameter
            model_type = "fast" if "Fast" in selected_model else "quality"

            self.update_status_with_log(f"📋 Using Model: {selected_model}, Count: {selected_count}")

            # Define complete workflow steps với DYNAMIC VALUES
            workflow_steps = [
                ("Find New Project Button", lambda: self.find_new_project_button()),
                ("Click New Project", lambda: self.safe_click(self.current_element, "New Project Button")),
                ("Find Project Type Dropdown", lambda: self.find_project_type_dropdown()),
                ("Click Project Type Dropdown", lambda: self.safe_click(self.current_element, "Project Type Dropdown")),
                ("Select Text to Video", lambda: self.select_project_type_option("Từ văn bản sang video")),
                ("Close Dropdown After Selection", lambda: self.close_dropdown_if_open()),
                ("Find Settings Button", lambda: self.find_settings_button()),
                ("Click Settings Button", lambda: self.safe_click(self.current_element, "Settings Button")),
                ("Find Model Dropdown", lambda: self.find_model_dropdown()),
                ("Click Model Dropdown", lambda: self.click_model_dropdown_enhanced()),
                ("Select Model", lambda: self.select_model_option(model_type)),  # 🎯 DYNAMIC
                ("Find Output Count Dropdown", lambda: self.find_output_count_dropdown()),
                ("Click Output Count Dropdown", lambda: self.safe_click(self.current_element, "Output Count Dropdown")),
                ("Select Output Count", lambda: self.select_output_count(selected_count)),  # 🎯 DYNAMIC
                ("Find Aspect Ratio Dropdown", lambda: self.find_aspect_ratio_dropdown()),
                ("Click Aspect Ratio Dropdown", lambda: self.safe_click(self.current_element, "Aspect Ratio Dropdown") if self.current_element else True),
                ("Select Aspect Ratio", lambda: self.select_aspect_ratio()),
                ("Close Settings Popup", lambda: self.close_settings_popup()),
                ("Find Prompt Input", lambda: self.find_prompt_input()),
                ("Type Prompt", lambda: self.type_prompt_enhanced(self.current_element, prompt_text)),
                ("Find Send Button", lambda: self.find_send_button()),
                ("Click Send Button", lambda: self.safe_click_send_button(self.current_element)),
                ("Wait for Video Generation", lambda: self.wait_for_video_generation()),
                ("Find Generated Videos", lambda: self.find_generated_videos_with_retry(only_new=True)),
                ("Download Videos", lambda: self._download_all_found_videos())
            ]

            # Initialize progress tracker
            if progress_callback:
                self.progress_tracker = ProgressTracker(len(workflow_steps), progress_callback)

            # Execute steps với progress tracking
            for step_name, step_func in workflow_steps:
                self.update_status_with_log(f"🔄 {step_name}...")

                try:
                    result = step_func()

                    if step_name.startswith("Find"):
                        if step_name == "Find Generated Videos":
                            # Special handling for video detection
                            if not result or len(result) == 0:
                                self.update_status_with_log(f"⚠️ {step_name} - No videos found (this may be normal)")
                                if self.progress_tracker:
                                    self.progress_tracker.update(step_name, success=False, details="No videos found")
                                # Don't return False - continue workflow
                            else:
                                self.update_status_with_log(f"✅ {step_name} - Found {len(result)} videos")
                                if self.progress_tracker:
                                    self.progress_tracker.update(step_name, success=True, details=f"Found {len(result)} videos")
                        else:
                            # Regular Find steps
                            if not result:
                                self.update_status_with_log(f"❌ {step_name} - Failed")
                                if self.progress_tracker:
                                    self.progress_tracker.update(step_name, success=False, details="Element not found")
                                return False
                            else:
                                self.current_element = result
                                self.update_status_with_log(f"✅ {step_name} - Success")
                                if self.progress_tracker:
                                    self.progress_tracker.update(step_name, success=True, details="Element found")
                    else:
                        if not result:
                            self.update_status_with_log(f"❌ {step_name} - Failed")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=False, details="Action failed")
                            return False
                        else:
                            self.update_status_with_log(f"✅ {step_name} - Success")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=True, details="Action completed")

                except Exception as e:
                    self.update_status_with_log(f"❌ {step_name} - Error: {e}")
                    if self.progress_tracker:
                        self.progress_tracker.update(step_name, success=False, details=str(e))
                    return False

            self.update_status_with_log("🎉 Complete workflow with video download finished!")
            return True

        except Exception as e:
            self.update_status(f"❌ Workflow failed: {e}")
            return False
        finally:
            with self._lock:
                self._is_running = False

    def _download_all_found_videos(self):
        """Download all videos found in the last scan"""
        if not hasattr(self, '_last_found_videos') or not self._last_found_videos:
            self.update_status("❌ No videos found to download")
            return False

        downloaded_count = 0
        for i, video in enumerate(self._last_found_videos):
            self.update_status(f"📥 Downloading video {i+1}/{len(self._last_found_videos)}...")

            # 🎯 DYNAMIC DOWNLOAD DIR: Use workflow subfolder
            workflow_download_dir = self.get_workflow_download_dir()
            result = self.download_video_with_retry(video, download_dir=workflow_download_dir)
            if result:
                downloaded_count += 1

        if downloaded_count > 0:
            self.update_status(f"✅ Successfully downloaded {downloaded_count}/{len(self._last_found_videos)} videos")
            return True
        else:
            self.update_status("❌ No videos were successfully downloaded")
            return False

    def run_quick_batch_workflow(self, prompt_text, progress_callback=None):
        """⚡ Quick workflow for batch processing (skip initial setup)"""
        with self._lock:
            if self._is_running:
                self.update_status_with_log("⚠️ Workflow already running")
                return False
            self._is_running = True

        try:
            self.update_status_with_log("⚡ Starting quick batch workflow...")

            # Quick workflow steps (skip setup, go straight to prompt input)
            quick_steps = [
                ("Clear and Type New Prompt", lambda: self.clear_and_type_prompt_enhanced(prompt_text)),
                ("Find Send Button", lambda: self.find_send_button()),
                ("Click Send Button", lambda: self.safe_click_send_button(self.current_element)),
                ("Wait for Video Generation", lambda: self.wait_for_video_generation()),
                ("Find Generated Videos", lambda: self.find_generated_videos_with_retry(only_new=True)),
                ("Download Videos", lambda: self._download_all_found_videos())
            ]

            # Initialize progress tracker
            if progress_callback:
                self.progress_tracker = ProgressTracker(len(quick_steps), progress_callback)

            # Execute quick steps
            for step_name, step_func in quick_steps:
                self.update_status_with_log(f"🔄 {step_name}...")

                try:
                    result = step_func()

                    if step_name == "Find Generated Videos":
                        # Special handling for video detection
                        if not result or len(result) == 0:
                            self.update_status_with_log(f"⚠️ {step_name} - No videos found (this may be normal)")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=False, details="No videos found")
                        else:
                            self.update_status_with_log(f"✅ {step_name} - Found {len(result)} videos")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=True, details=f"Found {len(result)} videos")
                    elif step_name.startswith("Find"):
                        if not result:
                            self.update_status_with_log(f"❌ {step_name} - Failed")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=False, details="Element not found")
                            return False
                        else:
                            self.current_element = result
                            self.update_status_with_log(f"✅ {step_name} - Success")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=True, details="Element found")
                    else:
                        if not result:
                            self.update_status_with_log(f"❌ {step_name} - Failed")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=False, details="Action failed")
                            return False
                        else:
                            self.update_status_with_log(f"✅ {step_name} - Success")
                            if self.progress_tracker:
                                self.progress_tracker.update(step_name, success=True, details="Action completed")

                except Exception as e:
                    error_msg = str(e).lower()
                    # 🎯 SESSION RECOVERY: Handle session errors during workflow
                    if any(keyword in error_msg for keyword in ['invalid session', 'session deleted', 'disconnected']):
                        self.update_status_with_log(f"⚠️ Session error in {step_name}, attempting recovery...")
                        if self.recover_session():
                            self.update_status_with_log(f"✅ Session recovered, retrying {step_name}...")
                            try:
                                # Retry the step after recovery
                                result = step_func()
                                if result:
                                    self.update_status_with_log(f"✅ {step_name} - Success after recovery")
                                    if self.progress_tracker:
                                        self.progress_tracker.update(step_name, success=True, details="Success after session recovery")
                                    continue
                            except:
                                pass
                        
                    self.update_status_with_log(f"❌ {step_name} - Error: {e}")
                    if self.progress_tracker:
                        self.progress_tracker.update(step_name, success=False, details=str(e))
                    return False

            self.update_status_with_log("🎉 Quick batch workflow completed!")
            return True

        except Exception as e:
            self.update_status_with_log(f"❌ Quick workflow failed: {e}")
            return False
        finally:
            with self._lock:
                self._is_running = False

    def clear_and_type_prompt_enhanced(self, prompt_text):
        """📋 SIMPLIFIED: Clear and paste prompt using clipboard"""
        self.update_status(f"📋 Pasting prompt: {prompt_text[:50]}...")

        # Find prompt input
        prompt_input = self.find_prompt_input()
        if not prompt_input:
            self.update_status("❌ Cannot find prompt input")
            return False

        # Use simple paste method
        return self.type_prompt_enhanced(prompt_input, prompt_text)


    def get_workflow_download_dir(self):
        """🎯 Get download directory with workflow subfolder"""
        try:
            # Get download folder from GUI
            download_folder = self.gui.download_folder.get().strip()
            if not download_folder:
                download_folder = "output"  # Fallback

            # Get workflow name for subfolder
            workflow_name = self.gui.workflow_name.get().strip()
            if not workflow_name or workflow_name == "(No workflow selected)":
                workflow_name = "default_workflow"

            # Clean workflow name for folder (remove invalid chars)
            import re
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', workflow_name)

            # Create full path: download_folder/workflow_name
            full_path = os.path.join(download_folder, clean_name)

            # Create directory if not exists
            os.makedirs(full_path, exist_ok=True)

            self.update_status(f"📁 Videos will be saved to: {full_path}")
            return full_path

        except Exception as e:
            self.update_status(f"⚠️ Error getting download dir: {e}")
            return "output"  # Fallback

    def add_downloaded_video(self, video_url):
        """Thread-safe video tracking"""
        with self._video_lock:
            self.downloaded_videos.add(video_url)
            self.current_session_videos.add(video_url)

    def is_video_downloaded(self, video_url):
        """Check if video already downloaded"""
        with self._video_lock:
            return video_url in self.downloaded_videos

    def get_session_video_count(self):
        """Get current session video count"""
        with self._video_lock:
            return len(self.current_session_videos)

    def reset_video_counter(self):
        """Reset video counter for new workflow"""
        with self._video_lock:
            self.video_counter = 0
        self.update_status_with_log("🔄 Video counter reset for new workflow")

    def find_generated_videos_with_retry(self, only_new=True, prompt_index=None):
        """Find generated videos with retry mechanism - ENHANCED for GUI"""
        self.update_status("🔍 Starting video detection with retry...")

        for attempt in range(1, self.config['video_detection_retries'] + 1):
            self.update_status(f"🔍 Video detection attempt {attempt}/{self.config['video_detection_retries']}")

            try:
                videos = self.find_generated_videos(only_new, prompt_index)

                if videos:
                    self.update_status(f"✅ Found {len(videos)} videos on attempt {attempt}")
                    self._last_found_videos = videos  # Store for download step
                    return videos
                else:
                    self.update_status(f"⚠️ No videos found on attempt {attempt}")
                    if attempt < self.config['video_detection_retries']:
                        self.update_status(f"⏳ Waiting {self.config['retry_delay']}s before retry...")
                        time.sleep(self.config['retry_delay'])

            except Exception as e:
                self.update_status(f"❌ Video detection attempt {attempt} failed: {e}")
                if attempt < self.config['video_detection_retries']:
                    time.sleep(self.config['retry_delay'])

        self.update_status("❌ Video detection failed after all retries")
        return []

    def find_generated_videos(self, only_new=True, prompt_index=None):
        """Find all generated videos on the page - ENHANCED for GUI"""
        self.update_status("🔍 Scanning for generated videos...")

        # Enhanced selectors specific to Google Veo interface
        video_selectors = [
            # Video elements with src (primary)
            "//video[@src and @src!='']",
            "//video[contains(@src, 'blob:') or contains(@src, 'http')]",

            # Google Veo specific video containers
            "//*[contains(@class, 'video')]//video[@src]",
            "//*[contains(@class, 'preview')]//video[@src]",
            "//*[contains(@class, 'player')]//video[@src]",
            "//*[contains(@class, 'result')]//video[@src]",
            "//*[contains(@class, 'generated')]//video[@src]",

            # Download buttons and links (Google Veo style)
            "//button[contains(@aria-label, 'download') or contains(@aria-label, 'Download')]",
            "//button[contains(text(), 'Tải xuống') or contains(text(), 'Download')]",
            "//a[contains(@href, '.mp4') or contains(@href, '.webm') or contains(@href, '.mov')]",
            "//a[contains(@download, '.mp4') or contains(@download, '.webm')]",

            # Video thumbnails and data attributes
            "//*[@data-video-url and @data-video-url!='']",
            "//*[@data-src and contains(@data-src, 'video')]",
            "//*[@data-video-src]",

            # Google specific video elements
            "//div[contains(@class, 'video')]//video",
            "//div[contains(@role, 'video')]//video",
            "//*[contains(@class, 'media')]//video[@src]"
        ]

        found_videos = []
        current_scan_time = time.time()

        # Enhanced video detection with multiple methods
        for selector in video_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        # Get video URL using multiple methods
                        video_url = None
                        video_type = "unknown"

                        if element.tag_name == 'video':
                            video_url = element.get_attribute('src')
                            video_type = "video_element"
                        elif element.tag_name == 'a':
                            video_url = element.get_attribute('href') or element.get_attribute('download')
                            video_type = "download_link"
                        elif element.tag_name == 'button':
                            # For download buttons, try to find associated video
                            try:
                                # Look for nearby video elements
                                nearby_videos = element.find_elements(By.XPATH, ".//video[@src] | ./preceding::video[@src][1] | ./following::video[@src][1]")
                                if nearby_videos:
                                    video_url = nearby_videos[0].get_attribute('src')
                                    video_type = "button_associated"
                            except:
                                pass
                        else:
                            # Try data attributes
                            video_url = (element.get_attribute('data-video-url') or
                                       element.get_attribute('data-src') or
                                       element.get_attribute('data-video-src'))
                            video_type = "data_attribute"

                        # Validate video URL
                        if video_url and self._is_valid_video_url(video_url):
                            # ENHANCED DEDUPLICATION - Check global tracking
                            is_duplicate = (
                                # Already in current scan
                                any(v['url'] == video_url for v in found_videos) or
                                # Already downloaded in this session (if only_new=True)
                                (only_new and video_url in self.downloaded_videos) or
                                # Already in current session videos
                                (only_new and video_url in self.current_session_videos)
                            )

                            if not is_duplicate:
                                found_videos.append({
                                    'element': element,
                                    'url': video_url,
                                    'selector': selector,
                                    'type': video_type,
                                    'tag': element.tag_name,
                                    'scan_time': current_scan_time
                                })
                                # Track this video in current session
                                with self._video_lock:
                                    self.current_session_videos.add(video_url)

            except Exception as e:
                self.update_status(f"⚠️ Error with selector {selector}: {e}")

        # Enhanced logging
        self.update_status(f"📋 Found {len(found_videos)} unique video(s)")
        for i, video in enumerate(found_videos):
            self.update_status(f"   [{i}] Type: {video['type']}, Tag: {video['tag']}")
            self.update_status(f"       URL: {video['url'][:80]}...")

        return found_videos

    def _is_valid_video_url(self, url):
        """Check if URL is a valid video URL"""
        if not url or len(url) < 10:
            return False

        # Check for valid video URL patterns
        valid_patterns = [
            'blob:', 'http://', 'https://',
            '.mp4', '.webm', '.mov', '.avi',
            'video/', 'media/'
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in valid_patterns)

    def download_video_with_retry(self, video_info, download_dir="output", prompt_index=None):
        """Download video with retry mechanism - ENHANCED for GUI"""
        video_url = video_info['url']

        # CHECK IF ALREADY DOWNLOADED
        if video_url in self.downloaded_videos:
            self.update_status(f"⏭️ Skipping duplicate video: {video_url[:60]}...")
            return None

        for attempt in range(1, self.config['download_retry_attempts'] + 1):
            self.update_status(f"📥 Download attempt {attempt}/{self.config['download_retry_attempts']}")

            try:
                result = self.download_video(video_info, download_dir, prompt_index)
                if result:
                    self.update_status(f"✅ Download successful on attempt {attempt}")
                    return result
                else:
                    self.update_status(f"⚠️ Download failed on attempt {attempt}")

            except Exception as e:
                self.update_status(f"❌ Download attempt {attempt} failed: {e}")

            if attempt < self.config['download_retry_attempts']:
                self.update_status(f"⏳ Waiting {self.config['retry_delay']}s before retry...")
                time.sleep(self.config['retry_delay'])

        self.update_status("❌ Download failed after all retries")
        return None

    def download_video(self, video_info, download_dir="output", prompt_index=None):
        """Download video to specified directory - ENHANCED for GUI"""
        video_url = video_info['url']
        video_type = video_info.get('type', 'unknown')

        # CHECK IF ALREADY DOWNLOADED
        if video_url in self.downloaded_videos:
            self.update_status(f"⏭️ Skipping duplicate video: {video_url[:60]}...")
            return None

        self.update_status(f"📥 Downloading video ({video_type}) from: {video_url[:80]}...")

        try:
            # Create download directory
            os.makedirs(download_dir, exist_ok=True)

            # Generate filename with sequential naming (1_1, 1_2, 1_3...)
            with self._video_lock:
                self.video_counter += 1
                current_number = self.video_counter
            
            video_extension = self._get_video_extension(video_url)
            filename = f"1_{current_number}{video_extension}"
            filepath = os.path.join(download_dir, filename)

            # Handle different video URL types
            success_filepath = None
            if video_url.startswith('blob:'):
                success_filepath = self._download_blob_video(video_info, filepath)
            else:
                success_filepath = self._download_http_video(video_info, filepath)

            # Track successful download
            if success_filepath:
                with self._video_lock:
                    self.downloaded_videos.add(video_url)
                self.update_status(f"✅ Downloaded and tracked: {success_filepath}")

            return success_filepath

        except Exception as e:
            self.update_status(f"❌ Download failed: {e}")
            return None

    def _get_video_extension(self, url):
        """Get appropriate video file extension"""
        url_lower = url.lower()
        if '.mp4' in url_lower:
            return '.mp4'
        elif '.webm' in url_lower:
            return '.webm'
        elif '.mov' in url_lower:
            return '.mov'
        else:
            return '.mp4'  # Default

    def _download_blob_video(self, video_info, filepath):
        """Download blob: video using browser automation - SIMPLIFIED for GUI"""
        self.update_status("🔄 Downloading blob video using browser automation...")

        try:
            # For GUI, we'll use a simpler approach - try to trigger download via button
            return self._try_download_via_button(video_info, filepath)
        except Exception as e:
            self.update_status(f"❌ Blob download failed: {e}")
            return None

    def _download_http_video(self, video_info, filepath):
        """Download HTTP video using requests - MEMORY SAFE"""
        video_url = video_info['url']
        self.update_status("🔄 Starting HTTP download...")

        try:
            import requests
            import gc

            # Enhanced headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'Accept-Encoding': 'identity;q=1, *;q=0',
                'Accept-Language': 'en-US,en;q=0.9',
                'Range': 'bytes=0-'
            }

            response = None
            try:
                response = requests.get(video_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 4096  # Smaller chunk size for better memory management

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Force flush to disk periodically
                            if downloaded % (chunk_size * 100) == 0:
                                f.flush()
                                os.fsync(f.fileno())  # Force write to disk
                                gc.collect()  # Force garbage collection
                                self._check_memory_usage()  # Monitor memory

                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                if downloaded % (chunk_size * 50) == 0:  # Less frequent updates
                                    self.update_status(f"📥 Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

                self.update_status(f"✅ HTTP video downloaded successfully!")
                self.update_status(f"📁 File: {filepath}")
                self.update_status(f"📊 Size: {downloaded} bytes")

                return filepath

            finally:
                # Ensure response is properly closed
                if response:
                    response.close()
                # Force garbage collection
                gc.collect()

        except Exception as e:
            self.update_status(f"❌ HTTP download failed: {e}")
            # Force cleanup before fallback
            import gc
            gc.collect()
            # Fallback: try to trigger download via button click
            return self._try_download_via_button(video_info, filepath)

    def _try_download_via_button(self, video_info, filepath):
        """Try to download by clicking download button"""
        self.update_status("🔄 Trying download via button click...")

        try:
            # Look for download buttons
            download_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Tải xuống') or contains(text(), 'Download') or contains(@aria-label, 'download')]")

            for btn in download_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    self.update_status(f"🖱️ Clicking download button: {btn.text[:30]}...")
                    btn.click()
                    time.sleep(3)  # Wait for download to start

                    # Check if download started (this is browser-dependent)
                    self.update_status("✅ Download button clicked - check your Downloads folder")
                    return "download_triggered"

            self.update_status("❌ No download buttons found")
            return None

        except Exception as e:
            self.update_status(f"❌ Button download failed: {e}")
            return None

    def find_project_type_dropdown(self):
        """Tìm dropdown chọn loại dự án"""
        self.update_status("🔍 Finding Project Type dropdown...")

        selectors = [
            "//button[contains(text(), 'Từ văn bản sang video')]",
            "//button[contains(text(), 'Text to Video')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'văn bản')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'video')]",
            "//button[contains(text(), 'video') and contains(., 'arrow_drop_down')]",
            "//button[contains(@class, 'dropdown') and contains(text(), 'video')]"
        ]

        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    self.update_status(f"✅ Found Project Type dropdown")
                    return element
            except:
                continue

        self.update_status("❌ Project Type dropdown not found")
        return None

    def select_project_type_option(self, target_option="Từ văn bản sang video"):
        """Chọn option trong Project Type dropdown"""
        self.update_status(f"🎯 Selecting project type: {target_option}")

        # Wait for dropdown options
        time.sleep(2)

        option_selectors = [
            f"//div[normalize-space(text())='{target_option}']",
            f"//button[normalize-space(text())='{target_option}']",
            f"//li[normalize-space(text())='{target_option}']",
            f"//*[contains(text(), '{target_option}')]",
            f"//*[contains(text(), 'Từ văn bản sang video')]",
            f"//*[contains(text(), 'Text to Video')]",
            f"//*[@role='option'][contains(text(), 'văn bản')]",
            f"//*[@role='menuitem'][contains(text(), 'văn bản')]"
        ]

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        if self.safe_click(element, f"Project Type Option: {target_option}"):
                            time.sleep(2)
                            return True
            except Exception as e:
                continue

        # Fallback to keyboard navigation
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_DOWN)
            time.sleep(1)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            self.update_status("✅ Keyboard navigation successful")
            return True
        except Exception as e:
            self.update_status(f"❌ All methods failed for project type: {target_option}")
            return False

    def close_dropdown_if_open(self):
        """Đóng dropdown nếu đang mở"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(1)
            self.update_status("🔄 Closed any open dropdowns")
            return True
        except:
            return True

    def find_settings_button(self):
        """Tìm nút Settings để mở popup chứa model dropdown"""
        self.update_status("🔍 Finding Settings button...")

        selectors = [
            "//button[contains(., 'tune')]",
            "//button[contains(text(), 'Cài đặt')]",
            "//button[contains(text(), 'Settings')]",
            "//button[contains(., 'settings')]",
            "//button[contains(@aria-label, 'Settings')]",
            "//button[contains(@aria-label, 'settings')]",
            "//button[contains(@title, 'Settings')]",
            "//button[contains(., '⚙')]",
            "//header//button[last()]",
            "//nav//button[last()]"
        ]

        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    self.update_status(f"✅ Found Settings button")
                    return element
            except:
                continue

        self.update_status("❌ Settings button not found")
        return None

    def find_model_dropdown(self):
        """Tìm dropdown model trong settings popup - ENHANCED"""
        self.update_status("🔍 Finding Model dropdown in settings popup...")

        # ENHANCED: Longer wait for popup to fully load
        self.update_status("⏳ Waiting for popup to fully load...")
        time.sleep(4)

        selectors = [
            # Based on screenshot - "Mô hình" label with Veo 3 dropdown
            "//div[contains(text(), 'Mô hình')]/following-sibling::*//button",
            "//div[contains(text(), 'Mô hình')]/..//button[contains(text(), 'Veo')]",
            "//button[contains(text(), 'Veo 3 - Quality')]",
            "//button[contains(text(), 'Veo 3 - Fast')]",
            "//button[contains(text(), 'Mô hình') and contains(text(), 'Veo')]",

            # ENHANCED: More generic patterns
            "//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Veo')]",
            "//button[contains(text(), 'Quality')]",
            "//button[contains(text(), 'Fast')]",

            # Generic model dropdown patterns in popup
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Veo')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Veo')]",
            "//div[contains(@class, 'dialog')]//button[contains(text(), 'Veo')]",

            # Fallback: any button with Veo in popup context
            "//*[contains(@class, 'popup')]//*[contains(text(), 'Veo')]/ancestor-or-self::button",
            "//*[contains(@class, 'modal')]//*[contains(text(), 'Veo')]/ancestor-or-self::button"
        ]

        # ENHANCED: Debug all visible buttons in current state
        self.update_status("🔍 DEBUG: Scanning all visible buttons after settings click...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            relevant_buttons = []

            for i, btn in enumerate(all_buttons):
                if btn.is_displayed() and btn.text:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in ['veo', 'quality', 'fast', 'mô hình', 'model']):
                        relevant_buttons.append({
                            'index': i,
                            'text': btn.text,
                            'element': btn
                        })

            self.update_status(f"📋 Found {len(relevant_buttons)} relevant buttons:")
            for btn_info in relevant_buttons[:10]:  # Show first 10
                self.update_status(f"   [{btn_info['index']}] '{btn_info['text']}'")

            # Try clicking the most promising one
            if relevant_buttons:
                # Prioritize button with "Mô hình" and dropdown indicator
                for btn_info in relevant_buttons:
                    text_lower = btn_info['text'].lower()
                    if 'mô hình' in text_lower and any(indicator in btn_info['text'] for indicator in ['arrow_drop_down', '▼', 'dropdown']):
                        self.update_status(f"✅ Using dropdown button with 'Mô hình': '{btn_info['text'][:50]}...'")
                        return btn_info['element']

                # Fallback to first relevant button
                best_btn = relevant_buttons[0]
                self.update_status(f"✅ Using fallback button: '{best_btn['text'][:50]}...'")
                return best_btn['element']

        except Exception as e:
            self.update_status(f"   Debug scan failed: {e}")

        # Original selector approach
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    self.update_status(f"✅ Found Model dropdown in popup: {element.text[:50]}...")
                    return element
            except:
                continue

        self.update_status("❌ Model dropdown not found in popup")
        return None

    def click_model_dropdown_enhanced(self):
        """Enhanced model dropdown clicking với forced opening"""
        if not self.current_element:
            self.update_status("❌ No model dropdown element found")
            return False

        self.update_status("🔧 Enhanced model dropdown click...")

        # Initial click
        success = self.safe_click(self.current_element, "Model Dropdown")
        if not success:
            return False

        # Multiple click attempts to force dropdown open
        try:
            for click_type in ["regular", "javascript", "actions"]:
                try:
                    if click_type == "regular":
                        self.current_element.click()
                    elif click_type == "javascript":
                        self.driver.execute_script("arguments[0].click();", self.current_element)
                    elif click_type == "actions":
                        ActionChains(self.driver).click(self.current_element).perform()
                    time.sleep(1)
                except:
                    continue
        except:
            pass

        return True

    def select_model_option(self, model_type="fast"):
        """Chọn model (fast/quality) với enhanced logic cho tất cả Veo models"""
        # 🎯 ENHANCED MODEL MAPPING từ GUI selection
        selected_model = self.gui.model_var.get()

        if selected_model == "Veo 3 Quality":
            target_text = "Veo 3 - Quality"
        elif selected_model == "Veo 3 Fast":
            target_text = "Veo 3 - Fast"
        elif selected_model == "Veo 2 Quality":
            target_text = "Veo 2 - Quality"
        elif selected_model == "Veo 2 Fast":
            target_text = "Veo 2 - Fast"
        else:
            # Fallback to parameter-based selection for backward compatibility
            target_text = "Veo 3 - Fast" if model_type.lower() == "fast" else "Veo 3 - Quality"

        self.update_status(f"🎯 Selecting model: {target_text} (from GUI: {selected_model})")

        # Wait for options to load
        time.sleep(3)

        option_selectors = [
            f"//div[normalize-space(text())='{target_text}']",
            f"//span[normalize-space(text())='{target_text}']",
            f"//label[normalize-space(text())='{target_text}']",
            f"//*[contains(text(), '{target_text}')]",
            f"//*[@role='option'][contains(text(), '{model_type}')]",
            f"//*[@role='menuitem'][contains(text(), '{model_type}')]"
        ]

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        if self.safe_click(element, f"Model Option: {target_text}"):
                            return True
            except:
                continue

        # Keyboard fallback
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            self.update_status("✅ Keyboard navigation successful")
            return True
        except:
            self.update_status(f"❌ All methods failed for model: {target_text}")
            return False

    def find_output_count_dropdown(self):
        """Tìm dropdown chọn số lượng video trong settings popup - ENHANCED"""
        self.update_status("🔍 Finding Output Count dropdown in settings popup...")

        selectors = [
            # Based on screenshot - "Câu trả lời đầu ra cho mỗi câu lệnh" dropdown
            "//button[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]",
            "//button[contains(text(), 'Câu trả lời đầu ra')]",
            "//button[contains(text(), 'câu lệnh') and contains(., 'arrow_drop_down')]",

            # ENHANCED: More generic patterns
            "//button[contains(text(), 'Câu trả lời')]",
            "//button[contains(text(), 'đầu ra')]",

            # In popup context
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Câu trả lời')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Câu trả lời')]",
            "//div[contains(@class, 'dialog')]//button[contains(text(), 'Câu trả lời')]",

            # Number-based patterns in popup
            "//*[contains(@class, 'popup')]//*[contains(text(), 'đầu ra')]/ancestor-or-self::button",
            "//*[contains(@class, 'modal')]//*[contains(text(), 'đầu ra')]/ancestor-or-self::button"
        ]

        # ENHANCED: Debug scan for output count buttons
        self.update_status("🔍 DEBUG: Scanning for output count buttons...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            relevant_buttons = []

            for i, btn in enumerate(all_buttons):
                if btn.is_displayed() and btn.text:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in ['câu trả lời', 'đầu ra', 'output', 'response']):
                        relevant_buttons.append({
                            'index': i,
                            'text': btn.text,
                            'element': btn
                        })

            self.update_status(f"📋 Found {len(relevant_buttons)} output-related buttons:")
            for btn_info in relevant_buttons[:5]:  # Show first 5
                self.update_status(f"   [{btn_info['index']}] '{btn_info['text']}'")

            # Try the most promising one
            if relevant_buttons:
                best_btn = relevant_buttons[0]
                self.update_status(f"✅ Using most promising output button: '{best_btn['text']}'")
                return best_btn['element']

        except Exception as e:
            self.update_status(f"   Debug scan failed: {e}")

        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    self.update_status(f"✅ Found Output Count dropdown in popup: {element.text[:50]}...")
                    return element
            except:
                continue

        self.update_status("❌ Output Count dropdown not found in popup")
        return None

    def find_aspect_ratio_dropdown(self):
        """Tìm dropdown tỷ lệ khung hình trong settings popup"""
        self.update_status("🔍 Finding Aspect Ratio dropdown in settings popup...")
        
        # Debug scan for aspect ratio buttons FIRST
        self.update_status("🔍 DEBUG: Scanning for aspect ratio buttons...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            relevant_buttons = []

            for i, btn in enumerate(all_buttons):
                if btn.is_displayed() and btn.text:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in ['tỷ lệ', 'khung hình', 'khổ ngang', 'khổ dọc', '16:9', '9:16', 'ratio', 'crop']):
                        relevant_buttons.append({
                            'index': i,
                            'text': btn.text,
                            'element': btn
                        })

            self.update_status(f"📋 Found {len(relevant_buttons)} aspect ratio-related buttons:")
            for btn_info in relevant_buttons[:3]:  # Show top 3
                self.update_status(f"   [{btn_info['index']}] '{btn_info['text']}'")
                
            # Try clicking the first relevant button directly
            if relevant_buttons:
                target_btn = relevant_buttons[0]['element']
                self.update_status(f"✅ Using first matching button: {relevant_buttons[0]['text'][:30]}...")
                return target_btn

        except Exception as e:
            self.update_status(f"❌ Debug scan failed: {e}")

        # Fallback to selectors
        selectors = [
            # Based on actual text found in debug
            "//button[contains(text(), 'Tỷ lệ khung hình') and contains(text(), 'Khổ ngang')]",
            "//button[contains(text(), 'Tỷ lệ khung hình') and contains(text(), 'arrow_drop_down')]",
            "//button[contains(., 'crop_landscape')]",
            "//*[contains(text(), 'Tỷ lệ khung hình')]/ancestor-or-self::button",
            "//*[contains(text(), 'crop_landscape')]/ancestor-or-self::button",
            "//button[contains(text(), 'Tỷ lệ')]",
            "//button[contains(text(), 'khung hình')]"
        ]

        # Try selectors with WebDriverWait
        for i, selector in enumerate(selectors):
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    self.update_status(f"✅ Found Aspect Ratio dropdown with selector {i+1}")
                    return element
            except:
                continue

        self.update_status("⚠️ Aspect Ratio dropdown not found - skipping (optional)")
        return None

    def select_output_count(self, count=1):
        """Chọn số lượng video output với enhanced logic từ GUI"""
        # 🎯 GET DYNAMIC VALUE FROM GUI
        selected_count = self.gui.video_count_var.get()

        try:
            count = int(selected_count) if selected_count else count
        except (ValueError, TypeError):
            count = 1  # Fallback to default

        # Validate count range
        if count < 1 or count > 4:
            count = 1
            self.update_status(f"⚠️ Invalid count, using default: {count}")

        self.update_status(f"🎯 Selecting output count: {count} (from GUI: {selected_count})")

        # Wait for dropdown options
        time.sleep(3)

        option_selectors = [
            f"//div[normalize-space(text())='{count}']",
            f"//button[normalize-space(text())='{count}']",
            f"//li[normalize-space(text())='{count}']",
            f"//span[normalize-space(text())='{count}']",
            f"//*[contains(text(), '{count}') and not(contains(text(), '10'))]",
            f"//*[@role='option'][normalize-space(text())='{count}']"
        ]

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        if element_text == str(count):
                            if self.safe_click(element, f"Output Count: {count}"):
                                # 🎯 VERIFY SELECTION: Wait and confirm dropdown closed
                                time.sleep(2)
                                self.update_status(f"✅ Clicked output count {count}, verifying selection...")
                                
                                # Check if dropdown actually closed and value changed
                                try:
                                    # Look for the updated dropdown button text
                                    updated_buttons = self.driver.find_elements(By.XPATH, 
                                        "//button[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]")
                                    for btn in updated_buttons:
                                        if btn.is_displayed() and str(count) in btn.text:
                                            self.update_status(f"✅ Output count {count} selection verified!")
                                            return True
                                    
                                    self.update_status(f"⚠️ Output count {count} clicked but not confirmed, continuing...")
                                    return True
                                except:
                                    return True
            except:
                continue

        # 🎯 ENHANCED: JavaScript method for direct option selection
        try:
            script = f"""
            // Look for dropdown options containing the target number
            var options = document.querySelectorAll('[role="option"], .option, li, button, span, div');
            for (var i = 0; i < options.length; i++) {{
                var option = options[i];
                var text = option.textContent.trim();
                if (text === '{count}' && option.offsetParent !== null) {{
                    option.click();
                    return true;
                }}
            }}
            
            // If exact match fails, try partial match
            for (var i = 0; i < options.length; i++) {{
                var option = options[i];
                var text = option.textContent.trim();
                if (text.includes('{count}') && option.offsetParent !== null && text.length < 5) {{
                    option.click();
                    return true;
                }}
            }}
            return false;
            """
            
            result = self.driver.execute_script(script)
            if result:
                time.sleep(2)
                self.update_status(f"✅ Output count {count} selected via JavaScript method")
                return True
                
        except Exception as e:
            self.update_status(f"⚠️ JavaScript method failed: {e}")

        # Keyboard fallback (enhanced)
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Reset to first option by going up
            for _ in range(5):
                body.send_keys(Keys.ARROW_UP)
                time.sleep(0.2)
            
            # Navigate down to target count  
            for i in range(count):
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.4)  # Increased delay
                
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            self.update_status(f"✅ Keyboard navigation for count {count} successful")
            return True
        except:
            self.update_status(f"❌ All methods failed for output count: {count}")
            return False

    def select_aspect_ratio(self, ratio=None):
        """Chọn tỷ lệ khung hình với enhanced logic từ GUI"""
        # 🎯 GET DYNAMIC VALUE FROM GUI
        selected_ratio = self.gui.aspect_ratio_var.get()
        
        # Parse ratio from GUI selection
        if "16:9" in selected_ratio:
            ratio = "16:9"
            target_text = ["khổ ngang", "16:9", "landscape", "crop_landscape"]
        elif "9:16" in selected_ratio:
            ratio = "9:16" 
            target_text = ["khổ dọc", "9:16", "portrait", "crop_portrait"]
        else:
            ratio = "16:9"  # Default fallback
            target_text = ["khổ ngang", "16:9", "landscape", "crop_landscape"]
            
        self.update_status(f"🎯 Selecting aspect ratio: {ratio} (from GUI: {selected_ratio})")

        # Wait for dropdown options to appear
        time.sleep(2)

        # Try multiple selector patterns for aspect ratio options
        option_selectors = []
        for text in target_text:
            option_selectors.extend([
                f"//div[contains(text(), '{text}')]",
                f"//button[contains(text(), '{text}')]", 
                f"//li[contains(text(), '{text}')]",
                f"//span[contains(text(), '{text}')]",
                f"//*[contains(@class, 'option')][contains(text(), '{text}')]",
                f"//*[@role='option'][contains(text(), '{text}')]"
            ])

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        if self.safe_click(element, f"Aspect Ratio: {ratio}"):
                            # 🎯 VERIFY ASPECT RATIO SELECTION
                            time.sleep(2)
                            self.update_status(f"✅ Clicked aspect ratio {ratio}, verifying selection...")
                            
                            # Check if aspect ratio actually updated
                            try:
                                updated_buttons = self.driver.find_elements(By.XPATH, 
                                    "//button[contains(text(), 'Tỷ lệ khung hình')]")
                                for btn in updated_buttons:
                                    if btn.is_displayed():
                                        expected_text = "Khổ ngang" if ratio == "16:9" else "Khổ dọc"
                                        if expected_text in btn.text or ratio in btn.text:
                                            self.update_status(f"✅ Aspect ratio {ratio} selection verified!")
                                            return True
                                
                                self.update_status(f"⚠️ Aspect ratio {ratio} clicked but not confirmed, continuing...")
                                return True
                            except:
                                return True
            except:
                continue

        # 🎯 ENHANCED: JavaScript method for aspect ratio selection
        try:
            # Enhanced keyword matching for different languages
            if ratio == "16:9":
                keywords = ["16:9", "khổ ngang", "landscape", "crop_landscape", "ngang"]
            elif ratio == "9:16":
                keywords = ["9:16", "khổ dọc", "portrait", "crop_portrait", "dọc"]
            else:
                keywords = ["16:9", "khổ ngang", "landscape", "crop_landscape", "ngang"]
                
            script = f"""
            var keywords = {keywords};
            var options = document.querySelectorAll('[role="option"], .option, li, button, span, div');
            
            for (var k = 0; k < keywords.length; k++) {{
                for (var i = 0; i < options.length; i++) {{
                    var option = options[i];
                    var text = option.textContent.toLowerCase();
                    if (text.includes(keywords[k].toLowerCase()) && 
                        option.offsetParent !== null &&
                        option.getBoundingClientRect().height > 0) {{
                        option.click();
                        return true;
                    }}
                }}
            }}
            return false;
            """
            
            result = self.driver.execute_script(script)
            if result:
                time.sleep(2)
                self.update_status(f"✅ Aspect ratio {ratio} selected via JavaScript method")
                return True
                
        except Exception as e:
            self.update_status(f"⚠️ JavaScript aspect ratio method failed: {e}")

        # Keyboard fallback for aspect ratio (enhanced)
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Reset to first option
            for _ in range(3):
                body.send_keys(Keys.ARROW_UP)
                time.sleep(0.3)
            
            if ratio == "9:16":  # Portrait usually second option
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                body.send_keys(Keys.ENTER)
            else:  # 16:9 usually first option  
                body.send_keys(Keys.ENTER)
            
            time.sleep(2)
            self.update_status(f"✅ Selected aspect ratio via keyboard: {ratio}")
            return True
        except Exception as e:
            self.update_status(f"⚠️ Aspect ratio selection failed, continuing: {e}")
            return True  # Don't break workflow

    def _debug_dropdown_state(self, dropdown_type):
        """🔍 DEBUG: Analyze dropdown state for troubleshooting"""
        try:
            self.update_status(f"🔍 DEBUG: Analyzing {dropdown_type} dropdown state...")
            
            # Check for any open dropdowns/menus
            dropdowns = self.driver.find_elements(By.XPATH, 
                "//*[@role='listbox' or @role='menu' or contains(@class, 'dropdown') or contains(@class, 'menu')]")
            
            self.update_status(f"🔍 Found {len(dropdowns)} potential dropdown containers")
            
            for i, dropdown in enumerate(dropdowns):
                if dropdown.is_displayed():
                    self.update_status(f"🔍 Dropdown {i+1}: Visible, size: {dropdown.size}")
                    
                    # Check options inside this dropdown
                    options = dropdown.find_elements(By.XPATH, ".//*[@role='option' or contains(@class, 'option')]")
                    self.update_status(f"🔍 Dropdown {i+1} has {len(options)} options")
                    
                    for j, option in enumerate(options[:5]):  # Show first 5 options
                        if option.is_displayed():
                            self.update_status(f"🔍 Option {j+1}: '{option.text[:30]}...'")
                            
        except Exception as e:
            self.update_status(f"🔍 Debug analysis failed: {e}")

    def close_settings_popup(self):
        """🎯 TRIỆT ĐỂ V2: Ultimate settings popup closure system"""
        self.update_status("🔧 ULTIMATE SETTINGS POPUP CLOSURE - Starting...")
        
        max_attempts = 5
        for attempt in range(max_attempts):
            self.update_status(f"🔄 Closure attempt {attempt + 1}/{max_attempts}")
            
            # Check if settings are still visible
            settings_visible = self._check_settings_visibility()
            if not settings_visible:
                self.update_status("✅ Settings popup successfully closed!")
                return True  # Successfully closed early
                
            self.update_status(f"⚠️ Settings still visible on attempt {attempt + 1}, trying closure methods...")
            
            # Apply closure methods in sequence
            if attempt == 0:
                self._method_keyboard_close()
            elif attempt == 1:
                self._method_button_close()
            elif attempt == 2:
                self._method_outside_click()
            elif attempt == 3:
                self._method_force_hide()
            else:
                self._method_nuclear_option()
                
            time.sleep(2)  # Wait for UI to settle
            
        # Final verification
        final_check = self._check_settings_visibility()
        if final_check:
            self.update_status("❌ SETTINGS POPUP STILL PERSISTS - MAXIMUM NUCLEAR FORCE")
            self._method_nuclear_option()
            self.update_status("⚠️ Applied nuclear option - continuing workflow")
            return True  # Continue anyway after nuclear option
        else:
            self.update_status("✅ Settings popup CONFIRMED CLOSED")
            return True  # Successfully closed

    def _check_settings_visibility(self):
        """Check if any settings elements are visible"""
        try:
            settings_selectors = [
                "//button[contains(text(), 'Veo 3 - Fast')]",
                "//button[contains(text(), 'Khổ ngang')]", 
                "//button[contains(text(), 'Tỷ lệ khung hình')]",
                "//button[contains(text(), 'Câu trả lời đầu ra')]",
                "//button[contains(text(), 'Mô hình')]",
                "//*[contains(text(), 'arrow_drop_down')]"
            ]
            
            for selector in settings_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if any(elem.is_displayed() for elem in elements):
                    return True
            return False
        except:
            return True  # Assume visible if can't check

    def _method_keyboard_close(self):
        """Method 1: Enhanced keyboard closure"""
        self.update_status("🔧 Method 1: Enhanced keyboard closure...")
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Multiple ESC attempts with different targets
            for i in range(5):
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                
            # Try other keys that might close popups
            body.send_keys(Keys.TAB)
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
            
            # Try clicking body and then ESC
            body.click()
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
            
        except Exception as e:
            self.update_status(f"⚠️ Keyboard method failed: {e}")

    def _method_button_close(self):
        """Method 2: Enhanced close button detection and clicking"""
        self.update_status("🔧 Method 2: Enhanced close button detection...")
        try:
            close_selectors = [
                "//button[contains(@aria-label, 'close') or contains(@aria-label, 'Close')]",
                "//button[contains(@title, 'close') or contains(@title, 'Close')]",
                "//button[contains(text(), '×')]",
                "//button[contains(text(), 'Đóng')]",
                "//button[contains(text(), 'close')]",
                "//*[contains(@class, 'close')]//button",
                "//button[contains(@class, 'close')]",
                "//*[@role='button'][contains(@aria-label, 'close')]",
                "//div[contains(@class, 'close-button')]",
                "//i[contains(@class, 'close')]//parent::button",
                "//span[contains(@class, 'close')]//parent::button"
            ]
            
            for selector in close_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            self.update_status(f"🔧 Clicking close button: {selector}")
                            # Try multiple click methods
                            try:
                                btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            self.update_status(f"⚠️ Button close method failed: {e}")

    def _method_outside_click(self):
        """Method 3: Click outside popup to close"""
        self.update_status("🔧 Method 3: Outside click and overlay removal...")
        try:
            # Click multiple areas outside popup
            click_points = [
                (50, 50),    # Top left
                (100, 100),  # Top left area
                (50, 500),   # Left middle
                (200, 50),   # Top area
            ]
            
            for x, y in click_points:
                self.driver.execute_script(f"""
                    var event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {x},
                        clientY: {y}
                    }});
                    document.elementFromPoint({x}, {y}).dispatchEvent(event);
                """)
                time.sleep(0.5)
                
            # Remove backdrop/overlay elements
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('[class*="backdrop"], [class*="overlay"], [class*="mask"]');
                overlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                    overlay.remove();
                });
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Outside click method failed: {e}")

    def _method_force_hide(self):
        """Method 4: Force hide settings elements"""
        self.update_status("🔧 Method 4: Force hiding settings elements...")
        try:
            self.driver.execute_script("""
                // Find and hide settings-related elements
                var settingsKeywords = [
                    'Veo 3 - Fast', 'Khổ ngang', 'Tỷ lệ khung hình', 
                    'Câu trả lời đầu ra', 'Mô hình', 'arrow_drop_down'
                ];
                
                settingsKeywords.forEach(function(keyword) {
                    var elements = document.evaluate(
                        "//*[contains(text(), '" + keyword + "')]",
                        document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null
                    );
                    
                    for (var i = 0; i < elements.snapshotLength; i++) {
                        var element = elements.snapshotItem(i);
                        
                        // Hide the element and its containers
                        var container = element.closest('div, section, aside, nav, form');
                        if (container) {
                            container.style.display = 'none';
                            container.style.visibility = 'hidden';
                            container.style.opacity = '0';
                            container.style.height = '0';
                            container.style.overflow = 'hidden';
                        }
                        
                        element.style.display = 'none';
                        element.style.visibility = 'hidden';
                    }
                });
                
                return true;
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Force hide method failed: {e}")

    def _method_nuclear_option(self):
        """Method 5: Nuclear option - remove everything settings-related"""
        self.update_status("🔧 Method 5: NUCLEAR OPTION - Removing all settings...")
        try:
            self.driver.execute_script("""
                // NUCLEAR OPTION: Remove all possible settings elements
                
                // 1. Remove by text content
                var allElements = document.getElementsByTagName('*');
                for (var i = allElements.length - 1; i >= 0; i--) {
                    var elem = allElements[i];
                    var text = elem.textContent || elem.innerText || '';
                    
                    if (text.includes('Veo 3') || text.includes('Khổ ngang') || 
                        text.includes('Tỷ lệ khung hình') || text.includes('Câu trả lời đầu ra') ||
                        text.includes('Mô hình') || text.includes('arrow_drop_down')) {
                        
                        // Try to find and remove the container
                        var container = elem.closest('div, section, aside, nav, form, dialog');
                        if (container && container !== document.body) {
                            container.remove();
                        } else {
                            elem.remove();
                        }
                    }
                }
                
                // 2. Remove common popup patterns
                var popupSelectors = [
                    '[role="dialog"]', '[aria-modal="true"]',
                    '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
                    '[class*="dropdown"]', '[class*="menu"]', '[class*="panel"]'
                ];
                
                popupSelectors.forEach(function(selector) {
                    var elements = document.querySelectorAll(selector);
                    elements.forEach(function(elem) {
                        if (elem.offsetParent !== null) { // Only if visible
                            elem.remove();
                        }
                    });
                });
                
                // 3. Hide anything with high z-index (likely overlays)
                var allDivs = document.querySelectorAll('div, section, aside');
                allDivs.forEach(function(div) {
                    var style = window.getComputedStyle(div);
                    var zIndex = parseInt(style.zIndex);
                    if (zIndex > 100) {
                        div.remove();
                    }
                });
                
                return true;
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Nuclear option failed: {e}")
        
        # 🎯 METHOD 1: Multiple ESC key attempts
        try:
            self.update_status("🔧 Method 1: Multiple ESC attempts...")
            body = self.driver.find_element(By.TAG_NAME, "body")
            for i in range(3):  # Try ESC multiple times
                body.send_keys(Keys.ESCAPE)
                time.sleep(1)
                
                # Check if popup actually closed
                try:
                    remaining_popups = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'popup') or contains(@class, 'modal')]")
                    visible_popups = [p for p in remaining_popups if p.is_displayed()]
                    if not visible_popups:
                        self.update_status(f"✅ Settings popup closed after ESC attempt {i+1}")
                        break
                except:
                    pass
        except Exception as e:
            self.update_status(f"⚠️ ESC method failed: {e}")

        # 🎯 METHOD 2: Enhanced close button detection
        close_button_selectors = [
            "//button[contains(@aria-label, 'close') or contains(@title, 'close')]",
            "//button[contains(text(), '×') or contains(text(), 'Close')]", 
            "//button[contains(text(), 'Đóng') or contains(text(), 'close')]",
            "//*[@role='button'][contains(@aria-label, 'close')]",
            "//div[contains(@class, 'close')]//button",
            "//button[contains(@class, 'close')]"
        ]
        
        for selector in close_button_selectors:
            try:
                close_buttons = self.driver.find_elements(By.XPATH, selector)
                for btn in close_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        self.update_status(f"🔧 Trying close button: {btn.get_attribute('class')}")
                        btn.click()
                        time.sleep(2)
                        
                        # Verify popup actually closed
                        try:
                            remaining_popups = self.driver.find_elements(By.XPATH, 
                                "//div[contains(@class, 'popup') or contains(@class, 'modal')]")
                            visible_popups = [p for p in remaining_popups if p.is_displayed()]
                            if not visible_popups:
                                self.update_status("✅ Settings popup closed via close button")
                                break
                        except:
                            pass
            except:
                continue

        # 🎯 METHOD 3: Click outside popup to close
        try:
            self.update_status("🔧 Method 3: Click outside popup...")
            # Click on a safe area outside popup
            self.driver.execute_script("""
                // Click on document body outside any popup
                var event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: 50,
                    clientY: 50
                });
                document.body.dispatchEvent(event);
            """)
            time.sleep(2)
        except Exception as e:
            self.update_status(f"⚠️ Click outside method failed: {e}")

        # 🎯 TRIỆT ĐỂ VERIFICATION: Check actual settings elements
        try:
            # Check for specific settings elements again
            settings_still_visible = False
            settings_check_selectors = [
                "//button[contains(text(), 'Veo 3 - Fast')]",
                "//button[contains(text(), 'Khổ ngang')]", 
                "//button[contains(text(), 'Tỷ lệ khung hình')]",
                "//button[contains(text(), 'Câu trả lời đầu ra')]"
            ]
            
            for selector in settings_check_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [e for e in elements if e.is_displayed()]
                if visible_elements:
                    settings_still_visible = True
                    self.update_status(f"⚠️ Settings element still visible: {selector}")
            
            if settings_still_visible:
                self.update_status("❌ SETTINGS POPUP STILL OPEN - FORCING AGGRESSIVE CLOSE...")
                
                # 🎯 AGGRESSIVE METHOD: Force hide all settings-related elements
                self.driver.execute_script("""
                    // Force close settings popup - multiple approaches
                    
                    // Method 1: Hide elements by text content
                    var settingsTexts = ['Veo 3 - Fast', 'Khổ ngang', 'Tỷ lệ khung hình', 'Câu trả lời đầu ra', 'Mô hình'];
                    settingsTexts.forEach(function(text) {
                        var elements = document.evaluate(
                            "//*[contains(text(), '" + text + "')]", 
                            document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null
                        );
                        for (var i = 0; i < elements.snapshotLength; i++) {
                            var elem = elements.snapshotItem(i);
                            var container = elem.closest('div, section, aside, nav');
                            if (container) {
                                container.style.display = 'none';
                                container.remove();
                            }
                        }
                    });
                    
                    // Method 2: Remove by common popup/modal patterns
                    var popupSelectors = [
                        '[class*="popup"]', '[class*="modal"]', '[class*="dialog"]',
                        '[class*="overlay"]', '[class*="settings"]', '[id*="popup"]',
                        '[id*="modal"]', '[role="dialog"]', '[aria-modal="true"]'
                    ];
                    
                    popupSelectors.forEach(function(selector) {
                        var elements = document.querySelectorAll(selector);
                        elements.forEach(function(elem) {
                            if (elem.offsetHeight > 0 || elem.offsetWidth > 0) {
                                elem.style.display = 'none';
                                elem.remove();
                            }
                        });
                    });
                    
                    // Method 3: Click any close buttons
                    var closeButtons = document.querySelectorAll('button, [role="button"]');
                    closeButtons.forEach(function(btn) {
                        var text = btn.textContent || btn.getAttribute('aria-label') || '';
                        if (text.includes('close') || text.includes('×') || text.includes('đóng')) {
                            btn.click();
                        }
                    });
                    
                    return true;
                """)
                
                time.sleep(3)
                
                # Final check after aggressive closure
                final_settings_check = False
                for selector in settings_check_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if any(e.is_displayed() for e in elements):
                        final_settings_check = True
                        break
                
                if final_settings_check:
                    self.update_status("❌ SETTINGS POPUP STILL PERSISTS - MAXIMUM FORCE")
                    # Last resort: hide everything that might be a settings panel
                    self.driver.execute_script("""
                        var allElements = document.querySelectorAll('*');
                        for (var i = 0; i < allElements.length; i++) {
                            var elem = allElements[i];
                            var text = elem.textContent || '';
                            if (text.includes('Veo 3') || text.includes('Khổ ngang') || 
                                text.includes('Tỷ lệ khung hình') || text.includes('Câu trả lời đầu ra')) {
                                var container = elem.closest('div, section, aside');
                                if (container && container.style.position !== 'static') {
                                    container.style.display = 'none';
                                }
                            }
                        }
                    """)
                    self.update_status("⚠️ Applied maximum force closure - continuing workflow")
                else:
                    self.update_status("✅ Settings popup FINALLY closed after aggressive methods")
            else:
                self.update_status("✅ Settings popup confirmed closed")
                
        except Exception as e:
            self.update_status(f"⚠️ Final verification failed: {e}")
            # Continue anyway

        # 🎯 ENHANCED: Extended wait for UI to settle after settings close
        self.update_status("⏳ Waiting for UI to settle after settings close...")
        time.sleep(5)  # Extended UI settle time for prompt input accessibility
        
        # 🎯 ENHANCED: Scroll to prompt area to ensure visibility
        self.update_status("📜 Scrolling to prompt input area...")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        
        # 🎯 ENHANCED: Remove any potential overlays
        self.driver.execute_script("""
            // Remove common overlay elements that might intercept clicks
            var overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="backdrop"]');
            overlays.forEach(function(overlay) {
                if (overlay.style.zIndex > 1000) {
                    overlay.style.display = 'none';
                }
            });
        """)

        self.update_status("✅ Settings popup closed and UI settled")
        return True

    def _check_settings_visibility(self):
        """Check if any SPECIFIC settings elements are visible"""
        try:
            # 🎯 PRIORITY SELECTORS: Most specific settings indicators
            priority_selectors = [
                "//button[contains(text(), 'Veo 3 - Fast')]",
                "//button[contains(text(), 'Tỷ lệ khung hình')]",
                "//button[contains(text(), 'Câu trả lời đầu ra')]"
            ]
            
            # Check priority selectors first (these are definitive settings elements)
            for selector in priority_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if any(elem.is_displayed() for elem in elements):
                    self.update_status(f"🔍 Found DEFINITIVE settings element: {selector}")
                    return True
            
            # 🎯 SECONDARY SELECTORS: Less specific but still indicative
            secondary_selectors = [
                "//button[contains(text(), 'Khổ ngang')]", 
                "//button[contains(text(), 'Mô hình')]"
            ]
            
            visible_secondary = 0
            for selector in secondary_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if any(elem.is_displayed() for elem in elements):
                    visible_secondary += 1
            
            # Settings popup likely open if 2+ secondary elements visible
            if visible_secondary >= 2:
                self.update_status(f"🔍 Found {visible_secondary} secondary settings elements - popup likely open")
                return True
                
            # 🎯 CONTEXT CHECK: Look for settings popup container
            try:
                popup_containers = self.driver.find_elements(By.XPATH, 
                    "//div[contains(@role, 'dialog') or contains(@class, 'popup') or contains(@class, 'modal')]")
                for container in popup_containers:
                    if container.is_displayed():
                        # Check if this container has settings content
                        container_text = container.text.lower()
                        if any(word in container_text for word in ['veo 3', 'tỷ lệ', 'mô hình', 'câu trả lời']):
                            self.update_status("🔍 Found settings popup container")
                            return True
            except:
                pass
            
            self.update_status("✅ No definitive settings elements found - popup appears closed")
            return False
            
        except Exception as e:
            self.update_status(f"⚠️ Settings detection error: {e}")
            return False  # Changed: Don't assume visible on error

    def _method_keyboard_close(self):
        """Method 1: Enhanced keyboard closure"""
        self.update_status("🔧 Method 1: Enhanced keyboard closure...")
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Multiple ESC attempts with different targets
            for i in range(5):
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                
            # Try other keys that might close popups
            body.send_keys(Keys.TAB)
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
            
            # Try clicking body and then ESC
            body.click()
            time.sleep(0.5)
            body.send_keys(Keys.ESCAPE)
            
        except Exception as e:
            self.update_status(f"⚠️ Keyboard method failed: {e}")

    def _method_button_close(self):
        """Method 2: Enhanced close button detection and clicking"""
        self.update_status("🔧 Method 2: Enhanced close button detection...")
        try:
            close_selectors = [
                "//button[contains(@aria-label, 'close') or contains(@aria-label, 'Close')]",
                "//button[contains(@title, 'close') or contains(@title, 'Close')]",
                "//button[contains(text(), '×')]",
                "//button[contains(text(), 'Đóng')]",
                "//button[contains(text(), 'close')]",
                "//*[contains(@class, 'close')]//button",
                "//button[contains(@class, 'close')]",
                "//*[@role='button'][contains(@aria-label, 'close')]",
                "//div[contains(@class, 'close-button')]",
                "//i[contains(@class, 'close')]//parent::button",
                "//span[contains(@class, 'close')]//parent::button"
            ]
            
            for selector in close_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            self.update_status(f"🔧 Clicking close button: {selector}")
                            # Try multiple click methods
                            try:
                                btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            self.update_status(f"⚠️ Button close method failed: {e}")

    def _method_outside_click(self):
        """Method 3: Click outside popup to close"""
        self.update_status("🔧 Method 3: Outside click and overlay removal...")
        try:
            # Click multiple areas outside popup
            click_points = [
                (50, 50),    # Top left
                (100, 100),  # Top left area
                (50, 500),   # Left middle
                (200, 50),   # Top area
            ]
            
            for x, y in click_points:
                self.driver.execute_script(f"""
                    var event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {x},
                        clientY: {y}
                    }});
                    document.elementFromPoint({x}, {y}).dispatchEvent(event);
                """)
                time.sleep(0.5)
                
            # Remove backdrop/overlay elements
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('[class*="backdrop"], [class*="overlay"], [class*="mask"]');
                overlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                    overlay.remove();
                });
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Outside click method failed: {e}")

    def _method_force_hide(self):
        """Method 4: Force hide settings elements"""
        self.update_status("🔧 Method 4: Force hiding settings elements...")
        try:
            self.driver.execute_script("""
                // Find and hide settings-related elements
                var settingsKeywords = [
                    'Veo 3 - Fast', 'Khổ ngang', 'Tỷ lệ khung hình', 
                    'Câu trả lời đầu ra', 'Mô hình', 'arrow_drop_down'
                ];
                
                settingsKeywords.forEach(function(keyword) {
                    var elements = document.evaluate(
                        "//*[contains(text(), '" + keyword + "')]",
                        document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null
                    );
                    
                    for (var i = 0; i < elements.snapshotLength; i++) {
                        var element = elements.snapshotItem(i);
                        
                        // Hide the element and its containers
                        var container = element.closest('div, section, aside, nav, form');
                        if (container) {
                            container.style.display = 'none';
                            container.style.visibility = 'hidden';
                            container.style.opacity = '0';
                            container.style.height = '0';
                            container.style.overflow = 'hidden';
                        }
                        
                        element.style.display = 'none';
                        element.style.visibility = 'hidden';
                    }
                });
                
                return true;
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Force hide method failed: {e}")

    def _method_nuclear_option(self):
        """Method 5: Nuclear option - remove everything settings-related"""
        self.update_status("🔧 Method 5: NUCLEAR OPTION - Removing all settings...")
        try:
            self.driver.execute_script("""
                // NUCLEAR OPTION: Remove all possible settings elements
                
                // 1. Remove by text content
                var allElements = document.getElementsByTagName('*');
                for (var i = allElements.length - 1; i >= 0; i--) {
                    var elem = allElements[i];
                    var text = elem.textContent || elem.innerText || '';
                    
                    if (text.includes('Veo 3') || text.includes('Khổ ngang') || 
                        text.includes('Tỷ lệ khung hình') || text.includes('Câu trả lời đầu ra') ||
                        text.includes('Mô hình') || text.includes('arrow_drop_down')) {
                        
                        // Try to find and remove the container
                        var container = elem.closest('div, section, aside, nav, form, dialog');
                        if (container && container !== document.body) {
                            container.remove();
                        } else {
                            elem.remove();
                        }
                    }
                }
                
                // 2. Remove common popup patterns
                var popupSelectors = [
                    '[role="dialog"]', '[aria-modal="true"]',
                    '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
                    '[class*="dropdown"]', '[class*="menu"]', '[class*="panel"]'
                ];
                
                popupSelectors.forEach(function(selector) {
                    var elements = document.querySelectorAll(selector);
                    elements.forEach(function(elem) {
                        if (elem.offsetParent !== null) { // Only if visible
                            elem.remove();
                        }
                    });
                });
                
                // 3. Hide anything with high z-index (likely overlays)
                var allDivs = document.querySelectorAll('div, section, aside');
                allDivs.forEach(function(div) {
                    var style = window.getComputedStyle(div);
                    var zIndex = parseInt(style.zIndex);
                    if (zIndex > 100) {
                        div.remove();
                    }
                });
                
                return true;
            """)
            
        except Exception as e:
            self.update_status(f"⚠️ Nuclear option failed: {e}")

    def _diagnostic_ui_state(self):
        """🎯 SIMPLIFIED: Basic UI check only"""
        # Simplified for speed - only essential checks
        pass

    def _validate_send_button(self, button):
        """🎯 VALIDATE: Comprehensive send button validation"""
        try:
            # 1. Basic checks
            if not button.is_displayed():
                return {'is_valid': False, 'reason': 'Button not visible'}
            
            if not button.is_enabled():
                return {'is_valid': False, 'reason': 'Button disabled'}
            
            # 2. Position validation - should be near prompt textarea
            try:
                prompt_inputs = self.driver.find_elements(By.XPATH, "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']")
                if prompt_inputs:
                    prompt_rect = self.driver.execute_script("return arguments[0].getBoundingClientRect();", prompt_inputs[0])
                    button_rect = self.driver.execute_script("return arguments[0].getBoundingClientRect();", button)
                    
                    # Check if button is within reasonable distance of prompt (vertically)
                    vertical_distance = abs(button_rect['top'] - (prompt_rect['top'] + prompt_rect['height']))
                    if vertical_distance > 200:  # More than 200px away vertically
                        return {'is_valid': False, 'reason': f'Button too far from prompt ({vertical_distance}px)'}
            except:
                pass
            
            # 3. Content validation
            button_text = (button.get_attribute('textContent') or '').strip().lower()
            button_aria = (button.get_attribute('aria-label') or '').strip().lower()
            button_title = (button.get_attribute('title') or '').strip().lower()
            
            # Check for negative indicators (buttons that are definitely NOT send buttons)
            negative_indicators = [
                'settings', 'cài đặt', 'help', 'trợ giúp', 'close', 'đóng',
                'edit', 'chỉnh sửa', 'delete', 'xóa', 'cancel', 'hủy',
                'back', 'quay lại', 'previous', 'trước', 'next', 'tiếp theo',
                'menu', 'thực đơn', 'options', 'tùy chọn'
            ]
            
            all_text = f"{button_text} {button_aria} {button_title}"
            if any(neg in all_text for neg in negative_indicators):
                return {'is_valid': False, 'reason': f'Negative indicator found: {all_text[:30]}'}
            
            # 4. Visual validation - check for send/arrow icons
            has_send_icon = self.driver.execute_script("""
                var btn = arguments[0];
                var text = btn.textContent || btn.innerHTML || '';
                
                // Check for arrow characters
                if (text.includes('→') || text.includes('▶') || text.includes('►') || 
                    text.includes('arrow_forward') || text.includes('send')) {
                    return 'arrow_text';
                }
                
                // Check for SVG arrows
                var svgs = btn.querySelectorAll('svg, path');
                for (var i = 0; i < svgs.length; i++) {
                    var svg = svgs[i];
                    var d = svg.getAttribute('d') || '';
                    var viewBox = svg.getAttribute('viewBox') || '';
                    
                    // Common arrow path patterns
                    if (d.includes('M') && d.includes('L') && d.length > 10) {
                        return 'svg_arrow';
                    }
                }
                
                // Check for button type
                if (btn.type === 'submit') {
                    return 'submit_type';
                }
                
                return false;
            """, button)
            
            # 5. Clickability test
            is_clickable = self.driver.execute_script("""
                var btn = arguments[0];
                var rect = btn.getBoundingClientRect();
                var centerX = rect.left + rect.width / 2;
                var centerY = rect.top + rect.height / 2;
                
                var elementAtPoint = document.elementFromPoint(centerX, centerY);
                return elementAtPoint === btn || btn.contains(elementAtPoint);
            """, button)
            
            if not is_clickable:
                return {'is_valid': False, 'reason': 'Button not clickable (blocked by other element)'}
            
            # 6. Final validation score
            validation_score = 0
            reasons = []
            
            if has_send_icon:
                validation_score += 50
                reasons.append(f"Has icon: {has_send_icon}")
            
            if button.get_attribute('type') == 'submit':
                validation_score += 30
                reasons.append("Submit type")
            
            if any(keyword in all_text for keyword in ['send', 'gửi', 'tạo', 'create', 'generate']):
                validation_score += 40
                reasons.append("Send-related text")
            
            if validation_score >= 30:  # Minimum score to be valid
                return {'is_valid': True, 'reason': f"Score: {validation_score} ({', '.join(reasons)})"}
            else:
                return {'is_valid': False, 'reason': f"Low validation score: {validation_score}"}
                
        except Exception as e:
            return {'is_valid': False, 'reason': f"Validation error: {e}"}

    def cleanup(self):
        """Enhanced cleanup với resource management - MEMORY SAFE"""
        import gc
        
        with self._lock:
            self._is_running = False

        if self.driver:
            try:
                with self._driver_lock:
                    # Stop any ongoing operations
                    try:
                        self.driver.execute_script("window.stop();")
                    except:
                        pass
                    
                    # Clear browser data
                    try:
                        self.driver.delete_all_cookies()
                    except:
                        pass
                    
                    self.driver.quit()
                    self.update_status("🔒 Chrome browser closed")
            except Exception as e:
                self.update_status(f"⚠️ Chrome cleanup error: {e}")
            finally:
                self.driver = None
                self.wait = None

        # Clear all tracking data
        with self._video_lock:
            self.downloaded_videos.clear()
            self.current_session_videos.clear()
            self.video_cache.clear()

        # Clear progress tracker
        self.progress_tracker = None
        
        # Force garbage collection to prevent memory leaks
        gc.collect()
        self.update_status("🧹 Memory cleanup completed")
    
    def _check_memory_usage(self):
        """Monitor memory usage and auto-cleanup if needed"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # If memory usage > 500MB, force cleanup
            if memory_mb > 500:
                self.update_status(f"⚠️ High memory usage: {memory_mb:.1f}MB - Force cleanup")
                gc.collect()
                
                # If still high after GC, more aggressive cleanup
                if process.memory_info().rss / 1024 / 1024 > 400:
                    with self._video_lock:
                        self.video_cache.clear()
                        # Only keep recent downloads
                        if len(self.downloaded_videos) > 50:
                            recent_videos = list(self.downloaded_videos)[-25:]
                            self.downloaded_videos.clear()
                            self.downloaded_videos.update(recent_videos)
                    gc.collect()
                    
        except Exception as e:
            pass  # Silent fail - don't spam logs

class ClausoNetGUI:
    def __init__(self):
        self.root = ctk.CTk()

        # 🎨 Set Windows application icon FIRST (before title/geometry)
        self.setup_application_icon()

        self.root.title("ClausoNet 4.0 Pro - Tạo Video AI")  # Set proper title for taskbar
        self.root.geometry("1200x800")

        # ⚠️ IMPORTANT: Hide window initially until license is verified
        self.root.withdraw()

        # Backend engine
        self.engine = None
        self.content_generator = None
        self.config = self.load_config()
        self.workflows = []
        self.current_workflow = None

        # Hardware info cache
        self.current_hardware_info = None

        # License expiry check system
        self.license_expiry_timer = None
        self.expiry_check_interval = 3600000  # Check every hour (3600000 ms)
        self.shown_expiry_warnings = set()  # Track shown warnings to avoid spam

        # Initialize profile manager
        self.profile_manager = ChromeProfileManager()

        # 🔑 Initialize SIMPLIFIED License System
        try:
            self.license_system = SimpleLicenseSystem()
            print("✅ Simple license system initialized")
        except Exception as e:
            print(f"⚠️ License system init error: {e}")
            self.license_system = None

        # Initialize Veo Workflow Engine
        self.veo_engine = None

        # 🔒 Initialize Status Manager
        self.status_manager = None

        # ⚠️ DON'T create GUI yet - wait until license is verified
        self.gui_created = False

    def setup_application_icon(self):
        """🎨 Setup Windows application icon for taskbar and window"""
        try:
            # Get current directory and icon paths
            current_dir = Path(__file__).parent.parent

            # Try multiple icon paths - EXISTING ICON FIRST
            icon_paths = [
                current_dir / "assets" / "icon.ico",         # ✅ EXISTING
                current_dir / "gv.ico",                     # ✅ ALTERNATIVE
                current_dir / "assets" / "clausonet_icon.ico",
                current_dir / "assets" / "app_icon.ico",
                current_dir / "icon.ico",
                current_dir / "clausonet.ico"
            ]

            # For EXE builds, also check in sys._MEIPASS if available
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller temp directory
                exe_dir = Path(sys._MEIPASS)
                icon_paths.insert(0, exe_dir / "assets" / "icon.ico")
                icon_paths.insert(1, exe_dir / "icon.ico")
                icon_paths.insert(2, exe_dir / "gv.ico")
                print(f"🔍 EXE mode detected, looking in: {exe_dir}")

            print(f"🔍 Looking for icon files in: {current_dir}")

            # Check if running on Windows
            if platform.system() == "Windows":
                # Debug: List all available icon files
                for icon_path in icon_paths:
                    print(f"🔍 Checking icon: {icon_path} - Exists: {icon_path.exists()}")

                # Try to set icon from available paths
                for icon_path in icon_paths:
                    if icon_path.exists():
                        try:
                            # Use absolute path for better compatibility
                            abs_icon_path = str(icon_path.resolve())
                            self.root.iconbitmap(abs_icon_path)

                            print(f"✅ Windows taskbar icon set: {abs_icon_path}")

                            # Store icon path for future reference
                            self.app_icon_path = abs_icon_path

                            return True
                        except Exception as e:
                            print(f"⚠️ Failed to set icon {icon_path}: {e}")
                            continue

                # If no .ico file found, try to create a default icon
                print("⚠️ No .ico file found, trying to create default icon...")
                return self.create_default_icon()
            else:
                # For non-Windows platforms, try other formats
                return self.setup_non_windows_icon()

        except Exception as e:
            print(f"❌ Icon setup error: {e}")
            return False

    def create_default_icon(self):
        """Create a default icon if no icon file exists"""
        try:
            # For Windows, use Windows API to set default application icon
            if platform.system() == "Windows":
                try:
                    import ctypes
                    # Set the app user model ID for better taskbar grouping
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ClausoNet.4.0.Pro")
                    print("✅ Windows AppID set for taskbar grouping")
                except Exception as e:
                    print(f"⚠️ Windows AppID setup failed: {e}")

            # Set a meaningful window title for taskbar identification
            self.root.title("🎯 ClausoNet 4.0 Pro - AI Video Generation")

            # Try to use a system icon as fallback
            try:
                # This will use the default application icon
                self.root.iconname("ClausoNet 4.0 Pro")
                print("✅ Set default system icon")
                return True
            except Exception as e:
                print(f"⚠️ Default icon setup failed: {e}")
                return False

        except ImportError as e:
            print(f"⚠️ PIL not available for icon creation: {e}")
            # Fallback - just ensure proper window title
            self.root.title("ClausoNet 4.0 Pro - AI Video Generation")
            return False
        except Exception as e:
            print(f"❌ Default icon creation failed: {e}")
            return False
            draw = ImageDraw.Draw(img)

            # Draw "CN" text for ClausoNet
            try:
                # Try to use a system font
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            # Center the text
            draw.text((4, 8), "CN", fill=(255, 255, 255, 255), font=font)

            # Save as ico in assets folder
            assets_dir = Path(__file__).parent.parent / "assets"
            assets_dir.mkdir(exist_ok=True)

            icon_path = assets_dir / "clausonet_default.ico"
            img.save(str(icon_path), format='ICO', sizes=[(32, 32)])

            # Set the created icon
            self.root.iconbitmap(str(icon_path))
            print(f"✅ Default icon created and set: {icon_path}")

        except ImportError:
            print("⚠️ PIL not available for icon creation")
        except Exception as e:
            print(f"⚠️ Default icon creation failed: {e}")

    def setup_non_windows_icon(self):
        """Setup icon for non-Windows platforms"""
        try:
            current_dir = Path(__file__).parent.parent

            # Try PNG/XBM formats for Linux/macOS - EXISTING PNG FIRST
            icon_paths = [
                current_dir / "assets" / "icon.png",         # ✅ EXISTING
                current_dir / "assets" / "clausonet.png",
                current_dir / "assets" / "icon.xbm"
            ]

            for icon_path in icon_paths:
                if icon_path.exists():
                    try:
                        # For tkinter, we can use PhotoImage for PNG
                        import tkinter as tk
                        photo = tk.PhotoImage(file=str(icon_path))
                        self.root.iconphoto(False, photo)
                        print(f"✅ Non-Windows icon set: {icon_path}")
                        return
                    except Exception as e:
                        print(f"⚠️ Failed to set icon {icon_path}: {e}")
                        continue

        except Exception as e:
            print(f"⚠️ Non-Windows icon setup error: {e}")

    def create_widgets(self):
        """Tạo các widget GUI giống như ảnh"""

        # Title header - ở giữa màn hình
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(title_frame, text="Tạo Video AI - By Tuệ Minh",
                    font=ctk.CTkFont(size=16, weight="bold")).pack()

        # Main tabview
        self.tabview = ctk.CTkTabview(self.root, width=1180, height=720)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Add tabs
        self.tabview.add("Workflow")
        self.tabview.add("Setting")

        # Set active tab
        self.tabview.set("Workflow")

        # Create workflow tab content
        self.create_workflow_tab()

        # Create setting tab content
        self.create_setting_tab()

        # Status bar
        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(self.root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def create_workflow_tab(self):
        """Tạo nội dung tab Workflow"""
        workflow_tab = self.tabview.tab("Workflow")

        # Main container
        main_container = ctk.CTkFrame(workflow_tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - wider like in original (70% of space)
        left_panel = ctk.CTkFrame(main_container, fg_color="#2b2b2b")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Workflow name - COMPACT
        ctk.CTkLabel(left_panel, text="Tên luồng công việc:", anchor="w", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(15, 2))
        self.workflow_name = ctk.CTkEntry(left_panel, placeholder_text="(No workflow selected)", height=25,
                                        fg_color="#404040", border_color="#555555")
        self.workflow_name.pack(fill="x", padx=15, pady=(0, 10))

        # Content - BLACK BACKGROUND like original, smaller height to make room for log
        ctk.CTkLabel(left_panel, text="Nội dung:", anchor="w", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(0, 2))
        self.content_text = ctk.CTkTextbox(
            left_panel,
            height=120,  # Reduced from 180 to make room for larger log
            wrap="word",
            fg_color="#000000",  # BLACK like original image
            text_color="white",
            border_color="#333333"
        )
        self.content_text.pack(fill="x", padx=15, pady=(0, 8))  # fill="x" instead of "both"

        # Settings grid frame - MORE COMPACT like original
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        settings_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Configure grid - 4 columns for compact layout
        for i in range(4):
            settings_frame.grid_columnconfigure(i, weight=1 if i in [1, 3] else 0)

        row = 0

        # ChatGPT Link - FULL WIDTH, smaller
        ctk.CTkLabel(settings_frame, text="Link ChatGPT:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.chatgpt_link = ctk.CTkEntry(settings_frame, height=22, fg_color="#404040")
        self.chatgpt_link.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=2)
        row += 1

        # GPT|Gemini Prompt + Open/Select buttons (adjacent) + ChatGPT Gemini API dropdown
        ctk.CTkLabel(settings_frame, text="Prompt GPT|Gemini:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)

        # Create sub-frame for Open/Select buttons to be adjacent
        gemini_buttons_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        gemini_buttons_frame.grid(row=row, column=1, sticky="w", padx=(8, 3), pady=2)

        self.gemini_open_btn = ctk.CTkButton(gemini_buttons_frame, text="Mở", width=45, height=22,
                                           fg_color="#0078d4", hover_color="#106ebe", command=self.open_gemini_prompt)
        self.gemini_open_btn.pack(side="left", padx=(0, 2))

        self.gemini_select_btn = ctk.CTkButton(gemini_buttons_frame, text="Chọn...", width=55, height=22,
                                             fg_color="#0078d4", hover_color="#106ebe", command=self.select_gemini_prompt)
        self.gemini_select_btn.pack(side="left")

        # ChatGPT Gemini API label and dropdown on same row
        ctk.CTkLabel(settings_frame, text="ChatGPT|Gemini API:", font=("Arial", 9)).grid(row=row, column=2, sticky="w", padx=(15, 5), pady=2)
        self.chatgpt_gemini_api_var = ctk.StringVar(value="")
        self.chatgpt_api_combo = ctk.CTkComboBox(settings_frame, variable=self.chatgpt_gemini_api_var,
                                               values=["Gemini API", "ChatGPT"], width=100, height=22,
                                               state="readonly", fg_color="#404040", button_color="#0078d4")
        self.chatgpt_api_combo.grid(row=row, column=3, sticky="w", padx=(0, 0), pady=2)
        row += 1

        # Video Duration + Your Prompt (Txt) + Open/Select buttons - ALL on SAME ROW like in image
        ctk.CTkLabel(settings_frame, text="Thời lượng video (s):", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.video_duration = ctk.CTkEntry(settings_frame, width=50, height=22, fg_color="#404040")
        self.video_duration.grid(row=row, column=1, sticky="w", padx=(8, 5), pady=2)
        self.video_duration.insert(0, "30")

        # Your Prompt (Txt) section in a sub-grid to fit 3 elements in columns 2-3
        prompt_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        prompt_frame.grid(row=row, column=2, columnspan=2, sticky="ew", padx=(5, 0), pady=2)
        prompt_frame.grid_columnconfigure(1, weight=0)
        prompt_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(prompt_frame, text="Prompt của bạn (Txt):", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=0)
        self.prompt_open_btn = ctk.CTkButton(prompt_frame, text="Mở", width=50, height=22,
                                           fg_color="#0078d4", hover_color="#106ebe", command=self.open_prompt_file)
        self.prompt_open_btn.grid(row=0, column=1, sticky="w", padx=(5, 3), pady=0)

        # Select button for Your Prompt (Txt) - SAME ROW
        self.prompt_select_btn = ctk.CTkButton(prompt_frame, text="Chọn...", width=50, height=22,
                                             fg_color="#0078d4", hover_color="#106ebe", command=self.select_prompt_file)
        self.prompt_select_btn.grid(row=0, column=2, sticky="w", padx=(3, 0), pady=0)
        row += 1

        # VEO Project link - FULL WIDTH, separate row
        ctk.CTkLabel(settings_frame, text="VEO Project link:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.veo_link = ctk.CTkEntry(settings_frame, height=22, fg_color="#404040")
        self.veo_link.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=2)
        row += 1

        # Type + Veo Profile on SAME ROW - like in image
        ctk.CTkLabel(settings_frame, text="Loại:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.type_var = ctk.StringVar(value="")
        self.type_combo = ctk.CTkComboBox(settings_frame, variable=self.type_var,
                                        values=["Text to Video", "Image to Video"],
                                        width=80, height=22, state="readonly", fg_color="#404040", button_color="#0078d4")
        self.type_combo.grid(row=row, column=1, sticky="w", padx=(8, 15), pady=2)

        ctk.CTkLabel(settings_frame, text="Hồ sơ Veo:", font=("Arial", 9)).grid(row=row, column=2, sticky="w", pady=2)
        self.veo_profile_var = ctk.StringVar(value="")
        self.veo_profile_combo = ctk.CTkComboBox(settings_frame, variable=self.veo_profile_var,
                                               values=[], width=80, height=22,
                                               state="readonly", fg_color="#404040", button_color="#0078d4",
                                               command=self.on_veo_profile_select)
        self.veo_profile_combo.grid(row=row, column=3, sticky="w", padx=(8, 0), pady=2)
        row += 1

        # Model + Video Count on SAME ROW - like in image
        ctk.CTkLabel(settings_frame, text="Mô hình:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.model_var = ctk.StringVar(value="")  # 🎯 START EMPTY
        # Official Google Veo models: Quality=best quality, Fast=speed optimized
        # Veo 3=with audio, Veo 2=video only
        self.model_combo = ctk.CTkComboBox(settings_frame, variable=self.model_var,
                                         values=["Veo 3 Quality", "Veo 3 Fast", "Veo 2 Quality", "Veo 2 Fast"], width=80, height=22,
                                         state="readonly", fg_color="#404040", button_color="#0078d4")
        self.model_combo.grid(row=row, column=1, sticky="w", padx=(8, 15), pady=2)
        # Don't set default value - leave empty until workflow selected

        ctk.CTkLabel(settings_frame, text="Số video:", font=("Arial", 9)).grid(row=row, column=2, sticky="w", pady=2)
        self.video_count_var = ctk.StringVar(value="")  # 🎯 START EMPTY
        self.video_count_combo = ctk.CTkComboBox(settings_frame, variable=self.video_count_var,
                                               values=["1", "2", "3", "4"], width=80, height=22,
                                               state="readonly", fg_color="#404040", button_color="#0078d4")
        self.video_count_combo.grid(row=row, column=3, sticky="w", padx=(8, 0), pady=2)
        # Don't set default value - leave empty until workflow selected
        row += 1

        # ⭐ ASPECT RATIO - NEW CONTROL
        ctk.CTkLabel(settings_frame, text="Tỷ lệ:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.aspect_ratio_var = ctk.StringVar(value="")  # 🎯 START EMPTY
        self.aspect_ratio_combo = ctk.CTkComboBox(settings_frame, variable=self.aspect_ratio_var,
                                                values=["16:9 (Khổ ngang)", "9:16 (Khổ dọc)"], width=120, height=22,
                                                state="readonly", fg_color="#404040", button_color="#0078d4")
        self.aspect_ratio_combo.grid(row=row, column=1, sticky="w", padx=(8, 15), pady=2)
        # Don't set default value - leave empty until workflow selected
        row += 1

        # Image Folder + Open/Select buttons (adjacent) on same row
        ctk.CTkLabel(settings_frame, text="Thư mục ảnh:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.image_folder = ctk.CTkEntry(settings_frame, height=22, fg_color="#404040")
        self.image_folder.grid(row=row, column=1, sticky="ew", padx=(8, 3), pady=2)

        # Create sub-frame for Open/Select buttons to be adjacent
        image_buttons_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        image_buttons_frame.grid(row=row, column=2, columnspan=2, sticky="w", padx=(3, 0), pady=2)

        self.image_open_btn = ctk.CTkButton(image_buttons_frame, text="Mở", width=45, height=22,
                                          fg_color="#0078d4", hover_color="#106ebe", command=self.browse_folder)
        self.image_open_btn.pack(side="left", padx=(0, 2))

        self.image_select_btn = ctk.CTkButton(image_buttons_frame, text="Chọn", width=45, height=22,
                                            fg_color="#0078d4", hover_color="#106ebe", command=self.select_image_folder)
        self.image_select_btn.pack(side="left")
        row += 1

        # Download Folder + Open/Select buttons (adjacent) on same row
        ctk.CTkLabel(settings_frame, text="Thư mục tải về:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        self.download_folder = ctk.CTkEntry(settings_frame, height=22, fg_color="#404040")
        self.download_folder.grid(row=row, column=1, sticky="ew", padx=(8, 3), pady=2)

        # Create sub-frame for Open/Select buttons to be adjacent
        download_buttons_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        download_buttons_frame.grid(row=row, column=2, columnspan=2, sticky="w", padx=(3, 0), pady=2)

        self.download_open_btn = ctk.CTkButton(download_buttons_frame, text="Mở", width=45, height=22,
                                             fg_color="#0078d4", hover_color="#106ebe", command=self.browse_download_folder)
        self.download_open_btn.pack(side="left", padx=(0, 2))

        self.download_select_btn = ctk.CTkButton(download_buttons_frame, text="Chọn", width=45, height=22,
                                               fg_color="#0078d4", hover_color="#106ebe", command=self.select_download_folder)
        self.download_select_btn.pack(side="left")

        # Action buttons frame - FIXED: Ensure proper variable naming
        action_button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        action_button_frame.pack(fill="x", padx=15, pady=(10, 5))

        # Action buttons - smaller and more compact like original
        self.save_btn = ctk.CTkButton(action_button_frame, text="Lưu", width=90, height=28,
                                    fg_color="#28a745", hover_color="#218838", command=self.save_workflow,
                                    font=("Arial", 10))
        self.save_btn.pack(side="left", padx=(0, 5))

        self.delete_btn = ctk.CTkButton(action_button_frame, text="Xóa", width=90, height=28,
                                      fg_color="#6c757d", hover_color="#5a6268", command=self.delete_workflow,
                                      font=("Arial", 10))
        self.delete_btn.pack(side="left", padx=(0, 5))

        self.start_btn = ctk.CTkButton(action_button_frame, text="Bắt đầu", width=90, height=28,
                                     fg_color="#17a2b8", hover_color="#138496", command=self.start_generation,
                                     font=("Arial", 10))
        self.start_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = ctk.CTkButton(action_button_frame, text="Dừng", width=90, height=28,
                                    fg_color="#dc3545", hover_color="#c82333", command=self.stop_generation,
                                    font=("Arial", 10))
        self.stop_btn.pack(side="left")

        # Log area frame - NOW APPEARS AFTER BUTTONS
        log_frame = ctk.CTkFrame(left_panel, fg_color="#1a1a1a")
        log_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))  # Reduced top padding

        # Clear log button only (no header text)
        log_header_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header_frame.pack(fill="x", padx=10, pady=(5, 5))

        # Clear log button
        self.clear_log_btn = ctk.CTkButton(log_header_frame, text="Xóa", width=50, height=20,
                                         fg_color="#6c757d", hover_color="#5a6268",
                                         command=self.clear_workflow_log, font=("Arial", 8))
        self.clear_log_btn.pack(side="right")

        # Log text area with scrollbar - EXPANDED HEIGHT
        self.workflow_log = ctk.CTkTextbox(
            log_frame,
            height=220,  # Increased from 150 to show more log content
            wrap="word",
            fg_color="#000000",
            text_color="#00ff00",  # Green text like terminal
            border_color="#333333",
            font=("Consolas", 9)  # Monospace font for log
        )
        self.workflow_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right panel - Workflow List (narrower like original ~30%)
        right_panel = ctk.CTkFrame(main_container, width=320, fg_color="#2b2b2b")
        right_panel.pack(side="right", fill="y", padx=(5, 0))
        right_panel.pack_propagate(False)

        # Workflow List header
        ctk.CTkLabel(right_panel, text="Danh sách luồng công việc", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        # Workflow scrollable frame
        self.workflow_scrollable = ctk.CTkScrollableFrame(right_panel, height=400, fg_color="#1a1a1a")
        self.workflow_scrollable.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Store workflow buttons for selection
        self.workflow_buttons = []

        # Bottom buttons frame for right panel - ALL IN ONE ROW
        bottom_buttons_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        bottom_buttons_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 15))

        # All buttons in one row: ↑ ↓ + New ▶ Start All
        # Up arrow button
        self.move_up_btn = ctk.CTkButton(bottom_buttons_frame, text="↑", width=30, height=25,
                                       fg_color="#404040", hover_color="#505050", font=("Arial", 10),
                                       command=self.move_workflow_up)
        self.move_up_btn.pack(side="left", padx=(0, 2))

        # Down arrow button
        self.move_down_btn = ctk.CTkButton(bottom_buttons_frame, text="↓", width=30, height=25,
                                         fg_color="#404040", hover_color="#505050", font=("Arial", 10),
                                         command=self.move_workflow_down)
        self.move_down_btn.pack(side="left", padx=(0, 8))

        # + New button - smaller
        self.new_btn = ctk.CTkButton(bottom_buttons_frame, text="+ Mới", width=80, height=25,
                                   fg_color="#28a745", hover_color="#218838", command=self.new_workflow)
        self.new_btn.pack(side="left", padx=(0, 5))

        # ▶ Start All button - smaller
        self.start_all_btn = ctk.CTkButton(bottom_buttons_frame, text="▶ Bắt đầu tất cả", width=110, height=25,
                                         fg_color="#28a745", hover_color="#218838", command=self.start_all_workflows)
        self.start_all_btn.pack(side="left")

    def create_setting_tab(self):
        """Tạo nội dung tab Setting như ảnh"""
        setting_tab = self.tabview.tab("Setting")

        # Main container
        main_container = ctk.CTkFrame(setting_tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Settings parameters
        left_panel = ctk.CTkFrame(main_container, fg_color="#2b2b2b", width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 5))
        left_panel.pack_propagate(False)

        # Settings grid frame
        settings_grid = ctk.CTkFrame(left_panel, fg_color="transparent")
        settings_grid.pack(fill="both", expand=True, padx=15, pady=15)

        # Configure grid for settings
        settings_grid.grid_columnconfigure(1, weight=1)

        # Settings data
        settings_data = [
            ("WAIT_GEN_VIDEO:", "20"),
            ("WAIT_GEN_IMAGE:", "20"),
            ("WAIT_IF_ERROR:", "9999"),
            ("WAIT_DOW_VIDEO:", "1"),
            ("WAIT_RESEND_VIDEO:", "520"),
            ("WAIT_RESEND_IMAGE:", "120"),
            ("WAIT_RANDOM_VIDEO:", "15"),
            ("WAIT_RANDOM_IMAGE:", "20"),
            ("NUMBER_REQUEST_DOW:", "10"),
            ("SHORT_WORKFLOW_NAME:", "W"),
            ("SHORT_VIDEO_NAME:", "V"),
            ("SHORT_IMAGE_NAME:", "I"),
        ]

        # Create settings entries
        self.setting_entries = {}
        for i, (label, default_value) in enumerate(settings_data):
            # Label
            ctk.CTkLabel(settings_grid, text=label, font=("Arial", 10), anchor="w").grid(
                row=i, column=0, sticky="w", pady=3, padx=(0, 10)
            )

            # Entry
            entry = ctk.CTkEntry(settings_grid, height=25, width=80, fg_color="#404040")
            entry.grid(row=i, column=1, sticky="w", pady=3)
            entry.insert(0, default_value)

            # Store reference
            setting_key = label.rstrip(":")
            self.setting_entries[setting_key] = entry

        # Center panel - Cookies (large area in middle)
        center_panel = ctk.CTkFrame(main_container, fg_color="#2b2b2b")
        center_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Cookies section - SMALLER textbox
        ctk.CTkLabel(center_panel, text="Cookies:", font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        self.cookies_text = ctk.CTkTextbox(center_panel, height=200, fg_color="#000000",
                                         text_color="white", border_color="#333333")
        self.cookies_text.pack(fill="x", padx=15, pady=(0, 10))

        # Cookies management buttons
        # Manual cookie buttons removed - cookies now handled automatically by backend

        # Profiles section - UNDER Cookies in center panel
        ctk.CTkLabel(center_panel, text="Hồ sơ:", font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Profile dropdown + 3 buttons frame - ALL ON SAME ROW in center panel
        profile_row_frame = ctk.CTkFrame(center_panel, fg_color="transparent")
        profile_row_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Profile dropdown
        self.profile_var = ctk.StringVar(value="Default")
        self.profile_combo = ctk.CTkComboBox(profile_row_frame, variable=self.profile_var,
                                           values=["Default", "Profile 1", "Profile 2"],
                                           width=80, height=30, state="readonly",
                                           fg_color="#404040", button_color="#0078d4",
                                           command=self.on_profile_select)
        self.profile_combo.pack(side="left", padx=(0, 5))

        # Also bind to StringVar for additional coverage
        self.profile_var.trace_add("write", self.on_profile_select)

        # 3 Profile buttons - như trong ảnh gốc
        self.new_profile_btn = ctk.CTkButton(profile_row_frame, text="+ Hồ sơ mới", width=100, height=30,
                                           fg_color="#28a745", hover_color="#218838",
                                           command=self.create_new_profile)
        self.new_profile_btn.pack(side="left", padx=(0, 3))

        self.open_profile_btn = ctk.CTkButton(profile_row_frame, text="📂 Mở hồ sơ", width=110, height=30,
                                            fg_color="#17a2b8", hover_color="#138496",
                                            command=self.open_profile_chrome)
        self.open_profile_btn.pack(side="left", padx=(0, 3))

        self.delete_profile_btn = ctk.CTkButton(profile_row_frame, text="🗑️ Xóa hồ sơ", width=120, height=30,
                                              fg_color="#dc3545", hover_color="#c82333",
                                              command=self.delete_profile)
        self.delete_profile_btn.pack(side="left", padx=(0, 3))

        # Profile guide button
        self.profile_guide_btn = ctk.CTkButton(profile_row_frame, text="❓ Hướng dẫn", width=100, height=30,
                                             fg_color="#6c757d", hover_color="#5a6268",
                                             command=self.show_profile_creation_guide_dialog)
        self.profile_guide_btn.pack(side="left", padx=(0, 3))

        # Extract Cookies button removed - cookies now handled automatically by backend

        # Gemini API Key section - AFTER 4 buttons
        ctk.CTkLabel(center_panel, text="Gemini API Key:", font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        self.gemini_api_key = ctk.CTkEntry(center_panel, placeholder_text="Nhập Gemini API Key",
                                         height=35, fg_color="#404040")
        self.gemini_api_key.pack(fill="x", padx=15, pady=(0, 10))

        # Save Setting button - RIGHT AFTER Gemini API Key
        self.save_setting_btn = ctk.CTkButton(center_panel, text="💾 Lưu cài đặt", width=400, height=40,
                                            fg_color="#0078d4", hover_color="#106ebe",
                                            font=("Arial", 12, "bold"), command=self.save_settings)
        self.save_setting_btn.pack(fill="x", padx=15, pady=(5, 15))

    def load_settings(self):
        """Load settings từ file và apply vào UI"""
        settings_file = Path('data/settings.json')

        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)

                # Load setting entries
                for key, entry in self.setting_entries.items():
                    if key in settings_data:
                        entry.delete(0, 'end')
                        entry.insert(0, settings_data[key])

                # Load cookies
                if 'COOKIES' in settings_data:
                    self.cookies_text.delete("1.0", "end")
                    self.cookies_text.insert("1.0", settings_data['COOKIES'])

                # Load Gemini API key
                if 'GEMINI_API_KEY' in settings_data:
                    self.gemini_api_key.delete(0, 'end')
                    self.gemini_api_key.insert(0, settings_data['GEMINI_API_KEY'])

                    # Update content generator with API key
                    if self.content_generator and settings_data['GEMINI_API_KEY'].strip():
                        self.content_generator.set_api_key('gemini', settings_data['GEMINI_API_KEY'].strip())

                # Load profile
                if 'PROFILE' in settings_data:
                    self.profile_var.set(settings_data['PROFILE'])

                print("Settings loaded successfully")



            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            print("No settings file found, using defaults")

    def save_settings(self):
        """Lưu settings và cập nhật content generator"""
        settings_data = {}
        for key, entry in self.setting_entries.items():
            settings_data[key] = entry.get().strip()

        # Add cookies, API key, and profile
        settings_data['COOKIES'] = self.cookies_text.get("1.0", "end").strip()
        settings_data['GEMINI_API_KEY'] = self.gemini_api_key.get().strip()
        settings_data['PROFILE'] = self.profile_var.get()

        # Save to file
        settings_file = Path('data/settings.json')
        settings_file.parent.mkdir(exist_ok=True)

        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            # Update content generator with new API key
            gemini_api_key = settings_data['GEMINI_API_KEY'].strip()
            if self.content_generator and gemini_api_key:
                self.content_generator.set_api_key('gemini', gemini_api_key)
                print(f"Updated Gemini API key in content generator")

            # Update config for future use
            if gemini_api_key:
                self.config.setdefault('apis', {}).setdefault('gemini', {})['api_key'] = gemini_api_key

            self.status_var.set("Settings saved successfully")
            messagebox.showinfo("Success", f"Settings saved successfully!\n{'API key updated.' if gemini_api_key else 'No API key provided.'}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def create_new_profile(self):
        """Tạo Chrome profile mới"""
        # License validation
        if not self.validate_license_for_operation():
            return

        # Get profile name from user
        profile_name = self.show_input_dialog("Tạo Chrome Profile Mới", "Nhập tên profile:")

        if profile_name and profile_name.strip():
            profile_name = profile_name.strip()

            try:
                # Check if profile already exists
                existing_profiles = self.profile_manager.list_profiles()
                if profile_name in existing_profiles:
                    messagebox.showerror("Lỗi", f"Profile '{profile_name}' đã tồn tại!")
                    return

                # Create new profile
                success = self.profile_manager.create_profile(profile_name)

                if success:
                    # Update dropdown lists
                    current_profiles = list(self.profile_combo.cget("values"))
                    if profile_name not in current_profiles:
                        current_profiles.append(profile_name)
                    self.profile_combo.configure(values=current_profiles)
                    self.profile_var.set(profile_name)

                    # ⭐ NEW: Also refresh Veo Profile dropdown in Workflow tab
                    self.refresh_veo_profile_dropdown()

                    # Get actual profile path for display
                    actual_profile_path = self.profile_manager.base_profile_dir / profile_name
                    
                    messagebox.showinfo("Thành công",
                        f"✅ Profile '{profile_name}' đã được tạo thành công!\n\n"
                        f"📂 Vị trí: {actual_profile_path}\n\n"
                        f"Các bước tiếp theo:\n"
                        f"1. Nhấp '📂 Mở Profile' để khởi động Chrome\n"
                        f"2. Đăng nhập vào tài khoản Google Veo của bạn\n"
                        f"3. Cookies sẽ được trích xuất tự động khi bạn chạy workflows")
                else:
                    messagebox.showerror("Lỗi", f"Không thể tạo profile '{profile_name}'")

            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo profile: {e}")
        else:
            messagebox.showwarning("Cảnh báo", "Tên profile không được để trống!")

    def open_profile_chrome(self):
        """Mở Chrome profile và hướng dẫn đăng nhập"""
        # License validation
        if not self.validate_license_for_operation():
            return

        current_profile = self.profile_var.get()

        if current_profile == "Default":
            messagebox.showwarning("Cảnh báo", "Vui lòng tạo profile mới trước!")
            return

        try:
            # Launch Chrome with profile
            process = self.profile_manager.launch_chrome_with_profile(current_profile, open_veo_login=True)

            # Show Vietnamese instructions dialog with beautiful UI
            result = self.show_vietnamese_login_guide_dialog(current_profile)

            if result == 'yes':
                self.extract_profile_cookies(current_profile)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Chrome: {e}")

    # extract_current_profile_cookies method removed - cookies now handled automatically by backend

    def show_vietnamese_login_guide_dialog(self, profile_name):
        """🇻🇳 Hiển thị dialog hướng dẫn đăng nhập bằng tiếng Việt với giao diện đẹp"""
        # Create beautiful dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Hướng dẫn đăng nhập Profile")
        dialog.geometry("650x750")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"650x750+{x}+{y}")

        # Result variable
        result = ['no']

        # Header with gradient-like effect
        header_frame = ctk.CTkFrame(dialog, fg_color="#1f538d", height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(header_frame, 
                    text="🚀 Hướng dẫn đăng nhập Google Account",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color="white").pack(expand=True)

        # Main content frame
        main_frame = ctk.CTkScrollableFrame(dialog, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Profile info section
        profile_info_frame = ctk.CTkFrame(main_frame, fg_color="#404040")
        profile_info_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(profile_info_frame, 
                    text=f"📁 Profile đang sử dụng: {profile_name}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#4CAF50").pack(pady=15)

        # Step 1
        step1_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        step1_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(step1_frame, 
                    text="📋 Bước 1: Đăng nhập Gmail (Google)",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="#FFA726").pack(pady=(15, 5), padx=20, anchor="w")

        step1_content = """Khi Veo(VEO3) bây giờ đang nhập Google, hãy đăng nhập Gmail trước
hoặc mở Gmail(Gmail(Google))"""

        ctk.CTkLabel(step1_frame, 
                    text=step1_content,
                    font=ctk.CTkFont(size=14),
                    text_color="#E0E0E0",
                    justify="left").pack(pady=(0, 15), padx=20, anchor="w")

        # Step 2  
        step2_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        step2_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(step2_frame, 
                    text="🔗 Bước 2: Mở Flow(VEO3) và đăng nhập",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="#FFA726").pack(pady=(15, 5), padx=20, anchor="w")

        # URL input field
        url_frame = ctk.CTkFrame(step2_frame, fg_color="#404040")
        url_frame.pack(fill="x", padx=20, pady=(5, 10))

        ctk.CTkLabel(url_frame, 
                    text="🌐 URL chuẩn để truy cập:",
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 5), padx=10, anchor="w")

        url_entry = ctk.CTkEntry(url_frame, 
                                font=ctk.CTkFont(size=13),
                                height=40)
        url_entry.pack(fill="x", padx=10, pady=(0, 5))
        url_entry.insert(0, "https://labs.google/fx/tools/flow")
        url_entry.configure(state="readonly")

        def copy_url():
            dialog.clipboard_clear()
            dialog.clipboard_append("https://labs.google/fx/tools/flow")
            messagebox.showinfo("Đã sao chép", "URL đã được sao chép vào clipboard!")

        ctk.CTkButton(url_frame, 
                     text="📋 Sao chép URL",
                     width=140,
                     height=35,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     command=copy_url).pack(pady=(0, 10))

        step2_content = """Sau khi đăng nhập trong các bước trên thì tại đây vào & lưu cookie
Xác nhận đăng nhập và lưu cookie"""

        ctk.CTkLabel(step2_frame, 
                    text=step2_content,
                    font=ctk.CTkFont(size=12),
                    text_color="#E0E0E0",
                    justify="left").pack(pady=(0, 15), padx=20, anchor="w")

        # Advantages section
        advantages_frame = ctk.CTkFrame(main_frame, fg_color="#1a4d3a")
        advantages_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(advantages_frame, 
                    text="✨ Ưu điểm của phương pháp mới (CDP):",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#81C784").pack(pady=(15, 10), padx=20, anchor="w")

        advantages = [
            "🔄 Theo dõi cookie thời gian thực",
            "🚫 Không xung đột hệ thống file", 
            "⚡ Trích xuất ngay lập tức (không cần khởi động lại Chrome)",
            "🛡️ Duy trì tách biệt profile",
            "📊 Phát hiện xác thực trực tiếp"
        ]

        for advantage in advantages:
            ctk.CTkLabel(advantages_frame, 
                        text=f"  • {advantage}",
                        font=ctk.CTkFont(size=11),
                        text_color="#C8E6C9",
                        justify="left").pack(pady=2, padx=30, anchor="w")

        ctk.CTkLabel(advantages_frame, text="", height=10).pack()  # Spacer

        # Action buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def on_success():
            result[0] = 'yes'
            dialog.destroy()

        def on_cancel():
            result[0] = 'no'
            dialog.destroy()

        # Button container for centering
        btn_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        btn_container.pack(expand=True)

        ctk.CTkButton(btn_container, 
                     text="✅ Đã đăng nhập thành công",
                     width=200,
                     height=40,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#4CAF50",
                     hover_color="#45a049",
                     command=on_success).pack(side="left", padx=(0, 15))

        ctk.CTkButton(btn_container, 
                     text="❌ Hủy bỏ",
                     width=120,
                     height=40,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#f44336",
                     hover_color="#da190b",
                     command=on_cancel).pack(side="left")

        # Wait for dialog to close
        dialog.wait_window()
        return result[0]

    def show_profile_creation_guide_dialog(self):
        """🇻🇳 Hiển thị dialog hướng dẫn tạo profile mới"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Hướng dẫn tạo Chrome Profile")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="#1f538d", height=70)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(header_frame, 
                    text="📁 Hướng dẫn tạo Chrome Profile",
                    font=ctk.CTkFont(size=22, weight="bold"),
                    text_color="white").pack(expand=True)

        # Main content
        main_frame = ctk.CTkScrollableFrame(dialog, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Step 1
        step1_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        step1_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(step1_frame, 
                    text="🚀 Bước 1: Tạo Profile mới",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="#FFA726").pack(pady=(15, 5), padx=20, anchor="w")

        step1_content = """1. Nhấp vào button "➕ Tạo Profile Mới" trong tab Cài đặt
2. Nhập tên profile (ví dụ: "veo_profile_1", "my_google_account")
3. Nhấp "OK" để tạo profile"""

        ctk.CTkLabel(step1_frame, 
                    text=step1_content,
                    font=ctk.CTkFont(size=12),
                    text_color="#E0E0E0",
                    justify="left").pack(pady=(0, 15), padx=20, anchor="w")

        # Step 2
        step2_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        step2_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(step2_frame, 
                    text="🌐 Bước 2: Mở Chrome với Profile",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#FFA726").pack(pady=(15, 5), padx=20, anchor="w")

        step2_content = """1. Chọn profile vừa tạo từ dropdown
2. Nhấp "📂 Mở Profile" để khởi động Chrome
3. Chrome sẽ mở với profile riêng biệt"""

        ctk.CTkLabel(step2_frame, 
                    text=step2_content,
                    font=ctk.CTkFont(size=12),
                    text_color="#E0E0E0",
                    justify="left").pack(pady=(0, 15), padx=20, anchor="w")

        # Step 3
        step3_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        step3_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(step3_frame, 
                    text="🔑 Bước 3: Đăng nhập tài khoản",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#FFA726").pack(pady=(15, 5), padx=20, anchor="w")

        step3_content = """1. Đăng nhập vào tài khoản Google của bạn
2. Truy cập: https://labs.google/fx/tools/flow
3. Đảm bảo đăng nhập thành công
4. Cookies sẽ được lưu tự động"""

        ctk.CTkLabel(step3_frame, 
                    text=step3_content,
                    font=ctk.CTkFont(size=12),
                    text_color="#E0E0E0",
                    justify="left").pack(pady=(0, 15), padx=20, anchor="w")

        # Important notes
        note_frame = ctk.CTkFrame(main_frame, fg_color="#4d1f1f")
        note_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(note_frame, 
                    text="⚠️ Lưu ý quan trọng:",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#FF7043").pack(pady=(15, 5), padx=20, anchor="w")

        notes = [
            "Mỗi profile sử dụng tài khoản Google khác nhau",
            "Không được sử dụng chung profile giữa nhiều tài khoản", 
            "Profile sẽ lưu trữ cookie và session riêng biệt",
            "Đảm bảo tài khoản có quyền truy cập Veo"
        ]

        for note in notes:
            ctk.CTkLabel(note_frame, 
                        text=f"  • {note}",
                        font=ctk.CTkFont(size=11),
                        text_color="#FFAB91",
                        justify="left").pack(pady=2, padx=30, anchor="w")

        ctk.CTkLabel(note_frame, text="", height=10).pack()  # Spacer

        # Close button
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def close_dialog():
            dialog.destroy()

        ctk.CTkButton(button_frame, 
                     text="✅ Đã hiểu",
                     width=150,
                     height=40,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#4CAF50",
                     hover_color="#45a049",
                     command=close_dialog).pack(expand=True)

        # Wait for dialog to close
        dialog.wait_window()

    def extract_profile_cookies(self, profile_name):
        """Trích xuất cookies từ profile và điền vào ô cookies"""
        try:
            # Show processing dialog
            processing_dialog = ctk.CTkToplevel(self.root)
            processing_dialog.title("Extracting Cookies")
            processing_dialog.geometry("400x200")
            processing_dialog.transient(self.root)
            processing_dialog.grab_set()

            # Center dialog
            processing_dialog.update_idletasks()
            x = (processing_dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (processing_dialog.winfo_screenheight() // 2) - (200 // 2)
            processing_dialog.geometry(f"400x200+{x}+{y}")

            label = ctk.CTkLabel(processing_dialog, text="🔄 Extracting cookies from Chrome...\n\nPlease wait...",
                               font=ctk.CTkFont(size=14))
            label.pack(expand=True)

            def extract_cookies_thread():
                try:
                    time.sleep(2)  # Give Chrome time to save cookies

                    # Use CDP for real-time cookie extraction
                    login_status = self.profile_manager.check_profile_login_status(profile_name, use_cdp=True)

                    self.root.after(0, lambda: processing_dialog.destroy())

                    if login_status.get('logged_in'):
                        cookies = login_status.get('cookies', '')

                        # Fill cookies into textbox
                        self.cookies_text.delete("1.0", "end")
                        self.cookies_text.insert("1.0", cookies)

                        # ⭐ NEW: Auto-save cookies for this profile
                        auto_save_success = self.auto_save_profile_cookies(profile_name, cookies)

                        # Get improved auth info
                        traditional_auth = login_status.get('traditional_auth_cookies', [])
                        veo_auth = login_status.get('veo_auth_cookies', [])

                        # Enhanced success message for CDP
                        method = login_status.get('method', 'Unknown')
                        save_status = "✅ Cookies auto-saved for this profile!" if auto_save_success else "⚠️ Cookies extracted but auto-save failed!"

                        success_msg = f"""✅ COOKIES EXTRACTED SUCCESSFULLY via {method}!

🎯 Profile: {profile_name}
📊 Total cookies: {login_status.get('total_cookies', 'N/A')}
🔐 Auth cookies: {login_status.get('auth_cookies', 'N/A')}
⚡ Critical cookies: {login_status.get('critical_cookies', 'N/A')}

{save_status}
📁 Cookies saved to: data/profile_cookies/{profile_name}.json

✅ Ready to use with Veo API!"""

                        messagebox.showinfo("Success", success_msg)

                    else:
                        # Get detailed debug info
                        traditional_auth = login_status.get('traditional_auth_cookies', [])
                        veo_auth = login_status.get('veo_auth_cookies', [])
                        has_email = login_status.get('has_email', False)
                        has_session = login_status.get('has_session_token', False)
                        debug_info = login_status.get('debug_info', 'No debug info')
                        error_msg_detail = login_status.get('error', '')

                        # Check if it's a "no cookies database" issue
                        cookies_result = login_status.get('cookies', '')

                        if "No cookies database found" in cookies_result:
                            error_msg = f"""❌ NO COOKIES DATABASE FOUND

🔍 Profile '{profile_name}' hasn't been used to browse websites yet.

📋 What you need to do:
1. 📂 Click 'Open Profile' to launch Chrome with this profile
2. 🌐 Navigate to: https://labs.google/fx/tools/flow
3. 🔐 Login with your Google account for Veo access
4. ✅ Make sure you can access the Veo interface
5. 🍪 Cookies will be extracted automatically for workflows

💡 The profile needs to be logged in for automatic cookie extraction!"""
                        else:
                            error_msg = f"""❌ LOGIN NOT DETECTED

⚠️ No Google authentication cookies found in profile '{profile_name}'.

🔄 Please try again:
1. Make sure you logged into Google Veo successfully
2. Wait a few seconds after login
3. Try extracting cookies again

🔍 Debug info: {debug_info}
📋 Traditional auth cookies: {len(traditional_auth)}
🎯 Veo auth cookies: {len(veo_auth)}
📧 Has email cookie: {has_email}
🔑 Has session token: {has_session}
⚠️ Error details: {error_msg_detail}"""

                        messagebox.showwarning("Login Not Detected", error_msg)

                except Exception as e:
                    self.root.after(0, lambda: processing_dialog.destroy())
                    messagebox.showerror("Error", f"Failed to extract cookies: {e}")

            # Start extraction in thread
            threading.Thread(target=extract_cookies_thread, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract cookies: {e}")

    def delete_profile(self):
        """Xóa Chrome profile"""
        current_profile = self.profile_var.get()

        if current_profile == "Default":
            messagebox.showwarning("Warning", "Cannot delete the Default profile!")
            return

        result = messagebox.askyesno("Confirm Delete",
            f"Are you sure you want to delete profile '{current_profile}'?\n\n"
            "This will permanently remove all data for this profile including:\n"
            "• Login sessions\n"
            "• Cookies\n"
            "• Browsing history\n"
            "• Bookmarks\n\n"
            "This action cannot be undone!")

        if result:
            try:
                success = self.profile_manager.delete_profile(current_profile)

                if success:
                    # Delete saved cookies for this profile as well
                    try:
                        from utils.resource_manager import resource_manager
                        cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
                        cookies_file = cookies_dir / f"{current_profile}.json"
                    except ImportError:
                        # Fallback to relative path
                        cookies_file = Path(f"data/profile_cookies/{current_profile}.json")
                    
                    if cookies_file.exists():
                        try:
                            cookies_file.unlink()
                            print(f"✅ Deleted saved cookies for profile '{current_profile}' from {cookies_file}")
                        except Exception as e:
                            print(f"⚠️ Could not delete cookies file: {e}")

                    # Update dropdown
                    current_profiles = list(self.profile_combo.cget("values"))
                    if current_profile in current_profiles:
                        current_profiles.remove(current_profile)
                    self.profile_combo.configure(values=current_profiles)
                    self.profile_var.set("Default")

                    # Clear cookies textbox when switching to Default
                    self.cookies_text.delete("1.0", "end")

                    messagebox.showinfo("Success", f"Profile '{current_profile}' deleted successfully!")
                else:
                    messagebox.showerror("Error", f"Profile '{current_profile}' not found!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete profile: {e}")

    def auto_save_profile_cookies(self, profile_name, cookies):
        """Tự động lưu cookies cho profile ngay sau khi extract thành công"""
        try:
            if profile_name == "Default":
                # Don't auto-save for Default profile
                return False

            # 🎯 Use ResourceManager for consistent data storage
            try:
                from utils.resource_manager import resource_manager
                cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
            except ImportError:
                # Fallback to relative path
                cookies_dir = Path("data/profile_cookies")
            
            cookies_dir.mkdir(parents=True, exist_ok=True)

            # Lưu cookies vào file JSON riêng cho profile
            cookies_file = cookies_dir / f"{profile_name}.json"

            with open(cookies_file, 'w', encoding='utf-8') as f:
                f.write(cookies)

            print(f"✅ Auto-saved cookies for profile '{profile_name}' to {cookies_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to auto-save cookies for profile '{profile_name}': {e}")
            return False

    def auto_load_profile_cookies(self, profile_name):
        """Tự động nạp cookies của profile khi chọn profile"""
        try:
            if profile_name == "Default":
                # Clear cookies for Default profile
                self.cookies_text.delete("1.0", "end")
                print(f"ℹ️ Cleared cookies for Default profile")
                return True

            # 🎯 Use ResourceManager for consistent data storage
            try:
                from utils.resource_manager import resource_manager
                cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
                cookies_file = cookies_dir / f"{profile_name}.json"
            except ImportError:
                # Fallback to relative path
                cookies_file = Path(f"data/profile_cookies/{profile_name}.json")

            if cookies_file.exists():
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = f.read()

                # Điền cookies vào textbox
                self.cookies_text.delete("1.0", "end")
                self.cookies_text.insert("1.0", cookies)

                print(f"✅ Auto-loaded cookies for profile '{profile_name}' from {cookies_file}")
                return True
            else:
                # Nếu không có cookies saved, clear textbox
                self.cookies_text.delete("1.0", "end")
                print(f"ℹ️ No saved cookies found for profile '{profile_name}' - cleared textbox")
                return False

        except Exception as e:
            print(f"❌ Failed to auto-load cookies for profile '{profile_name}': {e}")
            return False

    def on_profile_select(self, *args):
        """Called when user selects a profile from dropdown"""
        selected_profile = self.profile_var.get()
        print(f"🔄 Profile selected: {selected_profile}")

        # Auto-load cookies for selected profile
        self.auto_load_profile_cookies(selected_profile)

    # save_profile_cookies method removed - cookies now handled automatically by backend

    # load_profile_cookies method removed - cookies now handled automatically by backend

    def refresh_profile_list(self):
        """Cập nhật danh sách profiles trong dropdown"""
        try:
            available_profiles = self.profile_manager.list_profiles()
            all_profiles = ["Default"] + available_profiles

            # Update dropdown
            self.profile_combo.configure(values=all_profiles)

            # Keep current selection if valid
            current = self.profile_var.get()
            if current not in all_profiles:
                self.profile_var.set("Default")

            # ⭐ NEW: Auto-load cookies for current profile
            current_profile = self.profile_var.get()
            self.auto_load_profile_cookies(current_profile)

            # ⭐ NEW: Also refresh Veo Profile dropdown in Workflow tab
            self.refresh_veo_profile_dropdown()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh profile list: {e}")

    def get_veo_profiles_list(self):
        """Lấy danh sách Chrome profiles để hiển thị trong Veo Profile dropdown"""
        try:
            available_profiles = self.profile_manager.list_profiles()
            all_profiles = ["Select Profile..."] + available_profiles
            return all_profiles
        except Exception as e:
            print(f"Error getting Veo profiles: {e}")
            return ["Select Profile..."]

    def clear_veo_profile_dropdown(self):
        """Xóa tất cả dropdown khi không có workflow nào được chọn"""
        self.veo_profile_combo.configure(values=[])
        self.veo_profile_var.set("")

        # Clear other dropdowns too
        self.type_var.set("")
        self.type_combo.set("")

        self.model_var.set("")
        self.model_combo.set("")

        self.video_count_var.set("")
        self.video_count_combo.set("")

        self.chatgpt_gemini_api_var.set("")
        self.chatgpt_api_combo.set("")

    def refresh_veo_profile_dropdown(self):
        """Cập nhật dropdown Veo Profile trong Workflow tab"""
        try:
            # Only refresh if a workflow is currently selected
            if hasattr(self, 'current_workflow') and self.current_workflow is not None:
                new_values = self.get_veo_profiles_list()
                self.veo_profile_combo.configure(values=new_values)

                # Keep current selection if valid
                current = self.veo_profile_var.get()
                if current not in new_values:
                    if len(new_values) > 1:  # Has profiles other than "Select Profile..."
                        self.veo_profile_var.set(new_values[1])  # Select first real profile
                    else:
                        self.veo_profile_var.set("Select Profile...")
            else:
                # No workflow selected, clear dropdown
                self.clear_veo_profile_dropdown()
        except Exception as e:
            print(f"Error refreshing Veo profile dropdown: {e}")

    def on_veo_profile_select(self, selected_profile):
        """Khi user chọn Veo profile trong Workflow tab"""
        print(f"Selected Veo Profile: {selected_profile}")

        # Validate selection
        if selected_profile == "Select Profile...":
            messagebox.showinfo("Thông tin", "Vui lòng tạo Chrome profile trong tab Cài đặt trước,\nsau đó chọn nó ở đây để sử dụng Veo automation.")
            return

        # Save to current workflow if exists
        if hasattr(self, 'current_workflow') and self.current_workflow is not None:
            if self.current_workflow < len(self.workflows):
                self.workflows[self.current_workflow]['veo_profile'] = selected_profile
                print(f"Saved Veo profile '{selected_profile}' to current workflow")

    def on_profile_select(self, *args):
        """Khi user chọn profile trong Settings tab - cũng cập nhật Veo dropdown"""
        current_profile = self.profile_var.get()
        print(f"Profile selected: {current_profile}")

        # Auto-load cookies for this profile
        self.auto_load_profile_cookies(current_profile)

    def browse_folder(self):
        """Chọn thư mục hình ảnh"""
        # License validation
        if not self.validate_license_for_operation():
            return

        folder = filedialog.askdirectory()
        if folder:
            self.image_folder.delete(0, "end")
            self.image_folder.insert(0, folder)

    def browse_download_folder(self):
        """Chọn thư mục download"""
        # License validation
        if not self.validate_license_for_operation():
            return

        folder = filedialog.askdirectory()
        if folder:
            self.download_folder.delete(0, "end")
            self.download_folder.insert(0, folder)

    def open_gemini_prompt(self):
        """🔍 Open và hiển thị prompt file đã tạo"""
        # License validation
        if not self.validate_license_for_operation():
            return

        try:
            # Tìm file prompt gần nhất
            output_dir = Path("output")
            if not output_dir.exists():
                messagebox.showwarning("No Files", "No output directory found!\nPlease generate prompts first.")
                return

            # Tìm file prompt dựa trên provider được chọn
            selected_provider = self.chatgpt_gemini_api_var.get()

            if selected_provider == "ChatGPT":
                prompt_files = list(output_dir.glob("chatgpt_prompt*.txt"))
                file_type = "ChatGPT"
            elif selected_provider == "Gemini API":
                prompt_files = list(output_dir.glob("geminiai_prompt*.txt"))
                file_type = "Gemini AI"
            else:
                # Fallback - tìm tất cả prompt files
                prompt_files = list(output_dir.glob("*_prompt*.txt"))
                file_type = "AI"

            if not prompt_files:
                # Không có file, cho phép user chọn file
                file_path = filedialog.askopenfilename(
                    title=f"Open {file_type} Prompt File",
                    initialdir="output",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                )
                if not file_path:
                    return
                selected_file = Path(file_path)
            else:
                # Lấy file mới nhất
                selected_file = max(prompt_files, key=lambda p: p.stat().st_mtime)

            # Đọc và hiển thị content
            with open(selected_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Hiển thị trong dialog
            self.show_prompt_content_dialog(str(selected_file), content)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open prompt file:\n{str(e)}")

    def select_gemini_prompt(self):
        """🎯 Tạo prompt mới từ content hiện tại"""
        # License validation
        if not self.validate_license_for_operation():
            return

        try:
            # Kiểm tra content
            content = self.content_text.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showwarning("No Content", "Please enter content first!")
                return

            # Kiểm tra provider
            selected_provider = self.chatgpt_gemini_api_var.get()
            if not selected_provider or selected_provider not in ["Gemini API", "ChatGPT"]:
                messagebox.showwarning("No Provider", "Please select ChatGPT or Gemini API first!")
                return

            # Confirmation dialog
            confirm_msg = f"🎯 CREATE {selected_provider.upper()} PROMPT\n\n"
            confirm_msg += f"Content: {content[:100]}{'...' if len(content) > 100 else ''}\n"
            confirm_msg += f"Provider: {selected_provider}\n\n"
            confirm_msg += f"This will generate video prompts and save to:\n"

            if selected_provider == "ChatGPT":
                filename = "chatgpt_prompt.txt"
            else:
                filename = "geminiai_prompt.txt"

            confirm_msg += f"• output/{filename}\n\n"
            confirm_msg += f"Continue?"

            if not messagebox.askyesno("Create Prompt", confirm_msg):
                return

            # Disable button và tạo prompt
            self.gemini_select_btn.configure(state="disabled")
            self.status_var.set(f"Creating {selected_provider} prompt...")

            # Chạy trong thread
            def create_prompt():
                try:
                    result = self.generate_prompt_only(content, selected_provider)
                    self.root.after(0, self.on_prompt_creation_complete, result)
                except Exception as e:
                    self.root.after(0, self.on_prompt_creation_error, str(e))

            import threading
            thread = threading.Thread(target=create_prompt, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create prompt:\n{str(e)}")

    def generate_prompt_only(self, content: str, provider: str) -> Dict[str, Any]:
        """🎯 Tạo prompt riêng từ content và provider"""
        # 🔒 VALIDATE LICENSE BEFORE PROMPT GENERATION
        if not self.validate_license_for_operation("prompt generation"):
            return {"success": False, "error": "License validation failed"}

        try:
            # Check if content generator is available
            if not self.content_generator:
                return {
                    'success': False,
                    'error': "Content generator not initialized. Please configure API keys in Settings."
                }

            # Validate provider
            if provider not in ["Gemini API", "ChatGPT"]:
                return {
                    'success': False,
                    'error': f"Invalid provider: {provider}"
                }

            provider_key = 'gemini' if provider == 'Gemini API' else 'chatgpt'

            # Check if provider is available
            if not self.content_generator.is_provider_available(provider_key):
                return {
                    'success': False,
                    'error': f"{provider} API not configured. Please add API key in Settings."
                }

            # Generate video prompts using content generator
            prompts_result = self.content_generator.generate_video_prompts(
                script=content,
                provider=provider_key,
                style='cinematic'
            )

            if prompts_result.get('status') != 'success':
                return {
                    'success': False,
                    'error': prompts_result.get('error_message', 'Failed to generate prompts')
                }

            video_prompts = prompts_result.get('video_prompts', '')

            # 🎯 USE RESOURCEMANAGER FOR PROPER OUTPUT PATHS
            default_paths = self.get_default_output_paths()

            # Save to specific filename based on provider
            if provider == "ChatGPT":
                prompt_filename = os.path.join(default_paths['prompts'], "chatgpt_prompt.txt")
            else:
                prompt_filename = os.path.join(default_paths['prompts'], "geminiai_prompt.txt")

            # Save prompt to file
            with open(prompt_filename, 'w', encoding='utf-8') as f:
                f.write(f"Provider: {provider}\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Original Content: {content}\n")
                f.write(f"\n{'='*50}\n")
                f.write(f"VIDEO PROMPTS:\n")
                f.write(f"{'='*50}\n\n")
                f.write(video_prompts)

            return {
                'success': True,
                'prompt_file': prompt_filename,
                'video_prompts': video_prompts,
                'provider': provider,
                'original_content': content
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Prompt generation error: {str(e)}"
            }

    def on_prompt_creation_complete(self, result):
        """Callback khi tạo prompt hoàn thành"""
        self.gemini_select_btn.configure(state="normal")

        if result.get('success'):
            provider = result.get('provider', 'AI')
            prompt_file = result.get('prompt_file', '')
            video_prompts = result.get('video_prompts', '')

            success_msg = f"🎯 {provider.upper()} PROMPT CREATED!\n\n"
            success_msg += f"✅ Provider: {provider}\n"
            success_msg += f"📁 File: {prompt_file}\n"
            success_msg += f"📝 Length: {len(video_prompts)} characters\n\n"
            success_msg += f"Prompt preview:\n"
            success_msg += f"{video_prompts[:200]}{'...' if len(video_prompts) > 200 else ''}\n\n"
            success_msg += f"💡 Use 'Open' button to view full content"

            messagebox.showinfo("Prompt Created", success_msg)
            self.status_var.set(f"✅ {provider} prompt created: {prompt_file}")

            # Automatically open the created prompt
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.show_prompt_content_dialog(prompt_file, content)

        else:
            error_msg = result.get('error', 'Unknown error')
            messagebox.showerror("Prompt Creation Failed", f"❌ Failed to create prompt:\n\n{error_msg}")
            self.status_var.set("Prompt creation failed")

    def on_prompt_creation_error(self, error_msg):
        """Callback khi có lỗi tạo prompt"""
        self.gemini_select_btn.configure(state="normal")
        self.status_var.set(f"Error: {error_msg}")
        messagebox.showerror("Error", f"Prompt creation error:\n{error_msg}")

    def show_prompt_content_dialog(self, file_path: str, content: str):
        """Hiển thị dialog với nội dung prompt"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Prompt Content - {Path(file_path).name}")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"800x600+{x}+{y}")

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header_frame, text=f"📄 {Path(file_path).name}",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkLabel(header_frame, text=f"📁 {file_path}",
                    font=ctk.CTkFont(size=10)).pack(side="right")

        # Content frame
        content_frame = ctk.CTkFrame(dialog, fg_color="#2b2b2b")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Text widget with scrollbar
        text_widget = ctk.CTkTextbox(content_frame, font=ctk.CTkFont(family="Consolas", size=12))
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)

        # Insert content
        text_widget.insert("1.0", content)

        # Buttons frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def copy_content():
            dialog.clipboard_clear()
            dialog.clipboard_append(content)
            messagebox.showinfo("Copied", "Prompt content copied to clipboard!")

        def save_as():
            filename = filedialog.asksaveasfilename(
                title="Save Prompt As",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo("Saved", f"Prompt saved to:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save file:\n{str(e)}")

        # Buttons
        ctk.CTkButton(button_frame, text="📋 Copy", command=copy_content,
                     width=100).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="💾 Save As", command=save_as,
                     width=100).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="Close", command=dialog.destroy,
                     width=100).pack(side="right")

    def open_prompt_file(self):
        """Open prompt text file"""
        # License validation
        if not self.validate_license_for_operation():
            return

        file_path = filedialog.askopenfilename(
            title="Open Prompt File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Info", f"Prompt file selected: {file_path}")

    def select_prompt_file(self):
        """Select prompt from list"""
        # License validation
        if not self.validate_license_for_operation():
            return

        messagebox.showinfo("Info", "Select from predefined prompts")

    def select_image_folder(self):
        """Select from predefined image folders"""
        # License validation
        if not self.validate_license_for_operation():
            return

        messagebox.showinfo("Info", "Select from predefined image folders")

    def select_download_folder(self):
        """Select from predefined download folders or set default"""
        # License validation
        if not self.validate_license_for_operation():
            return

        # Provide some common download folder options
        import platform
        system = platform.system()

        common_folders = []
        if system == "Windows":
            common_folders = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Desktop/Videos"),
                "D:/Videos",
                "E:/Videos"
            ]
        else:
            common_folders = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Desktop/Videos")
            ]

        # Add app-specific folders using new method
        suggested_folders = self.get_suggested_download_folders()
        
        # Merge with common folders (remove duplicates)
        all_folders = common_folders + suggested_folders
        existing_folders = []
        seen = set()
        for folder in all_folders:
            if folder not in seen and os.path.exists(folder):
                existing_folders.append(folder)
                seen.add(folder)

        if existing_folders:
            # Show selection dialog
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Select Download Folder")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()

            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")

            selected_folder = [None]

            ctk.CTkLabel(dialog, text="Select Download Folder for Videos:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))

            # Scrollable frame for folders
            scrollable = ctk.CTkScrollableFrame(dialog, height=250)
            scrollable.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            def select_folder(folder):
                selected_folder[0] = folder
                dialog.destroy()

            # Add folder buttons
            for folder in existing_folders:
                btn = ctk.CTkButton(scrollable, text=f"📁 {folder}",
                                  command=lambda f=folder: select_folder(f),
                                  anchor="w", height=35)
                btn.pack(fill="x", pady=2)

            # Buttons
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=(0, 20))

            ctk.CTkButton(btn_frame, text="Browse...",
                         command=lambda: [dialog.destroy(), self.browse_download_folder()]).pack(side="left")
            ctk.CTkButton(btn_frame, text="Cancel",
                         command=dialog.destroy).pack(side="right")

            dialog.wait_window()

            if selected_folder[0]:
                self.download_folder.delete(0, "end")
                self.download_folder.insert(0, selected_folder[0])
        else:
            # No existing folders, just browse
            self.browse_download_folder()

    def show_input_dialog(self, title, message):
        """Hiển thị dialog nhập text ở giữa màn hình tool"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog on main window
        dialog.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        dialog_width = 400
        dialog_height = 200

        x = main_x + (main_width // 2) - (dialog_width // 2)
        y = main_y + (main_height // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Result variable
        result = [None]

        # Dialog content
        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(dialog, text=message, font=("Arial", 12)).pack(pady=(0, 15))

        # Entry field
        entry = ctk.CTkEntry(dialog, width=300, height=35, placeholder_text="Nhập tên workflow hoặc profile...")
        entry.pack(pady=(0, 20))
        entry.focus()

        # Buttons frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20)

        def on_ok():
            result[0] = entry.get().strip()
            dialog.destroy()

        def on_cancel():
            result[0] = None
            dialog.destroy()

        def on_enter(event):
            on_ok()

        # Bind Enter key
        entry.bind('<Return>', on_enter)

        ctk.CTkButton(button_frame, text="Cancel", width=80, height=30,
                     fg_color="#6c757d", hover_color="#5a6268", command=on_cancel).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="OK", width=80, height=30,
                     fg_color="#28a745", hover_color="#218838", command=on_ok).pack(side="right")

        # Wait for dialog to close
        dialog.wait_window()
        return result[0]

    def get_default_output_paths(self):
        """🎯 Get default paths using ResourceManager for EXE compatibility"""
        try:
            from utils.resource_manager import resource_manager
            
            # Use ResourceManager for proper paths
            base_output = resource_manager.get_output_path()
            
            paths = {
                'videos': os.path.join(base_output, 'videos'),
                'prompts': os.path.join(base_output, 'prompts'), 
                'downloads': os.path.join(base_output, 'downloads')
            }
            
            # Ensure directories exist
            for path in paths.values():
                os.makedirs(path, exist_ok=True)
                
            return paths
            
        except ImportError:
            # Fallback to current directory if ResourceManager not available
            base_dir = os.getcwd()
            paths = {
                'videos': os.path.join(base_dir, 'videos'),
                'prompts': os.path.join(base_dir, 'output'),
                'downloads': os.path.join(base_dir, 'downloads')
            }
            
            # Ensure directories exist
            for path in paths.values():
                os.makedirs(path, exist_ok=True)
                
            return paths

    def get_suggested_download_folders(self):
        """🎯 Get suggested download folders with proper paths"""
        # Get default paths first
        default_paths = self.get_default_output_paths()
        
        system = platform.system()
        suggested_folders = []
        
        if system == "Windows":
            suggested_folders = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Desktop/Videos"),
                "D:/Videos",
                "E:/Videos"
            ]
        else:
            suggested_folders = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Desktop/Videos")
            ]

        # Add app-specific folders from ResourceManager
        suggested_folders.extend([
            default_paths['videos'],    # Primary default
            default_paths['downloads'], # Secondary default  
            default_paths['prompts']    # For completeness
        ])

        # Filter existing folders and remove duplicates
        existing_folders = []
        seen = set()
        for folder in suggested_folders:
            if folder not in seen and os.path.exists(folder):
                existing_folders.append(folder)
                seen.add(folder)
                
        return existing_folders

    def new_workflow(self):
        """Tạo workflow mới với dialog nhập tên"""
        # License validation
        if not self.validate_license_for_operation():
            return

        # Create custom dialog centered on main window
        workflow_name = self.show_input_dialog("New Workflow", "Enter new workflow name:")

        if workflow_name and workflow_name.strip():
            workflow_name = workflow_name.strip()

            # Check if workflow name already exists
            existing_names = [w['name'] for w in self.workflows]
            if workflow_name in existing_names:
                messagebox.showerror("Error", f"Workflow '{workflow_name}' already exists!")
                return

            # 🎯 VALIDATE DROPDOWN VALUES trước khi tạo workflow
            self.validate_dropdown_values()

            # Clear current workflow
            self.current_workflow = None
            self.workflow_name.delete(0, "end")
            self.workflow_name.insert(0, workflow_name)
            self.content_text.delete("1.0", "end")
            self.chatgpt_link.delete(0, "end")

            # Set dropdown values explicitly
            self.chatgpt_gemini_api_var.set("Gemini API")
            self.chatgpt_api_combo.set("Gemini API")

            self.veo_link.delete(0, "end")
            self.image_folder.delete(0, "end")
            self.download_folder.delete(0, "end")

            # 🎯 USE RESOURCEMANAGER FOR PROPER PATHS
            default_paths = self.get_default_output_paths()
            self.download_folder.insert(0, default_paths['videos'])

            # Set dropdown values explicitly
            self.type_var.set("Text to Video")
            self.type_combo.set("Text to Video")

            # ⭐ NEW: Set Veo profile - ALWAYS EMPTY FOR USER TO CHOOSE
            # Only populate dropdown when creating new workflow, but keep selection empty
            available_profiles = self.get_veo_profiles_list()
            self.veo_profile_combo.configure(values=available_profiles)

            # Always set to empty for user to manually choose
            self.veo_profile_var.set("")
            self.veo_profile_combo.set("")

            # Set default values when creating new workflow
            self.video_count_var.set("1")
            self.video_count_combo.set("1")

            self.aspect_ratio_var.set("16:9 (Khổ ngang)")
            self.aspect_ratio_combo.set("16:9 (Khổ ngang)")

            self.model_var.set("Veo 3 Fast")
            self.model_combo.set("Veo 3 Fast")

            self.video_duration.delete(0, "end")
            self.video_duration.insert(0, "30")

            # Force UI update
            self.root.update_idletasks()

            # Create new workflow data with proper paths
            default_paths = self.get_default_output_paths()
            workflow_data = {
                'name': workflow_name,
                'content': '',
                'chatgpt_link': '',
                'chatgpt_gemini_api': 'Gemini API',
                'veo_link': '',
                'image_folder': '',
                'download_folder': default_paths['videos'],  # 🎯 PROPER PATH FROM RESOURCEMANAGER
                'type': 'Text to Video',
                'veo_profile': '',  # ⭐ NEW: Always empty for user to choose manually
                'video_count': '1',
                'aspect_ratio': '16:9 (Khổ ngang)',
                'model': 'Veo 3 Fast',
                'duration': 30,
                'created_at': datetime.datetime.now().isoformat()
            }

            # Add to workflows list
            self.workflows.append(workflow_data)
            self.current_workflow = len(self.workflows) - 1

            # Save individual workflow file (kingkong.json)
            self.save_individual_workflow(workflow_data)

            # Save main workflows file
            self.save_workflows_to_file()

            # Refresh workflow list
            self.refresh_workflow_list()

            # Clear selection and select new workflow
            for i, btn in enumerate(self.workflow_buttons):
                if i == self.current_workflow:
                    btn.configure(fg_color="#ff8c00")  # Orange for selected
                else:
                    btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))

            self.status_var.set(f"New workflow '{workflow_name}' created successfully")
        else:
            messagebox.showwarning("Warning", "Workflow name cannot be empty!")

    def validate_dropdown_values(self):
        """🎯 Validate và fix dropdown values để đảm bảo automation hoạt động"""
        # Validate Model dropdown
        current_model = self.model_var.get()
        valid_models = ["Veo 3 Quality", "Veo 3 Fast", "Veo 2 Quality", "Veo 2 Fast"]

        if not current_model or current_model not in valid_models:
            self.model_var.set("Veo 3 Fast")
            self.model_combo.set("Veo 3 Fast")

        # Validate Video Count dropdown
        current_count = self.video_count_var.get()
        valid_counts = ["1", "2", "3", "4"]

        if not current_count or current_count not in valid_counts:
            self.video_count_var.set("1")
            self.video_count_combo.set("1")

        # Validate Type dropdown
        current_type = self.type_var.get()
        valid_types = ["Text to Video", "Image to Video"]

        if not current_type or current_type not in valid_types:
            self.type_var.set("Text to Video")
            self.type_combo.set("Text to Video")

        # Update UI to show corrected values
        self.root.update_idletasks()

    def save_individual_workflow(self, workflow_data):
        """Lưu workflow riêng lẻ dưới dạng file JSON"""
        try:
            # Create workflows directory if not exists
            workflows_dir = Path('data/workflows')
            workflows_dir.mkdir(parents=True, exist_ok=True)

            # Create filename (e.g., kingkong.json)
            filename = f"{workflow_data['name'].lower().replace(' ', '_')}.json"
            filepath = workflows_dir / filename

            # Save workflow to individual file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)

            print(f"Workflow saved to: {filepath}")

        except Exception as e:
            print(f"Failed to save individual workflow: {e}")
            messagebox.showerror("Error", f"Failed to save workflow file: {e}")

    def save_workflow(self):
        """Lưu workflow hiện tại"""
        # 🔒 VALIDATE LICENSE BEFORE SAVING WORKFLOW
        if not self.validate_license_for_operation("saving workflow"):
            return

        name = self.workflow_name.get().strip()
        if not name or name == "(No workflow selected)":
            messagebox.showerror("Error", "Please enter a workflow name")
            return

        workflow_data = {
            'name': name,
            'content': self.content_text.get("1.0", "end").strip(),
            'chatgpt_link': self.chatgpt_link.get().strip(),
            'chatgpt_gemini_api': self.chatgpt_gemini_api_var.get(),
            'veo_link': self.veo_link.get().strip(),
            'image_folder': self.image_folder.get().strip(),
            'download_folder': self.download_folder.get().strip(),
            'type': self.type_var.get(),
            'veo_profile': self.veo_profile_var.get(),
            'video_count': self.video_count_var.get(),
            'aspect_ratio': self.aspect_ratio_var.get(),
            'model': self.model_var.get(),
            'duration': int(self.video_duration.get() or 30),
            'created_at': datetime.datetime.now().isoformat()
        }

        # Update or add workflow
        if self.current_workflow is not None:
            self.workflows[self.current_workflow] = workflow_data
        else:
            self.workflows.append(workflow_data)

        # Save individual workflow file
        self.save_individual_workflow(workflow_data)

        # Save main workflows file
        self.save_workflows_to_file()
        self.refresh_workflow_list()
        self.status_var.set(f"Workflow '{name}' saved successfully")

    def delete_workflow(self):
        """Xóa workflow hiện tại"""
        # License validation
        if not self.validate_license_for_operation():
            return

        if self.current_workflow is not None:
            workflow_name = self.workflows[self.current_workflow]['name']
            if messagebox.askyesno("Confirm Delete", f"Delete workflow '{workflow_name}'?"):
                del self.workflows[self.current_workflow]
                self.save_workflows_to_file()
                self.refresh_workflow_list()
                self.new_workflow()

                # ⭐ NEW: Clear Veo Profile dropdown when no workflow selected
                if not self.workflows:  # No workflows left
                    self.clear_veo_profile_dropdown()

                self.status_var.set(f"Workflow '{workflow_name}' deleted")

    def start_generation(self):
        """🎯 SMART START: Tự động quyết định mode dựa vào Veo Profile với validation"""
        # License validation
        if not self.validate_license_for_operation():
            return

        content = self.content_text.get("1.0", "end").strip()
        if not content:
            # 🎯 AUTO-SET default content instead of error
            default_content = "Create a beautiful video about nature and landscapes with cinematic quality"
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", default_content)
            content = default_content
            self.status_var.set("✅ Auto-set default script content")

        # 🎯 VALIDATE DROPDOWN VALUES trước khi start
        self.validate_dropdown_values()

        # 🔥 VALIDATION: Bắt buộc phải save workflow trước
        if self.current_workflow is None:
            # 🎯 AUTO-SAVE: Tự động save workflow thay vì show error
            self.status_var.set("⚡ Auto-saving workflow before start...")
            try:
                self.save_workflow()
                self.status_var.set("✅ Workflow auto-saved successfully")
            except Exception as e:
                # If auto-save fails, continue anyway but warn user
                self.status_var.set(f"⚠️ Auto-save failed, continuing anyway: {e}")
                # Don't return - continue with generation

        # 🔥 VALIDATION: Kiểm tra download folder
        download_folder = self.download_folder.get().strip()
        if not download_folder:
            # 🎯 AUTO-SET default download folder
            default_download = os.path.join(os.getcwd(), "videos")
            self.download_folder.delete(0, "end")
            self.download_folder.insert(0, default_download)
            download_folder = default_download
            self.status_var.set(f"✅ Auto-set download folder: {default_download}")

        if not os.path.exists(download_folder):
            # 🎯 AUTO-CREATE folder instead of asking
            try:
                os.makedirs(download_folder, exist_ok=True)
                self.status_var.set(f"✅ Created download folder: {download_folder}")
            except Exception as e:
                self.status_var.set(f"⚠️ Cannot create download folder: {e}")
                # Continue anyway

        # 🔥 VALIDATION: Kiểm tra workflow name để tạo subfolder
        workflow_name = self.workflow_name.get().strip()
        if not workflow_name or workflow_name == "(No workflow selected)":
            # 🎯 SILENT AUTO-GENERATION: No dialog, just auto-create name
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_workflow_name = f"video_project_{timestamp}"

            # Set auto-generated name silently
            self.workflow_name.delete(0, "end")
            self.workflow_name.insert(0, auto_workflow_name)
            workflow_name = auto_workflow_name

            # Update status instead of showing dialog
            self.status_var.set(f"✅ Auto-generated workflow: {auto_workflow_name}")

            # Optional: Auto-save the workflow with generated name
            try:
                self.save_workflow()
            except:
                pass  # Continue if save fails

        # Disable start button và bắt đầu generation
        self.start_btn.configure(state="disabled")
        self.status_var.set("Starting video generation...")

        # Run in separate thread - logic thông minh sẽ được xử lý trong run_video_generation
        thread = threading.Thread(target=self.run_video_generation, args=(content,))
        thread.daemon = True
        thread.start()

    def start_all_workflows(self):
        """Start all workflows in sequence"""
        # 🔒 VALIDATE LICENSE BEFORE STARTING WORKFLOWS
        if not self.validate_license_for_operation("starting workflows"):
            return

        if not self.workflows:
            messagebox.showwarning("Warning", "No workflows available to start")
            return

        self.start_all_btn.configure(state="disabled")
        self.status_var.set("Starting all workflows...")

        # TODO: Implement batch processing of all workflows
        messagebox.showinfo("Info", f"Starting {len(self.workflows)} workflows...")



        self.start_all_btn.configure(state="normal")
        self.status_var.set("All workflows completed")

    def move_workflow_up(self):
        """Di chuyển workflow được chọn lên trên"""
        # License validation
        if not self.validate_license_for_operation():
            return

        if self.current_workflow is not None and self.current_workflow > 0:
            # Swap workflows
            self.workflows[self.current_workflow], self.workflows[self.current_workflow - 1] = \
                self.workflows[self.current_workflow - 1], self.workflows[self.current_workflow]

            # Update current selection
            self.current_workflow -= 1

            # Refresh UI
            self.save_workflows_to_file()
            self.refresh_workflow_list()
            self.status_var.set("Workflow moved up")

    def move_workflow_down(self):
        """Di chuyển workflow được chọn xuống dưới"""
        # License validation
        if not self.validate_license_for_operation():
            return

        if self.current_workflow is not None and self.current_workflow < len(self.workflows) - 1:
            # Swap workflows
            self.workflows[self.current_workflow], self.workflows[self.current_workflow + 1] = \
                self.workflows[self.current_workflow + 1], self.workflows[self.current_workflow]

            # Update current selection
            self.current_workflow += 1

            # Refresh UI
            self.save_workflows_to_file()
            self.refresh_workflow_list()
            self.status_var.set("Workflow moved down")

    def run_video_generation(self, content: str):
        """🎯 SMART START: Tạo prompts + Tự động upload lên Veo 3 (nếu có profile)"""
        # 🔒 VALIDATE LICENSE BEFORE VIDEO GENERATION
        if not self.validate_license_for_operation("video generation"):
            return

        try:
            # Check if content generator is available
            if not self.content_generator:
                # 🎯 CONTINUE with warning instead of error
                self.root.after(0, lambda: self.status_var.set("⚠️ Content generator not initialized - using basic mode"))
                # Don't return - continue with basic functionality

            # Get selected provider and type
            api_selection = self.chatgpt_gemini_api_var.get()
            if not api_selection or api_selection not in ["Gemini API", "ChatGPT"]:
                # 🎯 AUTO-SET default API provider
                self.chatgpt_gemini_api_var.set("Gemini API")
                self.chatgpt_api_combo.set("Gemini API")
                api_selection = "Gemini API"
                self.root.after(0, lambda: self.status_var.set("✅ Auto-set API provider: Gemini API"))

            provider = 'gemini' if api_selection == 'Gemini API' else 'chatgpt'
            generation_type = self.type_var.get()
            model_selection = self.model_var.get()

            # Basic validation (should not happen with defaults but safety check)
            if not generation_type:
                generation_type = "Text to Video"
                self.type_var.set(generation_type)

            if not model_selection:
                model_selection = "Veo 3 Fast"
                self.model_var.set(model_selection)

            # Check if provider is available
            if not self.content_generator.is_provider_available(provider):
                # 🎯 CONTINUE with warning instead of stopping
                self.root.after(0, lambda: self.status_var.set(f"⚠️ {provider.upper()} API not configured - continuing with limited features"))
                # Don't return - continue anyway

            # 🎯 SMART LOGIC: Check Veo Profile để quyết định mode
            selected_veo_profile = self.veo_profile_var.get()
            veo_profile_available = selected_veo_profile and selected_veo_profile != "Select Profile..."
            cookies_available = False

            if veo_profile_available:
                # 🎯 Use ResourceManager for consistent path (exe compatibility)
                try:
                    from utils.resource_manager import resource_manager
                    cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
                    cookies_file = cookies_dir / f"{selected_veo_profile}.json"
                except ImportError:
                    # Fallback to relative path
                    cookies_file = Path(f"data/profile_cookies/{selected_veo_profile}.json")
                
                cookies_available = cookies_file.exists()
                print(f"🔍 DEBUG: Checking cookies at: {cookies_file} - Exists: {cookies_available}")

            # 🎯 ENHANCED MODE DETERMINATION - 3 modes thay vì 2
            if veo_profile_available and cookies_available:
                mode = "FULL_AUTOMATION"  # Tạo prompts + Upload lên Veo 3 tự động
                automation_info = f"Model: {self.model_var.get()}, Count: {self.video_count_var.get()}"
                self.root.after(0, lambda: self.status_var.set(f"🚀 SMART MODE: FULL AUTOMATION - {automation_info} - Profile: {selected_veo_profile}"))
            elif veo_profile_available and not cookies_available:
                mode = "PROMPT_WITH_CHROME"  # Tạo prompts + Mở Chrome cho user manual upload
                self.root.after(0, lambda: self.status_var.set(f"🤖 SMART MODE: PROMPT + CHROME - Profile '{selected_veo_profile}' needs login"))
            else:
                mode = "PROMPT_ONLY"  # Chỉ tạo prompts từ AI
                self.root.after(0, lambda: self.status_var.set("🤖 SMART MODE: PROMPT ONLY - No Veo profile selected"))

            # ===== PHASE 1: ALWAYS CREATE PROMPTS FROM AI =====

            # Handle different generation types
            if generation_type == "Text to Video":
                # Step 1: Enhance script with AI
                self.root.after(0, lambda: self.status_var.set(f"[{mode}] Enhancing script with AI..."))

                enhanced_result = self.content_generator.enhance_script(
                    script=content,
                    provider=provider,
                    style='professional'
                )

                if enhanced_result.get('status') != 'success':
                    error_msg = enhanced_result.get('error_message', 'Failed to enhance script')
                    self.root.after(0, self.on_generation_error, f"Script enhancement failed: {error_msg}")
                    return

                enhanced_script = enhanced_result.get('enhanced_script', content)

                # Step 2: Generate video prompts
                self.root.after(0, lambda: self.status_var.set(f"[{mode}] Generating video prompts..."))

                prompts_result = self.content_generator.generate_video_prompts(
                    script=enhanced_script,
                    provider=provider,
                    style='cinematic'
                )

                if prompts_result.get('status') != 'success':
                    error_msg = prompts_result.get('error_message', 'Failed to generate video prompts')
                    self.root.after(0, self.on_generation_error, f"Video prompt generation failed: {error_msg}")
                    return

                video_prompts = prompts_result.get('video_prompts', '')

            elif generation_type == "Image to Video":
                # For Image to Video, use content as image description and generate prompts
                self.root.after(0, lambda: self.status_var.set(f"[{mode}] Generating image-to-video prompts..."))

                # Use content as image description and enhance for video generation
                enhanced_result = self.content_generator.enhance_script(
                    script=f"Image Description: {content}\n\nCreate a video sequence that brings this image to life with natural movement and cinematic elements.",
                    provider=provider,
                    style='cinematic'
                )

                if enhanced_result.get('status') != 'success':
                    error_msg = enhanced_result.get('error_message', 'Failed to enhance image description')
                    self.root.after(0, self.on_generation_error, f"Image-to-video enhancement failed: {error_msg}")
                    return

                enhanced_script = enhanced_result.get('enhanced_script', content)

                # Generate video prompts based on image description
                prompts_result = self.content_generator.generate_video_prompts(
                    script=enhanced_script,
                    provider=provider,
                    style='cinematic'
                )

                if prompts_result.get('status') != 'success':
                    error_msg = prompts_result.get('error_message', 'Failed to generate video prompts')
                    self.root.after(0, self.on_generation_error, f"Video prompt generation failed: {error_msg}")
                    return

                video_prompts = prompts_result.get('video_prompts', '')

            else:
                self.root.after(0, self.on_generation_error, f"Unsupported generation type: {generation_type}")
                return

            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)

            # Save enhanced script and prompts to files
            timestamp = int(time.time())

            # 🎯 SMART FILE NAMING: 2 files rõ ràng với timestamp
            provider_name = 'geminiai' if provider == 'gemini' else 'chatgpt'

            if mode == "PROMPT_ONLY":
                # CHẾ ĐỘ CHỈ TẠO PROMPT: Tên file cơ bản (không có timestamp)
                script_file = f"output/{provider_name}_script.txt"
                prompts_file = f"output/{provider_name}_prompt.txt"
            else:
                # CHẾ ĐỘ FULL AUTOMATION: Tên file với timestamp để phân biệt rõ ràng
                from datetime import datetime
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
                script_file = f"output/{provider_name}_script_{time_str}.txt"
                prompts_file = f"output/{provider_name}_prompt_{time_str}.txt"

            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(f"Original Script:\n{content}\n\n")
                f.write(f"Enhanced Script:\n{enhanced_script}\n\n")
                f.write(f"Provider: {provider.upper()}")

            with open(prompts_file, 'w', encoding='utf-8') as f:
                f.write(video_prompts)

            # ===== PHASE 2: VEO AUTOMATION (if applicable) =====

            veo_automation_result = None

            if mode == "FULL_AUTOMATION":
                self.root.after(0, lambda: self.status_var.set(f"🚀 Starting Enhanced Veo 3 automation..."))

                try:
                    # Initialize thread-safe VeoWorkflowEngine
                    if not self.veo_engine:
                        self.veo_engine = VeoWorkflowEngine(self)
                    else:
                        # Reset video counter for new video generation session
                        self.veo_engine.reset_video_counter()

                    # Use context manager for Chrome session
                    with self.veo_engine.chrome_session(selected_veo_profile) as driver:
                        # Navigate to Veo
                        if not self.veo_engine.navigate_to_veo():
                            raise Exception("Failed to navigate to Veo")

                        # 🎯 ENHANCED: Read prompts from saved file instead of memory
                        self.root.after(0, lambda: self.status_var.set(f"📖 Reading prompts from saved file..."))

                        # Read prompts from the file we just created
                        parsed_prompts = self.read_prompts_from_file(prompts_file)

                        if parsed_prompts:
                            self.root.after(0, lambda: self.status_var.set(f"🎬 Starting BATCH processing with {len(parsed_prompts)} prompts..."))

                            # 🚀 BATCH PROCESSING: Process all prompts
                            veo_automation_result = self.run_batch_veo_workflow(parsed_prompts, selected_veo_profile)
                        else:
                            raise Exception("No valid prompts found in saved file")

                except Exception as veo_error:
                    # Veo automation failed, but we still have the prompts
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ Enhanced Veo automation failed, prompts saved"))
                    veo_automation_result = {
                        'success': False,
                        'error': f"Enhanced Veo automation error: {str(veo_error)}",
                        'videos_created': 0,
                        'method': 'VeoWorkflowEngine'
                    }

                finally:
                    # Cleanup
                    if self.veo_engine:
                        self.veo_engine.cleanup()
                        self.veo_engine = None

            elif mode == "PROMPT_WITH_CHROME":
                # 🎯 NEW MODE: Tạo prompts + Mở Chrome cho user manual upload
                self.root.after(0, lambda: self.status_var.set(f"🌐 Opening Chrome with profile for manual video creation..."))

                try:
                    # 🎯 EXE COMPATIBILITY: Use profile manager's launch method instead of webdriver directly
                    print(f"🚀 Launching Chrome with profile: {selected_veo_profile}")
                    
                    # Use profile manager to launch Chrome (handles exe mode properly)
                    process = self.profile_manager.launch_chrome_with_profile(
                        selected_veo_profile, 
                        open_veo_login=True,  # Auto open Veo URL
                        use_cdp=False  # Don't use CDP for manual mode
                    )
                    
                    if process:
                        self.root.after(0, lambda: self.status_var.set(f"✅ Chrome opened with profile '{selected_veo_profile}' - Please create videos manually"))
                        
                        veo_automation_result = {
                            'success': True,
                            'chrome_opened': True,
                            'manual_mode': True,
                            'message': f'Chrome opened with profile {selected_veo_profile} for manual video creation',
                            'videos_created': 0,  # User will create manually
                            'method': 'ProfileManager'
                        }
                    else:
                        raise Exception("Failed to launch Chrome process")

                except Exception as chrome_error:
                    print(f"❌ Chrome launch error: {chrome_error}")
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ Failed to open Chrome, prompts saved for manual use"))
                    veo_automation_result = {
                        'success': False,
                        'error': f"Chrome opening error: {str(chrome_error)}",
                        'videos_created': 0,
                        'method': 'ProfileManager'
                    }

            # ===== RESULT COMPILATION =====

            # Prepare result based on mode
            result = {
                'success': True,
                'mode': mode,
                'script_file': script_file,
                'prompts_file': prompts_file,
                'provider': provider.upper(),
                'generation_type': generation_type,
                'enhanced_script': enhanced_script,
                'video_prompts': video_prompts,
                'model_selection': model_selection,
                'timestamp': timestamp,
                'veo_profile': {
                    'profile_name': selected_veo_profile if veo_profile_available else None,
                    'cookies_available': cookies_available,
                    'ready_for_automation': veo_profile_available and cookies_available
                },
                'veo_automation': veo_automation_result  # Can be None if PROMPT_ONLY mode
            }

            # Update UI in main thread
            self.root.after(0, self.on_generation_complete, result)

        except Exception as e:
            self.root.after(0, self.on_generation_error, str(e))

    def on_generation_complete(self, result):
        """🎯 SMART CALLBACK: Xử lý kết quả cho cả 2 modes"""
        self.start_btn.configure(state="normal")

        if result.get('success'):
            mode = result.get('mode', 'UNKNOWN')
            provider = result.get('provider', 'AI')
            generation_type = result.get('generation_type', 'Text to Video')
            script_file = result.get('script_file', '')
            prompts_file = result.get('prompts_file', '')
            veo_profile = result.get('veo_profile', {})
            model_selection = result.get('model_selection', 'Unknown')
            veo_automation = result.get('veo_automation')

            # Build success message based on mode
            if mode == "PROMPT_ONLY":
                # Only set status, no need for detailed message
                self.status_var.set(f"✅ Prompts generated using {provider}")

            elif mode == "PROMPT_WITH_CHROME":
                # New mode: Prompts created + Chrome opened
                if veo_automation and veo_automation.get('success'):
                    self.status_var.set(f"✅ Chrome opened for manual video creation")
                else:
                    self.status_var.set(f"✅ Prompts generated, Chrome opening failed")

            elif mode == "FULL_AUTOMATION":
                # Only set status, no need for detailed message
                if veo_automation and veo_automation.get('success'):
                    videos_created = veo_automation.get('videos_created', 0)
                    if videos_created > 0:
                        self.status_var.set(f"🚀 Full automation completed - {videos_created} videos created")
                    else:
                        self.status_var.set(f"⚠️ Automation completed but no videos created")
                else:
                    self.status_var.set(f"⚠️ Veo automation failed, prompts saved")
            else:
                self.status_var.set("Generation completed")

            # Show simple completion message instead of detailed dialog
            if mode == "FULL_AUTOMATION":
                if veo_automation and veo_automation.get('success'):
                    videos_created = veo_automation.get('videos_created', 0)
                    if videos_created > 0:
                        # 🎉 SIMPLE SUCCESS MESSAGE
                        messagebox.showinfo("Hoàn Tất", f"✅ Tạo video thành công!\n\n🎬 Đã tạo: {videos_created} video(s)\n\n🎯 Kiểm tra Google Veo để xem kết quả")
                        self.status_var.set(f"🚀 Hoàn tất - Đã tạo {videos_created} video(s)")
                    else:
                        messagebox.showinfo("Hoàn Tất", "⚠️ Quá trình hoàn tất nhưng không tạo được video nào\n\n💡 Kiểm tra Google Veo dashboard")
                        self.status_var.set("⚠️ Hoàn tất - Không tạo được video")
                else:
                    messagebox.showinfo("Hoàn Tất", "⚠️ Automation gặp lỗi\n\n💡 Prompts đã được lưu, có thể dùng thủ công")
                    self.status_var.set("⚠️ Hoàn tất với lỗi")

            elif mode == "PROMPT_WITH_CHROME":
                # New mode: Prompts + Chrome opened for manual use
                if veo_automation and veo_automation.get('success') and veo_automation.get('chrome_opened'):
                    messagebox.showinfo("Hoàn Tất",
                        f"✅ Tạo prompt thành công!\n\n"
                        f"🌐 Chrome đã mở với profile: {veo_profile.get('profile_name', 'Unknown')}\n\n"
                        f"📝 Prompts đã lưu vào: {prompts_file}\n\n"
                        f"🎬 Vui lòng đăng nhập Google Veo và tạo video thủ công")
                    self.status_var.set("✅ Hoàn tất - Chrome đã mở để tạo video thủ công")
                else:
                    messagebox.showinfo("Hoàn Tất",
                        f"✅ Tạo prompt thành công!\n\n"
                        f"⚠️ Không thể mở Chrome tự động\n\n"
                        f"📝 Prompts đã lưu vào: {prompts_file}\n\n"
                        f"💡 Vui lòng mở Chrome thủ công và sử dụng prompts")
                    self.status_var.set("✅ Hoàn tất - Prompts đã tạo")

            else:
                # PROMPT_ONLY mode
                messagebox.showinfo("Hoàn Tất", "✅ Tạo prompt thành công!\n\n📝 Các file đã được lưu vào thư mục output")
                self.status_var.set("✅ Hoàn tất - Prompts đã tạo")

        else:
            error_msg = result.get('error', 'Unknown error')
            messagebox.showerror("Lỗi", f"❌ Quá trình tạo video gặp lỗi\n\n{error_msg}")
            self.status_var.set("Generation failed")

    def on_generation_error(self, error_msg):
        """Callback khi có lỗi"""
        self.start_btn.configure(state="normal")
        self.status_var.set(f"Error: {error_msg}")
        messagebox.showerror("Lỗi", f"❌ {error_msg}")

    def stop_generation(self):
        """Dừng quá trình tạo video"""
        self.status_var.set("Generation stopped by user")

    def on_workflow_select(self, index):
        """Khi chọn workflow từ list"""
        self.current_workflow = index
        workflow = self.workflows[index]

        # Load workflow data
        self.workflow_name.delete(0, "end")
        self.workflow_name.insert(0, workflow['name'])

        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", workflow.get('content', ''))

        self.chatgpt_link.delete(0, "end")
        self.chatgpt_link.insert(0, workflow.get('chatgpt_link', ''))

        # Set dropdown values explicitly with both variable and widget
        api_value = workflow.get('chatgpt_gemini_api', 'Gemini API')
        # Fix invalid values from old workflows
        if api_value not in ["Gemini API", "ChatGPT"]:
            api_value = "Gemini API"
        self.chatgpt_gemini_api_var.set(api_value)
        self.chatgpt_api_combo.set(api_value)

        self.veo_link.delete(0, "end")
        self.veo_link.insert(0, workflow.get('veo_link', ''))

        self.image_folder.delete(0, "end")
        self.image_folder.insert(0, workflow.get('image_folder', ''))

        self.download_folder.delete(0, "end")
        self.download_folder.insert(0, workflow.get('download_folder', ''))

        # Set dropdown values explicitly with both variable and widget
        type_value = workflow.get('type', 'Text to Video')
        # Fix invalid values from old workflows
        if type_value not in ["Text to Video", "Image to Video"]:
            type_value = "Text to Video"
        self.type_var.set(type_value)
        self.type_combo.set(type_value)

        # ⭐ NEW: Handle Veo Profile selection - ALWAYS SHOW EMPTY FOR USER TO CHOOSE
        # Only populate dropdown when workflow is selected, but keep selection empty
        available_profiles = self.get_veo_profiles_list()
        self.veo_profile_combo.configure(values=available_profiles)

        # Always set to empty for user to manually choose
        self.veo_profile_var.set("")
        self.veo_profile_combo.set("")

        self.video_count_var.set(workflow.get('video_count', '1'))
        self.aspect_ratio_var.set(workflow.get('aspect_ratio', '16:9 (Khổ ngang)'))

        # Set dropdown values explicitly with both variable and widget
        model_value = workflow.get('model', 'Veo 3 Fast')
        # Fix invalid values from old workflows
        if model_value not in ["Veo 3 Quality", "Veo 3 Fast", "Veo 2 Quality", "Veo 2 Fast"]:
            model_value = "Veo 3 Fast"
        self.model_var.set(model_value)
        self.model_combo.set(model_value)

        self.video_duration.delete(0, "end")
        self.video_duration.insert(0, str(workflow.get('duration', 30)))

        # Force UI update to ensure dropdowns show correct values
        self.root.update_idletasks()

        # Update workflow data with corrected values and save
        workflow['chatgpt_gemini_api'] = api_value
        workflow['type'] = type_value
        workflow['model'] = model_value
        # Don't auto-save veo_profile - let user choose manually
        self.save_individual_workflow(workflow)

        # Update button selection
        for i, btn in enumerate(self.workflow_buttons):
            if i == index:
                btn.configure(fg_color="#ff8c00")  # Orange for selected
            else:
                btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))  # Default blue

    def refresh_workflow_list(self):
        """Refresh danh sách workflow"""
        # Clear existing buttons
        for btn in self.workflow_buttons:
            btn.destroy()
        self.workflow_buttons.clear()

        # Create new buttons
        for i, workflow in enumerate(self.workflows):
            # Set color based on selection
            if i == self.current_workflow:
                fg_color = "#ff8c00"  # Orange for selected
                hover_color = "#e67e00"
            else:
                fg_color = "#404040"  # Default
                hover_color = "#505050"

            # Create filename for display (e.g., kingkong.json)
            filename = f"{workflow['name'].lower().replace(' ', '_')}.json"

            btn = ctk.CTkButton(
                self.workflow_scrollable,
                text=f"{i+1}. {filename}",
                width=240,
                height=25,
                anchor="w",
                font=("Arial", 10),
                fg_color=fg_color,
                hover_color=hover_color,
                command=lambda idx=i: self.on_workflow_select(idx)
            )
            btn.pack(fill="x", pady=1)
            self.workflow_buttons.append(btn)

    def load_workflows(self):
        """Load workflows từ file"""
        workflows_file = Path('data/workflows.json')
        if workflows_file.exists():
            try:
                with open(workflows_file, 'r', encoding='utf-8') as f:
                    self.workflows = json.load(f)
                self.refresh_workflow_list()
            except Exception as e:
                print(f"Failed to load workflows: {e}")

    def save_workflows_to_file(self):
        """Lưu workflows vào file"""
        workflows_file = Path('data/workflows.json')
        workflows_file.parent.mkdir(exist_ok=True)

        try:
            with open(workflows_file, 'w', encoding='utf-8') as f:
                json.dump(self.workflows, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save workflows: {e}")

    def run(self):
        """Chạy ứng dụng"""
        # Check license và hiển thị dialog nếu cần TRƯỚC KHI tạo GUI
        while True:
            try:
                is_valid, message = self.check_license_and_hardware()

                if not is_valid:
                    print(f"License check failed: {message}")
                    # Show license dialog - returns True if activated, False if exit
                    if not self.show_license_dialog_with_hardware():
                        # User chose to exit
                        return
                    # Continue loop to recheck license
                    continue
                else:
                    print("License valid - starting application")
                    break

            except Exception as e:
                print(f"License check error: {e}")
                if not self.show_license_dialog_with_hardware():
                    return
                continue

        # License is valid, NOW create and show GUI
        if not self.gui_created:
            try:
                print("🎨 Creating GUI widgets...")
                self.create_widgets()
                print("✅ GUI widgets created")

                print("📚 Loading workflows...")
                self.load_workflows()
                print("✅ Workflows loaded")

                print("⚙️ Loading settings...")
                self.load_settings()
                print("✅ Settings loaded")

                print("🤖 Initializing content generator...")
                self.initialize_content_generator()
                print("✅ Content generator initialized")

                print("👤 Refreshing profile list...")
                self.refresh_profile_list()
                print("✅ Profile list refreshed")

                # Setup license expiry monitoring AFTER GUI is created
                print("🔔 Setting up license expiry monitoring...")
                self.setup_license_expiry_monitoring()
                print("✅ License expiry monitoring started")

                # 🔒 Initialize Status Manager sau khi có GUI
                print("📊 Starting status manager...")
                self.status_manager = StatusManager(self)
                self.status_manager.start()
                print("✅ Status manager started")

                # Register cleanup on window close
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

                self.gui_created = True
                print("✅ GUI initialization completed!")

            except Exception as e:
                print(f"❌ Error creating GUI: {e}")
                import traceback
                traceback.print_exc()
                return

        # Show the main window
        print("🖼️ Showing main window...")
        print(f"🔍 Before deiconify - Window state: {self.root.state()}")

        # Ensure window is ready before showing
        self.root.update_idletasks()

        # Force show window with multiple attempts if needed
        for attempt in range(3):
            try:
                # Use more robust approach for CustomTkinter
                if attempt == 0:
                    # First attempt - standard deiconify
                    self.root.deiconify()
                elif attempt == 1:
                    # Second attempt - state change
                    self.root.state('normal')
                else:
                    # Third attempt - withdraw then deiconify
                    self.root.withdraw()
                    self.root.update_idletasks()
                    time.sleep(0.05)
                    self.root.deiconify()

                print(f"🔍 Attempt {attempt + 1} - Window state after operation: {self.root.state()}")

                # Verify window is actually shown
                self.root.update_idletasks()
                if self.root.state() == 'normal':
                    print(f"✅ Window successfully shown on attempt {attempt + 1}")
                    break
                else:
                    print(f"⚠️ Window still not normal, trying again...")
                    time.sleep(0.1)
            except Exception as e:
                print(f"❌ Show attempt {attempt + 1} failed: {e}")

        # Final check - if window still not shown, there's a serious issue
        if self.root.state() != 'normal':
            print(f"🚨 CRITICAL: Window failed to show after all attempts!")
            print(f"🔍 Final window state: {self.root.state()}")
            print(f"🔍 Window exists: {self.root.winfo_exists()}")

            # Last resort - try to recreate window visibility
            try:
                self.root.state('normal')
                self.root.update_idletasks()
                print(f"🔧 Emergency fix applied - Window state: {self.root.state()}")
            except Exception as e:
                print(f"❌ Emergency fix failed: {e}")

        # Force window to front and focus
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))

        # Ensure proper geometry
        self.root.update_idletasks()
        self.root.geometry("1200x800+100+100")  # Force position

        print("✅ Main window should be visible now!")
        print(f"🔍 Window state: {self.root.state()}")
        print(f"🔍 Window geometry: {self.root.geometry()}")
        print(f"🔍 Window winfo_viewable: {self.root.winfo_viewable()}")

        # Test window visibility with a delay
        print("⏰ Waiting 2 seconds to test window visibility...")
        self.root.after(2000, self.test_window_visibility)

        # Add additional window restoration after delay if needed
        self.root.after(3000, self.ensure_window_visible)

        # Start main application
        print("🚀 Starting main loop...")
        print(f"🧵 Current thread: {threading.current_thread().name}")
        print(f"🧵 Is main thread: {threading.current_thread() is threading.main_thread()}")

        # Add mainloop safety wrapper
        mainloop_started = False
        try:
            mainloop_started = True
            self.root.mainloop()
            print("🛑 Main loop ended normally")
        except KeyboardInterrupt:
            print("⌨️ KeyboardInterrupt caught - user terminated")
        except SystemExit as e:
            print(f"🚪 SystemExit caught: {e}")
        except Exception as e:
            print(f"❌ Exception in mainloop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if mainloop_started:
                print("🔚 Main loop cleanup...")
                # Ensure proper cleanup even if mainloop exits unexpectedly
                try:
                    if hasattr(self, 'status_manager') and self.status_manager:
                        self.status_manager.stop()
                except Exception as e:
                    print(f"⚠️ Cleanup warning: {e}")

        print("🔚 Application ending...")

    def test_window_visibility(self):
        """Test if window is still visible after delay"""
        try:
            print(f"🔍 Window still exists: {self.root.winfo_exists()}")
            print(f"🔍 Window viewable: {self.root.winfo_viewable()}")
            print(f"🔍 Window state: {self.root.state()}")
            print(f"🔍 Window mapped: {self.root.winfo_ismapped()}")

            # DO NOT try to restore window - this triggers CustomTkinter bug!
            # Just report the status for debugging
            if not self.root.winfo_viewable() or self.root.state() == 'withdrawn':
                print("⚠️ Window appears to be hidden - this may be normal CustomTkinter behavior")
                print("📝 Note: CustomTkinter sometimes hides window after initialization")
                # DO NOT call deiconify() here as it causes the window to close!
            else:
                print("✅ Window is visible and functioning normally")

        except Exception as e:
            print(f"❌ Window test failed: {e}")
            print("💀 Window appears to have been destroyed prematurely")

            # This might be the source of the issue - premature window destruction
            import traceback
            traceback.print_exc()

    def ensure_window_visible(self):
        """Ensure window is visible after CustomTkinter initialization quirks"""
        try:
            print("🔧 Ensuring window visibility...")

            # Check current state
            current_state = self.root.state()
            print(f"🔍 Current window state: {current_state}")

            # If window is withdrawn, show it properly
            if current_state == 'withdrawn':
                print("🔧 Window is withdrawn, attempting to show...")

                # Use a safer approach - update state directly
                try:
                    self.root.state('normal')
                    self.root.update_idletasks()
                    print(f"✅ Window state set to: {self.root.state()}")
                except Exception as e:
                    print(f"⚠️ Direct state change failed: {e}")

                    # Alternative approach - withdraw and deiconify cleanly
                    try:
                        self.root.withdraw()
                        self.root.update_idletasks()
                        time.sleep(0.1)
                        self.root.deiconify()
                        self.root.update_idletasks()
                        print(f"✅ Alternative restore completed: {self.root.state()}")
                    except Exception as e2:
                        print(f"❌ Alternative restore failed: {e2}")

                # Ensure window is visible and focused
                try:
                    self.root.lift()
                    self.root.focus_force()
                    self.root.attributes('-topmost', True)
                    self.root.after(100, lambda: self.root.attributes('-topmost', False))
                    print("✅ Window brought to front")
                except Exception as e:
                    print(f"⚠️ Window focus failed: {e}")
            else:
                print("✅ Window state is normal, no action needed")

        except Exception as e:
            print(f"❌ Window visibility check failed: {e}")
            import traceback
            traceback.print_exc()

    def run_batch_veo_workflow(self, parsed_prompts, profile_name):
        """🎬 BATCH PROCESSING: Process all prompts sequentially"""
        total_prompts = len(parsed_prompts)
        successful_videos = 0
        failed_prompts = []
        all_details = []

        # Reset video counter for new batch workflow
        if hasattr(self, 'veo_engine') and self.veo_engine:
            self.veo_engine.reset_video_counter()

        self.root.after(0, lambda: self.status_var.set(f"🚀 BATCH MODE: Processing {total_prompts} prompts..."))

        for i, prompt_obj in enumerate(parsed_prompts):
            current_prompt = prompt_obj['text']
            prompt_index = prompt_obj['index']

            self.root.after(0, lambda i=i, total=total_prompts, prompt=current_prompt:
                           self.status_var.set(f"🎬 Video {i+1}/{total}: {prompt[:60]}..."))

            try:
                # 🎯 SESSION RECOVERY: Check session before each prompt
                if not self.veo_engine.is_session_alive():
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ Session lost before prompt {i+1}, recovering..."))
                    if self.veo_engine.recover_session():
                        self.root.after(0, lambda: self.status_var.set(f"✅ Session recovered, continuing with prompt {i+1}"))
                        # After recovery, force full workflow to re-setup everything
                        time.sleep(3)  # Allow session to stabilize
                    else:
                        self.root.after(0, lambda: self.status_var.set(f"❌ Session recovery failed, stopping batch"))
                        break

                # Define progress callback for each prompt
                def progress_callback(step_info):
                    percentage = step_info.get('percentage', 0)
                    step_name = step_info.get('name', 'Processing')
                    self.root.after(0, lambda: self.status_var.set(f"🔄 [{i+1}/{total_prompts}] {step_name} ({percentage:.1f}%)"))

                if i == 0:
                    # First prompt: Run complete workflow (setup)
                    self.root.after(0, lambda: self.status_var.set(f"🔧 First prompt: Complete setup workflow..."))
                    success = self.veo_engine.run_basic_workflow(current_prompt, progress_callback)
                else:
                    # Subsequent prompts: Quick workflow (no setup)
                    self.root.after(0, lambda: self.status_var.set(f"⚡ Prompt {i+1}: Quick workflow..."))
                    success = self.veo_engine.run_quick_batch_workflow(current_prompt, progress_callback)

                # Track results
                if success:
                    successful_videos += 1
                    self.root.after(0, lambda i=i: self.status_var.set(f"✅ Video {i+1} completed successfully!"))
                else:
                    failed_prompts.append((prompt_index, current_prompt[:50]))
                    self.root.after(0, lambda i=i: self.status_var.set(f"❌ Video {i+1} failed!"))

                all_details.append({
                    'prompt': current_prompt,
                    'result': {'success': success},
                    'prompt_index': prompt_index
                })

                # Brief pause between prompts (except last one)
                if i < total_prompts - 1:
                    self.root.after(0, lambda: self.status_var.set("⏳ Preparing next prompt..."))
                    time.sleep(2)

            except Exception as e:
                self.root.after(0, lambda i=i, error=str(e): self.status_var.set(f"❌ Video {i+1} error: {error}"))
                failed_prompts.append((prompt_index, str(e)))
                all_details.append({
                    'prompt': current_prompt,
                    'result': {'success': False, 'error': str(e)},
                    'prompt_index': prompt_index
                })

        # Final results
        self.root.after(0, lambda: self.status_var.set(f"🎉 BATCH COMPLETED: {successful_videos}/{total_prompts} videos created!"))

        return {
            'success': successful_videos > 0,
            'videos_created': successful_videos,
            'total_prompts': total_prompts,
            'failed_prompts': len(failed_prompts),
            'details': all_details,
            'method': 'VeoWorkflowEngine-BatchProcessing',
            'session_videos': self.veo_engine.get_session_video_count(),
            'failed_details': failed_prompts
        }

    def read_prompts_from_file(self, file_path):
        """� Read and parse prompts from saved file - ENHANCED & IMPROVED for Gemini AI"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ Prompts file not found: {file_path}")
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"📖 Reading prompts from: {file_path}")

            # 🔧 STEP 1: Remove unnecessary header lines
            lines = content.split('\n')
            filtered_lines = []
            header_found = False

            for line in lines:
                line_stripped = line.strip()

                # Skip header lines like "Here are the detailed prompts..."
                if not header_found and (
                    line_stripped.startswith('Here are') or
                    line_stripped.startswith('The detailed prompts') or
                    line_stripped.startswith('Below are') or
                    (line_stripped == '' and len(filtered_lines) == 0)
                ):
                    continue

                # When we find the first PROMPT, start collecting
                if line_stripped.startswith('PROMPT'):
                    header_found = True

                if header_found:
                    filtered_lines.append(line)

            print(f"🧹 Removed {len(lines) - len(filtered_lines)} header lines")

            # 🔧 STEP 2: Parse prompts from filtered content
            prompts = []
            current_prompt = None

            for i, line in enumerate(filtered_lines):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # 🎯 Detect prompt patterns - Enhanced for Gemini format
                if (line.startswith('PROMPT') and ':' in line) or \
                   (line.startswith('**PROMPT') and '**' in line) or \
                   (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.')) and len(line) > 10):

                    # Save previous prompt if exists
                    if current_prompt and current_prompt['text'].strip():
                        # 🎨 Optimize for Google Veo before saving
                        current_prompt['veo_optimized'] = self._optimize_prompt_for_veo(current_prompt['text'])
                        current_prompt['character_refs'] = self._extract_character_references(current_prompt['text'])
                        prompts.append(current_prompt)

                    # Start new prompt
                    prompt_num = len(prompts) + 1
                    current_prompt = {
                        'index': prompt_num,
                        'original_line': i + 1,
                        'text': '',
                        'veo_ready': True
                    }

                    # Extract prompt text after colon or number
                    if line.startswith('**PROMPT') and ':' in line:
                        # For **PROMPT X: Title** format, the actual content comes on next lines
                        # Just extract the title after colon for now, content will be added later
                        colon_pos = line.find(':')
                        prompt_text = line[colon_pos + 1:].strip().rstrip('*').strip()
                        current_prompt['title'] = prompt_text
                        current_prompt['text'] = ''  # Content will be added from next lines
                    elif ':' in line:
                        colon_pos = line.find(':')
                        prompt_text = line[colon_pos + 1:].strip()
                        if prompt_text:
                            current_prompt['text'] = prompt_text
                    elif line.startswith(tuple(f'{i}.' for i in range(1, 16))):
                        dot_pos = line.find('.')
                        prompt_text = line[dot_pos + 1:].strip()
                        if prompt_text:
                            current_prompt['text'] = prompt_text
                    else:
                        prompt_text = line.strip()
                        if prompt_text:
                            current_prompt['text'] = prompt_text

                elif current_prompt is not None:
                    # 📝 Include content for this prompt, but skip meta lines
                    if len(line) > 0:
                        # Skip meta lines like "*   **Camera:**", "*   **Lighting:**", etc.
                        if line.strip().startswith('*') and ('**' in line and ':**' in line):
                            continue  # Skip metadata lines
                        if line.strip().startswith('---'):
                            continue  # Skip separator lines

                        # Add actual prompt content
                        if current_prompt['text']:
                            current_prompt['text'] += '\n' + line
                        else:
                            current_prompt['text'] = line

            # Don't forget the last prompt
            if current_prompt and current_prompt['text'].strip():
                current_prompt['veo_optimized'] = self._optimize_prompt_for_veo(current_prompt['text'])
                current_prompt['character_refs'] = self._extract_character_references(current_prompt['text'])
                prompts.append(current_prompt)

            # 🔧 STEP 3: Fallback for unstructured content
            if not prompts:
                print("⚠️  No structured prompts found, using fallback parsing...")
                for i, line in enumerate(filtered_lines):
                    line = line.strip()
                    if line and len(line) > 20 and not line.startswith(('-', '=', '#', 'Original', 'Enhanced', 'Provider')):
                        prompts.append({
                            'index': len(prompts) + 1,
                            'original_line': i + 1,
                            'text': line,
                            'veo_optimized': line,
                            'character_refs': {},
                            'veo_ready': True
                        })

            print(f"✅ Successfully parsed {len(prompts)} prompts")
            print(f"🎬 All prompts are Veo-ready with optimized formatting")

            # Show preview of first few prompts
            for i, prompt in enumerate(prompts[:3]):
                veo_text = prompt.get('veo_optimized', prompt['text'])
                print(f"   [{i+1}] {veo_text[:60]}...")

            if len(prompts) > 3:
                print(f"   ... and {len(prompts) - 3} more prompts")

            return prompts

        except Exception as e:
            print(f"❌ Error reading prompts file: {e}")
            return []

    def _optimize_prompt_for_veo(self, prompt_text):
        """🎯 Optimize prompt specifically for Google Veo"""
        try:
            # Extract structured elements
            veo_elements = {}
            lines = prompt_text.split('\n')

            for line in lines:
                line = line.strip()
                if line.startswith('**VISUAL:**'):
                    veo_elements['visual'] = line.replace('**VISUAL:**', '').strip()
                elif line.startswith('**CAMERA:**'):
                    veo_elements['camera'] = line.replace('**CAMERA:**', '').strip()
                elif line.startswith('**LIGHTING:**'):
                    veo_elements['lighting'] = line.replace('**LIGHTING:**', '').strip()
                elif line.startswith('**MOOD:**'):
                    veo_elements['mood'] = line.replace('**MOOD:**', '').strip()
                elif line.startswith('**STYLE:**'):
                    veo_elements['style'] = line.replace('**STYLE:**', '').strip()

            # Build optimized prompt for Veo
            if veo_elements.get('visual'):
                optimized = veo_elements['visual']

                # Add camera information
                if veo_elements.get('camera'):
                    optimized += f" Camera: {veo_elements['camera']}"

                # Add lighting
                if veo_elements.get('lighting'):
                    optimized += f" Lighting: {veo_elements['lighting']}"

                # Add style
                if veo_elements.get('style'):
                    optimized += f" Style: {veo_elements['style']}"

                return optimized.strip()

            # If no structured elements, return original
            return prompt_text

        except Exception as e:
            print(f"⚠️  Error optimizing prompt for Veo: {e}")
            return prompt_text

    def _extract_character_references(self, prompt_text):
        """👥 Extract character references for consistency"""
        characters = {}
        text_lower = prompt_text.lower()

        if 'luna' in text_lower:
            if 'graceful tabby mother cat' in prompt_text:
                characters['Luna'] = 'graceful tabby mother cat with emerald eyes'
            else:
                characters['Luna'] = 'tabby mother cat'

        if 'patch' in text_lower:
            if 'tiny, fluffy kitten' in prompt_text:
                characters['Patch'] = 'tiny, fluffy kitten'
            else:
                characters['Patch'] = 'small kitten'

        if 'barnaby' in text_lower:
            if 'golden retriever' in text_lower:
                characters['Barnaby'] = 'large, shaggy Golden Retriever with gentle, intelligent eyes'
            else:
                characters['Barnaby'] = 'Golden Retriever'

        return characters

    def on_closing(self):
        """Handle application closing với proper cleanup"""
        print("🚨 ON_CLOSING called - Application is being closed!")
        print(f"🧵 Called from thread: {threading.current_thread().name}")
        print(f"🔍 Call stack:")
        import traceback
        traceback.print_stack()

        try:
            # Cancel license expiry timer
            if hasattr(self, 'license_expiry_timer') and self.license_expiry_timer:
                print("🛑 Canceling license expiry timer...")
                self.root.after_cancel(self.license_expiry_timer)
                self.license_expiry_timer = None

            # Stop status manager
            if hasattr(self, 'status_manager') and self.status_manager:
                print("🛑 Stopping status manager...")
                self.status_manager.stop()

            # Cleanup VeoWorkflowEngine
            if hasattr(self, 'veo_engine') and self.veo_engine:
                print("🛑 Cleaning up VEO engine...")
                self.veo_engine.cleanup()

            # Close GUI
            print("🛑 Destroying GUI...")
            self.root.destroy()

        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            try:
                self.root.destroy()
            except:
                pass

    def show_license_dialog_with_hardware(self):
        """🔑 NEW LICENSE SYSTEM: Show license activation dialog
        Returns: True if license activated successfully, False if user exits
        """
        result = [False]  # Use list to modify from nested functions
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("ClausoNet 4.0 Pro - License Activation")
        dialog.geometry("500x320")  # Reduced size since Hardware ID section removed
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (320 // 2)
        dialog.geometry(f"500x320+{x}+{y}")

        # Focus on dialog
        dialog.focus_force()

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="#1f538d")
        header_frame.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(header_frame, text="🔑 ClausoNet 4.0 Pro License",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="white").pack(pady=15)

        # Main content
        main_frame = ctk.CTkFrame(dialog, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # License key section
        ctk.CTkLabel(main_frame, text="Enter License Key:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))

        license_entry = ctk.CTkEntry(main_frame, width=400, height=40,
                                   placeholder_text="CNPRO-XXXX-XXXX-XXXX-XXXX",
                                   font=ctk.CTkFont(size=12))
        license_entry.pack(padx=20, pady=(0, 15))
        license_entry.focus()

        # Status label
        status_label = ctk.CTkLabel(main_frame, text="",
                                  font=ctk.CTkFont(size=11))
        status_label.pack(pady=(0, 20))

        # Hardware ID stored internally but not displayed
        try:
            hardware_id = self.license_system.get_simple_hardware_id() if self.license_system else "ERROR"
        except:
            hardware_id = "ERROR_GETTING_HARDWARE_ID"

        # Action buttons - Fixed layout
        action_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(15, 25))

        # Create button container for better spacing
        button_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_container.pack(expand=True)

        activating = [False]

        def activate_license():
            if activating[0]:
                return  # Prevent multiple activations

            license_key = license_entry.get().strip()
            if not license_key:
                status_label.configure(text="❌ Please enter license key!", text_color="red")
                return

            activating[0] = True
            status_label.configure(text="🔄 Activating license...", text_color="blue")
            activate_btn.configure(state="disabled")
            exit_btn.configure(state="disabled")  # Disable exit during activation
            dialog.update()

            try:
                if not self.license_system:
                    status_label.configure(text="❌ License system not available!", text_color="red")
                    return

                # Activate license using simplified system
                success = self.license_system.activate_license(license_key)

                if success:
                    status_label.configure(text="✅ License activated successfully!", text_color="green")
                    dialog.update()
                    # Only close dialog on successful activation
                    result[0] = True
                    # Reset state before destroying dialog
                    activating[0] = False
                    dialog.destroy()
                    return  # Exit early to avoid finally block
                else:
                    status_label.configure(text="❌ Invalid license key or activation failed!", text_color="red")
                    # Stay on dialog for retry

            except Exception as e:
                # Log error but don't close dialog - allow user to retry
                error_msg = f"❌ Activation error: {str(e)}"
                status_label.configure(text=error_msg, text_color="red")
                print(f"License activation error: {e}")  # Use print instead of logger
                # Dialog stays open for retry

            finally:
                # Only configure buttons if dialog still exists
                activating[0] = False
                try:
                    activate_btn.configure(state="normal")
                    exit_btn.configure(state="normal")  # Re-enable exit button
                except:
                    # Ignore errors if dialog was already destroyed
                    pass

        def exit_app():
            # Direct exit without confirmation
            result[0] = False
            dialog.destroy()

        def copy_hardware_id():
            # Function kept for potential future use but button removed
            try:
                import pyperclip
                pyperclip.copy(hardware_id)
                status_label.configure(text="📋 Hardware ID copied to clipboard!", text_color="green")
            except ImportError:
                # Fallback for manual copy
                import tkinter.messagebox as messagebox
                messagebox.showinfo("Hardware ID", f"Hardware ID:\n{hardware_id}\n\nPlease copy manually.")

        # Buttons with improved layout - Hardware ID button removed for cleaner UI
        activate_btn = ctk.CTkButton(button_container, text="🔑 Activate License",
                                   command=activate_license, width=200, height=40,
                                   fg_color="#28a745", hover_color="#218838",
                                   font=ctk.CTkFont(size=13, weight="bold"))
        activate_btn.pack(side="left", padx=(0, 20))

        exit_btn = ctk.CTkButton(button_container, text="❌ Exit Application",
                               command=exit_app, width=160, height=40,
                               fg_color="#dc3545", hover_color="#c82333",
                               font=ctk.CTkFont(size=12, weight="bold"))
        exit_btn.pack(side="right")

        # Handle Enter key
        def on_enter(event):
            activate_license()

        license_entry.bind("<Return>", on_enter)

        # Handle dialog close - Allow direct exit
        def on_dialog_close():
            result[0] = False
            dialog.destroy()

        # Handle Escape key - Allow exit with Escape
        def on_escape(event):
            result[0] = False
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        dialog.bind("<Escape>", on_escape)

        # Focus on license entry to prevent other key bindings
        license_entry.focus_set()

        # Wait for dialog to close
        dialog.wait_window()
        return result[0]

    def show_license_dialog(self):
        """Backward compatibility method"""
        return self.show_license_dialog_with_hardware()

    def get_hardware_components(self) -> dict:
        """Thu thập thông tin hardware từ License Admin GUI - Chuẩn hóa với LicenseWizard"""
        components = {}

        try:
            # CPU Info - Chuẩn hóa với LicenseWizard
            try:
                # Ưu tiên sử dụng platform.processor() để đồng nhất
                cpu_info = platform.processor()
                if cpu_info and cpu_info.strip():
                    components['cpu_id'] = cpu_info.strip()
                else:
                    # Fallback: Windows wmic
                    if platform.system() == "Windows":
                        result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId', '/format:value'],
                                              capture_output=True, text=True, shell=True)
                        for line in result.stdout.split('\n'):
                            if line.startswith('ProcessorId='):
                                cpu_id = line.split('=', 1)[1].strip()
                                if cpu_id:
                                    components['cpu_id'] = cpu_id
                                    break
                        else:
                            components['cpu_id'] = "UNKNOWN_CPU"
                    else:
                        components['cpu_id'] = "UNKNOWN_CPU"
            except:
                components['cpu_id'] = "UNKNOWN_CPU"
        except:
            components['cpu_id'] = "UNKNOWN_CPU"

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

    def get_machine_fingerprint(self) -> str:
        """Lấy machine fingerprint cho license binding"""
        try:
            components = self.get_hardware_components()
            return self.generate_hardware_fingerprint(components)
        except Exception as e:
            print(f"Error getting machine fingerprint: {e}")
            return "UNKNOWN_MACHINE"

    def check_license_and_hardware(self):
        """🔑 SIMPLIFIED: Check local license file only - NO admin database"""
        try:
            if not self.license_system:
                return False, "License system not initialized.\n\nPlease restart the application."

            # Check local license file only - FAST and SIMPLE
            is_valid = self.license_system.check_local_license()

            if is_valid:
                return True, "License valid"
            else:
                return False, "No valid license found.\n\nPlease enter a valid license key to activate ClausoNet 4.0 Pro."

        except Exception as e:
            return False, f"License check error: {str(e)}"

    def validate_license_for_operation(self, operation_name="this operation"):
        """🔒 Validate license before performing any operation
        Returns: True if license is valid, False if expired/invalid
        """
        try:
            if not self.license_system:
                messagebox.showerror("License Error",
                    f"License system not available!\n\n"
                    f"Cannot perform {operation_name}.\n"
                    f"Please restart the application.")
                return False

            # Check if license is still valid
            is_valid = self.license_system.check_local_license()

            if not is_valid:
                # License is expired or invalid
                result = messagebox.askyesno("License Expired",
                    f"Your license has expired or is invalid!\n\n"
                    f"Operation: {operation_name}\n\n"
                    f"Do you want to enter a new license key to continue?\n\n"
                    f"Click 'Yes' to enter new license key\n"
                    f"Click 'No' to cancel operation")

                if result:
                    # User wants to enter new license
                    license_activated = self.show_license_dialog_with_hardware()
                    if license_activated:
                        # License successfully activated, allow operation
                        return True
                    else:
                        # User cancelled license activation
                        return False
                else:
                    # User cancelled operation
                    return False

            # License is valid
            return True

        except Exception as e:
            messagebox.showerror("License Check Error",
                f"Error checking license for {operation_name}:\n\n{str(e)}")
            return False

    def load_config(self) -> Dict[str, Any]:
        """Load configuration từ file config.yaml"""
        # Try multiple config paths
        config_paths = [
            Path(__file__).parent.parent / "config.yaml",  # ClausoNet4.0/config.yaml
            Path(__file__).parent / "config.yaml",         # gui/config.yaml
            Path.cwd() / "config.yaml",                    # Current directory
        ]

        # For EXE builds, also check in sys._MEIPASS if available
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller temp directory
            exe_dir = Path(sys._MEIPASS)
            config_paths.insert(0, exe_dir / "config.yaml")
            config_paths.insert(1, exe_dir / "config" / "config.yaml")
            print(f"🔍 EXE mode: checking config in {exe_dir}")

        for config_path in config_paths:
            try:
                print(f"🔍 Trying config: {config_path}")
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        print(f"✅ Config loaded: {config_path}")
                        return config or {}
            except Exception as e:
                print(f"⚠️ Failed to load {config_path}: {e}")
                continue

        print(f"⚠️ No valid config found, using defaults")
        return {}

    def initialize_content_generator(self):
        """Khởi tạo content generator với config"""
        try:
            # Start with base config
            api_config = self.config.get('apis', {})

            # Load API keys from settings if available
            settings_file = Path('data/settings.json')
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings_data = json.load(f)

                    # Update Gemini API key from settings
                    gemini_api_key = settings_data.get('GEMINI_API_KEY', '').strip()
                    if gemini_api_key:
                        if 'gemini' not in api_config:
                            api_config['gemini'] = {}
                        api_config['gemini']['api_key'] = gemini_api_key
                        print(f"Loaded Gemini API key from settings")

                except Exception as e:
                    print(f"Could not load settings for API keys: {e}")

            self.content_generator = ContentGenerator(api_config)
            print("Content generator initialized successfully")

        except Exception as e:
            print(f"Không thể khởi tạo content generator: {e}")
            self.content_generator = None

    def process_content_with_ai(self, script: str, provider: str = None) -> str:
        """Xử lý content với AI"""
        # 🔒 VALIDATE LICENSE BEFORE AI PROCESSING
        if not self.validate_license_for_operation("AI content processing"):
            return script

        if not self.content_generator:
            messagebox.showerror("Error", "Content generator chưa được khởi tạo!")
            return script

        if not script.strip():
            messagebox.showerror("Error", "Vui lòng nhập script trước!")
            return script

        # Determine provider from UI
        if not provider:
            api_choice = self.chatgpt_gemini_api_var.get()
            if not api_choice:
                api_choice = "Gemini API"  # Set default
                self.chatgpt_gemini_api_var.set(api_choice)
            provider = 'gemini' if api_choice == 'Gemini API' else 'chatgpt'

        try:
            # Show processing dialog
            processing_dialog = ctk.CTkToplevel(self.root)
            processing_dialog.title("Đang xử lý...")
            processing_dialog.geometry("400x150")
            processing_dialog.transient(self.root)
            processing_dialog.grab_set()

            # Center dialog
            processing_dialog.update_idletasks()
            x = (processing_dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (processing_dialog.winfo_screenheight() // 2) - (150 // 2)
            processing_dialog.geometry(f"400x150+{x}+{y}")

            ctk.CTkLabel(processing_dialog, text=f"Đang xử lý script với {provider.upper()}...",
                        font=ctk.CTkFont(size=14)).pack(pady=30)

            progress = ctk.CTkProgressBar(processing_dialog)
            progress.pack(pady=10, padx=40, fill="x")
            progress.set(0)

            result_text = script

            def process_in_thread():
                nonlocal result_text
                try:
                    # Animate progress
                    for i in range(20):
                        progress.set(i / 20)
                        time.sleep(0.1)

                    # Process with AI
                    result = self.content_generator.enhance_script(
                        script=script,
                        provider=provider,
                        style='professional'
                    )

                    if result.get('status') == 'success':
                        result_text = result.get('enhanced_script', script)
                        self.root.after(0, lambda: processing_dialog.destroy())
                        self.root.after(0, lambda: messagebox.showinfo("Thành công",
                                       f"Script đã được cải thiện bằng {result.get('provider', provider)}!"))
                    else:
                        error_msg = result.get('error_message', 'Unknown error')
                        self.root.after(0, lambda: processing_dialog.destroy())
                        self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể xử lý script:\n{error_msg}"))

                except Exception as e:
                    self.root.after(0, lambda: processing_dialog.destroy())
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi xử lý script:\n{str(e)}"))

            # Start processing in background thread
            thread = threading.Thread(target=process_in_thread, daemon=True)
            thread.start()

            # Wait for dialog to close
            self.root.wait_window(processing_dialog)

            return result_text

        except Exception as e:
            messagebox.showerror("Error", f"Lỗi khi xử lý content:\n{str(e)}")
            return script




    def show_script_comparison(self, original: str, enhanced: str):
        """Hiển thị dialog so sánh script gốc và enhanced"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Script Enhancement Comparison")
        dialog.geometry("1000x700")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (1000 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"1000x700+{x}+{y}")

        # Title
        title_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(title_frame, text="🤖 AI Script Enhancement Results",
                    font=ctk.CTkFont(size=20, weight="bold")).pack()

        # Main content frame
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Left panel - Original
        left_panel = ctk.CTkFrame(content_frame, fg_color="#2b2b2b")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_panel, text="📝 Original Script",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        original_text = ctk.CTkTextbox(left_panel, font=ctk.CTkFont(family="Arial"))
        original_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        original_text.insert("1.0", original)
        original_text.configure(state="disabled")

        # Right panel - Enhanced
        right_panel = ctk.CTkFrame(content_frame, fg_color="#2b2b2b")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_panel, text="✨ Enhanced Script",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        enhanced_text = ctk.CTkTextbox(right_panel, font=ctk.CTkFont(family="Arial"))
        enhanced_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        enhanced_text.insert("1.0", enhanced)

        # Buttons frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def use_enhanced():
            # Replace content with enhanced script
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", enhanced)
            messagebox.showinfo("Applied", "Enhanced script đã được áp dụng!")
            dialog.destroy()

        def copy_enhanced():
            dialog.clipboard_clear()
            dialog.clipboard_append(enhanced)
            messagebox.showinfo("Copied", "Enhanced script đã được copy vào clipboard!")

        def save_enhanced():
            filename = filedialog.asksaveasfilename(
                title="Save Enhanced Script",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(enhanced)
                    messagebox.showinfo("Saved", f"Enhanced script saved to:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save file:\n{str(e)}")

        # Buttons
        ctk.CTkButton(button_frame, text="✅ Use Enhanced Script", command=use_enhanced,
                     fg_color="#28a745", hover_color="#218838", width=150).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="📋 Copy", command=copy_enhanced,
                     width=100).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="💾 Save", command=save_enhanced,
                     width=100).pack(side="left", padx=(0, 10))

        ctk.CTkButton(button_frame, text="Close", command=dialog.destroy,
                     width=100).pack(side="right")

    # =================== WORKFLOW LOG METHODS ===================

    def clear_workflow_log(self):
        """Clear the workflow log"""
        # License validation
        if not self.validate_license_for_operation():
            return

        try:
            self.workflow_log.delete("0.0", "end")
            self.log_to_workflow("🔄 Log cleared")
        except:
            pass

    def log_to_workflow(self, message, level="INFO"):
        """Add message to workflow log with timestamp and color coding"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            # Color coding based on message content
            if "✅" in message or "completed" in message.lower() or "success" in message.lower():
                color = "#00ff00"  # Green for success
            elif "❌" in message or "error" in message.lower() or "failed" in message.lower():
                color = "#ff4444"  # Red for errors
            elif "⚠️" in message or "warning" in message.lower():
                color = "#ffaa00"  # Orange for warnings
            elif "🔄" in message or "starting" in message.lower() or "processing" in message.lower():
                color = "#00aaff"  # Blue for process
            elif "📥" in message or "download" in message.lower():
                color = "#ff00ff"  # Magenta for downloads
            else:
                color = "#ffffff"  # White for normal

            formatted_message = f"[{timestamp}] {message}\n"

            # Insert at end
            self.workflow_log.insert("end", formatted_message)

            # Configure color for the last line
            line_start = self.workflow_log.index("end-2c linestart")
            line_end = self.workflow_log.index("end-1c")
            self.workflow_log.tag_add(f"color_{timestamp}", line_start, line_end)
            self.workflow_log.tag_config(f"color_{timestamp}", foreground=color)

            # Auto-scroll to bottom
            self.workflow_log.see("end")

            # Update GUI
            self.root.update_idletasks()

        except Exception as e:
            print(f"Error logging to workflow: {e}")

    def update_status(self, message):
        """Update status bar"""
        try:
            self.status_var.set(message)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating status: {e}")

    def update_status_with_log(self, message, level='info'):
        """Update both status bar and workflow log"""
        self.update_status(message)
        self.log_to_workflow(message, level)

    def update_license_status_display(self):
        """Update license status display - no longer used in Settings tab"""
        pass

    def open_license_activation_dialog(self):
        """Open License Activation Dialog"""
        try:
            # Create dialog
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("License Activation")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()

            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")

            # Main frame
            main_frame = ctk.CTkFrame(dialog, fg_color="#2b2b2b")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            ctk.CTkLabel(main_frame, text="🔑 License Activation",
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))

            # Hardware ID Section
            hw_frame = ctk.CTkFrame(main_frame, fg_color="#404040")
            hw_frame.pack(fill="x", padx=20, pady=(0, 15))

            ctk.CTkLabel(hw_frame, text="🆔 Your Hardware ID:",
                        font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))

            # Get hardware ID
            try:
                hw_id = self.license_system.get_simple_hardware_id() if self.license_system else "Unable to get HW ID"
            except:
                hw_id = "Unable to get HW ID"

            hw_entry = ctk.CTkEntry(hw_frame, font=ctk.CTkFont(size=12), height=35, justify="center")
            hw_entry.pack(fill="x", padx=10, pady=(0, 5))
            hw_entry.insert(0, hw_id)
            hw_entry.configure(state="readonly")

            def copy_hw_id():
                dialog.clipboard_clear()
                dialog.clipboard_append(hw_id)
                messagebox.showinfo("Copied", "Hardware ID copied to clipboard!")

            ctk.CTkButton(hw_frame, text="📋 Copy Hardware ID", command=copy_hw_id).pack(pady=(0, 10))

            # License Key Section
            key_frame = ctk.CTkFrame(main_frame, fg_color="#404040")
            key_frame.pack(fill="x", padx=20, pady=(0, 15))

            ctk.CTkLabel(key_frame, text="🔐 Enter License Key:",
                        font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))

            license_key_entry = ctk.CTkEntry(key_frame, placeholder_text="Enter your license key",
                                           height=35, font=ctk.CTkFont(size=12))
            license_key_entry.pack(fill="x", padx=10, pady=(0, 10))

            # Buttons frame
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=(0, 15))

            def activate_license_dialog():
                license_key = license_key_entry.get().strip()
                if not license_key:
                    messagebox.showerror("Error", "Please enter a license key!")
                    return

                try:
                    if not self.license_system:
                        messagebox.showerror("Error", "License system not available!")
                        return

                    # Activate license
                    success = self.license_system.activate_license(license_key)
                    if success:
                        messagebox.showinfo("Success", "✅ License activated successfully!")
                        self.update_license_status_display()
                        dialog.destroy()
                    else:
                        messagebox.showerror("Error", "❌ Invalid license key or activation failed!")

                except Exception as e:
                    messagebox.showerror("Error", f"❌ License activation failed:\n{str(e)}")

            def check_license_dialog():
                try:
                    if not self.license_system:
                        messagebox.showerror("Error", "License system not available!")
                        return

                    is_valid = self.license_system.check_local_license()
                    if is_valid:
                        messagebox.showinfo("License Status", "✅ License is ACTIVE and valid!")
                    else:
                        messagebox.showwarning("License Status", "⚠️ No valid license found!")

                except Exception as e:
                    messagebox.showerror("Error", f"❌ Failed to check license:\n{str(e)}")

            # Activate button
            ctk.CTkButton(btn_frame, text="✅ Activate License", width=120, height=35,
                         fg_color="#28a745", hover_color="#218838",
                         command=activate_license_dialog).pack(side="left", padx=(0, 10))

            # Check button
            ctk.CTkButton(btn_frame, text="🔍 Check Status", width=120, height=35,
                         fg_color="#17a2b8", hover_color="#138496",
                         command=check_license_dialog).pack(side="left", padx=(0, 10))

            # Close button
            ctk.CTkButton(btn_frame, text="❌ Close", width=80, height=35,
                         fg_color="#dc3545", hover_color="#c82333",
                         command=dialog.destroy).pack(side="right")

            # Instructions
            instructions = """📝 Instructions:
1. Copy your Hardware ID above
2. Send it to get your license key
3. Enter the license key and click Activate
4. Your license will be validated and activated"""

            info_text = ctk.CTkTextbox(main_frame, height=80, font=ctk.CTkFont(size=11))
            info_text.pack(fill="x", padx=20, pady=(0, 20))
            info_text.insert("0.0", instructions)
            info_text.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open License Activation dialog:\n{str(e)}")

    def activate_license(self):
        """Activate license - redirect to dialog"""
        self.open_license_activation_dialog()

    def check_license_status(self):
        """Check and display current license status"""
        try:
            if not self.license_system:
                messagebox.showerror("Error", "License system not available!")
                return

            # Get detailed license information
            is_valid = self.license_system.check_local_license()
            hw_id = self.license_system.get_simple_hardware_id()

            # Try to get license details
            license_info = "📋 License Status Report\n" + "="*40 + "\n\n"

            if is_valid:
                license_info += "✅ Status: ACTIVE\n"

                # Try to load user license file for more details
                try:
                    # Use SimpleLicenseSystem path - NO admin_data needed
                    user_license_file = Path.home() / "AppData" / "Local" / "ClausoNet4.0" / "user_license.json"

                    if user_license_file.exists():
                        with open(user_license_file, 'r', encoding='utf-8') as f:
                            user_license = json.load(f)

                        license_info += f"🔑 License Key: {user_license.get('license_key', 'N/A')}\n"
                        activation_date = user_license.get('activation_date', 'N/A')
                        if activation_date != 'N/A':
                            try:
                                date_obj = datetime.datetime.fromisoformat(activation_date)
                                license_info += f"📅 Activated: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            except:
                                license_info += f"📅 Activated: {activation_date}\n"

                except Exception:
                    license_info += "🔑 License Key: [Admin Generated]\n"

            else:
                license_info += "⚠️ Status: INACTIVE\n"
                license_info += "💡 Please enter a valid license key to activate.\n"

            license_info += f"\n🖥️ Hardware ID:\n{hw_id}\n"
            license_info += "\n💼 ClausoNet 4.0 Pro License System"

            # Show in message box
            messagebox.showinfo("License Status", license_info)

            # Also update the status display
            self.update_license_status_display()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Failed to check license status:\n{str(e)}")

    def setup_license_expiry_monitoring(self):
        """🔔 Setup license expiry monitoring system"""
        try:
            # Start initial check
            self.check_license_expiry()

            # Schedule periodic checks every hour
            if self.license_expiry_timer:
                self.root.after_cancel(self.license_expiry_timer)

            self.license_expiry_timer = self.root.after(self.expiry_check_interval, self.check_license_expiry_periodic)
            print("✅ License expiry monitoring started")

        except Exception as e:
            print(f"⚠️ Failed to setup license monitoring: {e}")

    def check_license_expiry_periodic(self):
        """🔄 Periodic license expiry check"""
        try:
            self.check_license_expiry()
            # Schedule next check
            self.license_expiry_timer = self.root.after(self.expiry_check_interval, self.check_license_expiry_periodic)
        except Exception as e:
            print(f"⚠️ Error in periodic license check: {e}")
            # Still schedule next check even if error occurs
            self.license_expiry_timer = self.root.after(self.expiry_check_interval, self.check_license_expiry_periodic)

    def check_license_expiry(self):
        """🕐 Check license expiry and show warnings if needed"""
        try:
            current_time = datetime.datetime.now()

            # Check user license file first - Use SimpleLicenseSystem path
            user_license_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0" / "user_license.json"
            license_data = None
            license_source = "unknown"

            if user_license_path.exists():
                try:
                    with open(user_license_path, 'r', encoding='utf-8') as f:
                        license_data = json.load(f)
                        license_source = "user_file"
                except Exception as e:
                    print(f"⚠️ Error reading user license: {e}")

            # NO ADMIN DATABASE CHECK - Pure SimpleLicenseSystem only
            # Removed admin database fallback for clean deployment

            if not license_data:
                return  # No license to check

            # Parse expiry date
            expiry_str = license_data.get('expiry_date', '')
            if not expiry_str:
                return  # No expiry date

            try:
                if 'T' in expiry_str:
                    expiry_date = datetime.datetime.fromisoformat(expiry_str.replace('Z', ''))
                else:
                    expiry_date = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"⚠️ Invalid expiry date format: {expiry_str}")
                return

            # Calculate time until expiry
            time_until_expiry = expiry_date - current_time
            days_until_expiry = time_until_expiry.days

            license_key = license_data.get('license_key', license_data.get('key', 'Unknown'))
            license_type = license_data.get('license_type', license_data.get('type', 'unknown'))

            # Check if already expired
            if time_until_expiry.total_seconds() <= 0:
                warning_key = f"expired_{license_key}"
                if warning_key not in self.shown_expiry_warnings:
                    self.show_expiry_notification(
                        "⚠️ License Expired",
                        f"Your {license_type} license has expired!\n\n"
                        f"License: {license_key[:20]}...\n"
                        f"Expired: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Please contact support to renew your license.",
                        "error"
                    )
                    self.shown_expiry_warnings.add(warning_key)
                return

            # Show warnings at specific intervals
            # ✅ UPDATED: Removed 1-day warning since trial keys are minimum 7 days
            warning_thresholds = [
                (30, "30 days"),
                (14, "2 weeks"),
                (7, "1 week"),
                (3, "3 days"),
                # (1, "1 day"),     # ❌ REMOVED: No longer needed since trial keys are min 7 days
                (0, "Today")  # For same day expiry
            ]

            for threshold_days, threshold_text in warning_thresholds:
                if days_until_expiry <= threshold_days:
                    warning_key = f"warning_{threshold_days}_{license_key}"
                    if warning_key not in self.shown_expiry_warnings:
                        icon = "⚠️" if threshold_days <= 3 else "🔔"
                        urgency = "error" if threshold_days <= 1 else "warning"

                        self.show_expiry_notification(
                            f"{icon} License Expiry Warning",
                            f"Your {license_type} license will expire in {threshold_text}!\n\n"
                            f"License: {license_key[:20]}...\n"
                            f"Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"Please renew before expiry to avoid service interruption.",
                            urgency
                        )
                        self.shown_expiry_warnings.add(warning_key)
                        break  # Only show one warning per check

        except Exception as e:
            print(f"⚠️ Error checking license expiry: {e}")

    def show_expiry_notification(self, title, message, urgency="info"):
        """🔔 Show license expiry notification"""
        try:
            # Show notification popup
            if urgency == "error":
                messagebox.showerror(title, message)
            elif urgency == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)

            # Also log to console
            print(f"🔔 {title}: {message}")

        except Exception as e:
            print(f"⚠️ Error showing notification: {e}")

def main():
    """Khởi chạy GUI"""
    app = ClausoNetGUI()
    app.run()

if __name__ == "__main__":
    main()
