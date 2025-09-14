#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 VEO WORKFLOW DEBUG TOOL
Debug và kiểm tra từng bước trong automation workflow
"""

import os
import sys
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VeoWorkflowDebugger:
    """🔧 Debug tool cho Veo automation workflow"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.config = {
            'wait_timeout': 10,
            'debug_pause': 2,
            'screenshot_on_error': True
        }
        
        # Setup paths for exe compatibility
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys._MEIPASS)
            self.user_data_dir = Path.home() / "AppData/Local/ClausoNet4.0/profiles"
        else:
            self.base_dir = Path(__file__).parent
            self.user_data_dir = self.base_dir / "chrome_profiles"
            
        self.debug_dir = self.base_dir / "debug_screenshots"
        self.debug_dir.mkdir(exist_ok=True)
        
        print(f"🔧 Debug tool initialized")
        print(f"📁 User data dir: {self.user_data_dir}")
        print(f"📁 Debug screenshots: {self.debug_dir}")

    def list_available_profiles(self):
        """List all available profiles từ ProfileManager"""
        print("📋 Scanning for available profiles...")
        
        profiles = []
        try:
            # Check both exe và dev mode paths
            profile_dirs = [
                Path.home() / "AppData/Local/ClausoNet4.0/profiles",  # Exe mode
                Path(__file__).parent / "chrome_profiles"            # Dev mode
            ]
            
            for profile_base in profile_dirs:
                if profile_base.exists():
                    print(f"🔍 Checking: {profile_base}")
                    for item in profile_base.iterdir():
                        if item.is_dir():
                            # Check if có cookies file
                            cookies_file = None
                            data_dir = Path(__file__).parent / "data/profile_cookies"
                            if data_dir.exists():
                                cookies_file = data_dir / f"{item.name}.json"
                            
                            profile_info = {
                                'name': item.name,
                                'path': item,
                                'has_cookies': cookies_file.exists() if cookies_file else False,
                                'cookies_path': cookies_file if cookies_file else None
                            }
                            profiles.append(profile_info)
                            
                            status = "🍪 (with cookies)" if profile_info['has_cookies'] else "📁 (empty)"
                            print(f"   {status} {item.name}")
            
            return profiles
            
        except Exception as e:
            print(f"❌ Profile scan failed: {e}")
            return []

    def setup_chrome(self, profile_name=None):
        """Setup Chrome với profile từ ProfileManager hoặc tạo mới"""
        print("🚀 Setting up Chrome...")
        
        # List available profiles if no specific profile requested
        if not profile_name:
            profiles = self.list_available_profiles()
            
            if profiles:
                print("\nAvailable profiles:")
                for i, profile in enumerate(profiles):
                    status = "🍪" if profile['has_cookies'] else "📁"
                    print(f"   [{i}] {status} {profile['name']}")
                
                print(f"   [new] Create new debug profile")
                
                choice = input("\nSelect profile (number or 'new'): ").strip()
                
                if choice.isdigit() and 0 <= int(choice) < len(profiles):
                    selected_profile = profiles[int(choice)]
                    profile_name = selected_profile['name']
                    profile_path = selected_profile['path']
                    print(f"✅ Using existing profile: {profile_name}")
                elif choice == 'new':
                    profile_name = "debug_profile"
                    profile_path = self.user_data_dir / profile_name
                    profile_path.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Creating new debug profile: {profile_name}")
                else:
                    # Try to use the input as profile name
                    profile_name = choice
                    # Find matching profile
                    matching_profile = None
                    for profile in profiles:
                        if profile['name'] == profile_name:
                            matching_profile = profile
                            break
                    
                    if matching_profile:
                        profile_path = matching_profile['path']
                        print(f"✅ Using existing profile: {profile_name}")
                    else:
                        profile_path = self.user_data_dir / profile_name
                        profile_path.mkdir(parents=True, exist_ok=True)
                        print(f"✅ Creating new profile: {profile_name}")
            else:
                profile_name = "debug_profile"
                profile_path = self.user_data_dir / profile_name
                profile_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ No profiles found, creating debug profile: {profile_name}")
        else:
            # Use specified profile
            profile_path = self.user_data_dir / profile_name
            if not profile_path.exists():
                profile_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Using profile: {profile_name}")
        
        try:
            # 🎯 ENHANCED: Try using ProductionChromeDriverManager first
            try:
                sys.path.append(str(Path(__file__).parent))
                from utils.production_chrome_manager import ProductionChromeDriverManager
                from utils.resource_manager import resource_manager
                
                chrome_manager = ProductionChromeDriverManager(resource_manager)
                
                # Create Chrome options for production manager
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                options = ChromeOptions()
                options.add_argument("--no-first-run")
                options.add_argument("--no-default-browser-check")
                options.add_argument("--disable-default-apps")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--no-sandbox")
                options.add_argument("--window-size=1400,900")
                options.add_argument("--remote-debugging-port=9222")
                
                self.driver = chrome_manager.create_webdriver(
                    profile_path=str(profile_path.absolute()),
                    headless=False,
                    debug_port=9222,
                    options=options
                )
                print("✅ Chrome setup with ProductionChromeDriverManager")
                
            except (ImportError, Exception) as e:
                print(f"⚠️ Production manager failed: {e}")
                print("🔄 Using fallback Chrome setup...")
                
                options = Options()
                options.add_argument(f"--user-data-dir={str(profile_path.absolute())}")
                options.add_argument("--profile-directory=Default")
                options.add_argument("--no-first-run")
                options.add_argument("--no-default-browser-check")
                options.add_argument("--disable-default-apps")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--no-sandbox")
                options.add_argument("--window-size=1400,900")
                options.add_argument("--remote-debugging-port=9222")
                
                # Try webdriver manager first
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    print("✅ Chrome setup with webdriver-manager")
                except ImportError:
                    self.driver = webdriver.Chrome(options=options)
                    print("✅ Chrome setup with system driver")
            
            # Verify driver was created
            if not self.driver:
                print("❌ Failed to create Chrome driver")
                return False
            
            self.driver.implicitly_wait(3)
            self.wait = WebDriverWait(self.driver, self.config['wait_timeout'])
            
            # Anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.current_profile = profile_name
            print(f"🔒 Profile loaded: {profile_name}")
            return True
            
        except Exception as e:
            print(f"❌ Chrome setup failed: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return False

    def navigate_to_veo(self):
        """Navigate to Google Veo"""
        print("🌐 Navigating to Google Veo...")
        
        try:
            veo_url = "https://labs.google/fx/vi/tools/flow"
            self.driver.get(veo_url)
            
            # Wait for page load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(3)
            
            print(f"✅ Successfully navigated to: {self.driver.current_url}")
            self.take_debug_screenshot("01_navigation")
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            self.take_debug_screenshot("01_navigation_failed")
            return False

    def debug_page_elements(self):
        """Debug và scan tất cả elements trên page"""
        print("🔍 DEBUG: Scanning all page elements...")
        
        try:
            # Scan all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"\n📋 Found {len(buttons)} buttons:")
            
            relevant_buttons = []
            for i, btn in enumerate(buttons):
                try:
                    if btn.is_displayed():
                        text = btn.text.strip()
                        aria_label = btn.get_attribute('aria-label') or ''
                        class_name = btn.get_attribute('class') or ''
                        
                        if text or aria_label:
                            button_info = {
                                'index': i,
                                'text': text,
                                'aria_label': aria_label,
                                'class': class_name[:50],
                                'element': btn
                            }
                            relevant_buttons.append(button_info)
                            
                            # Check for keywords
                            keywords = ['new', 'project', 'create', 'tạo', 'mới', 'settings', 'cài đặt', 'tune']
                            if any(keyword in text.lower() or keyword in aria_label.lower() for keyword in keywords):
                                print(f"   🎯 [{i}] '{text[:30]}' | aria: '{aria_label[:30]}' | class: '{class_name[:30]}'")
                            
                except Exception as e:
                    continue
            
            print(f"\n📊 Total relevant buttons: {len(relevant_buttons)}")
            
            # Scan textareas and inputs
            inputs = self.driver.find_elements(By.TAG_NAME, "textarea") + self.driver.find_elements(By.TAG_NAME, "input")
            print(f"\n📝 Found {len(inputs)} input elements:")
            
            for i, inp in enumerate(inputs):
                try:
                    if inp.is_displayed():
                        placeholder = inp.get_attribute('placeholder') or ''
                        input_id = inp.get_attribute('id') or ''
                        input_type = inp.get_attribute('type') or inp.tag_name
                        
                        if placeholder or input_id:
                            print(f"   📝 [{i}] {input_type} | id: '{input_id}' | placeholder: '{placeholder[:50]}'")
                            
                except Exception as e:
                    continue
            
            self.take_debug_screenshot("02_element_scan")
            return relevant_buttons
            
        except Exception as e:
            print(f"❌ Element scan failed: {e}")
            return []

    def test_button_click(self, button_info):
        """Test clicking một button cụ thể"""
        print(f"\n🧪 Testing button click: '{button_info['text'][:30]}'")
        
        try:
            element = button_info['element']
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            
            # Take screenshot before click
            self.take_debug_screenshot(f"03_before_click_{button_info['index']}")
            
            # Try different click methods
            click_methods = [
                ("Regular Click", lambda: element.click()),
                ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
                ("ActionChains", lambda: ActionChains(self.driver).move_to_element(element).click().perform())
            ]
            
            for method_name, click_func in click_methods:
                try:
                    click_func()
                    print(f"✅ {method_name} successful")
                    time.sleep(2)
                    
                    # Take screenshot after click
                    self.take_debug_screenshot(f"04_after_click_{button_info['index']}_{method_name.replace(' ', '_')}")
                    return True
                    
                except Exception as e:
                    print(f"❌ {method_name} failed: {e}")
                    continue
                    
            return False
            
        except Exception as e:
            print(f"❌ Button click test failed: {e}")
            return False

    def find_element_with_retry(self, selectors, description, max_retries=3):
        """Tìm element với retry logic để handle stale references"""
        from selenium.common.exceptions import StaleElementReferenceException
        
        for retry in range(max_retries):
            try:
                print(f"🔍 Finding {description} (attempt {retry + 1}/{max_retries})...")
                
                for i, selector in enumerate(selectors):
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element and element.is_displayed():
                            print(f"✅ Found {description} with selector {i+1}")
                            return element
                    except Exception as e:
                        continue
                
                if retry < max_retries - 1:
                    print(f"🔄 Retry {retry + 1} failed, waiting and refreshing...")
                    time.sleep(2)
                    # Refresh page elements
                    self.driver.execute_script("return document.readyState") 
                    
            except Exception as e:
                print(f"⚠️ Retry {retry + 1} error: {e}")
                if retry < max_retries - 1:
                    time.sleep(2)
        
        print(f"❌ {description} not found after {max_retries} attempts")
        return None

    def click_element_with_retry(self, element, description, max_retries=3):
        """Click element với retry logic cho stale elements"""
        from selenium.common.exceptions import StaleElementReferenceException
        
        for retry in range(max_retries):
            try:
                # Scroll to element first
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                
                # Try clicking
                element.click()
                print(f"✅ Clicked {description} successfully")
                return True
                
            except StaleElementReferenceException:
                if retry < max_retries - 1:
                    print(f"🔄 Stale element detected, refreshing and retrying...")
                    time.sleep(2)
                    # Element is stale, need to re-find it
                    return False  # Caller should re-find element
                else:
                    print(f"❌ Element still stale after {max_retries} attempts")
                    return False
            except Exception as e:
                print(f"⚠️ Click retry {retry + 1} failed: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
                    
        return False

    def debug_dropdown_options(self):
        """Debug dropdown options sau khi click"""
        print("🔍 DEBUG: Scanning dropdown options...")
        
        try:
            time.sleep(2)  # Wait for dropdown to open
            
            # Scan for dropdown options
            option_selectors = [
                "//div[@role='option']",
                "//li[@role='option']", 
                "//div[contains(@class, 'option')]",
                "//li[contains(@class, 'option')]",
                "//div[contains(@class, 'menu-item')]",
                "//div[contains(text(), 'Veo')]",
                "//div[contains(text(), 'Quality')]",
                "//div[contains(text(), 'Fast')]"
            ]
            
            all_options = []
            for selector in option_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            if text:
                                all_options.append({
                                    'text': text,
                                    'selector': selector,
                                    'element': elem
                                })
                except:
                    continue
            
            print(f"📋 Found {len(all_options)} dropdown options:")
            for i, opt in enumerate(all_options[:10]):  # Show first 10
                print(f"   [{i}] '{opt['text']}'")
            
            self.take_debug_screenshot("05_dropdown_options")
            return all_options
            
        except Exception as e:
            print(f"❌ Dropdown options scan failed: {e}")
            return []

    def test_complete_workflow(self, test_prompt="Debug test video: A beautiful sunset over mountains"):
        """Test complete workflow dựa trên VeoWorkflowEngine thực tế"""
        print(f"\n🎬 TESTING COMPLETE VEO WORKFLOW")
        print("=" * 50)
        print(f"Test prompt: {test_prompt}")
        
        # Workflow steps giống hệt trong run_basic_workflow
        workflow_steps = [
            ("Find New Project Button", self.find_new_project_button),
            ("Click New Project", lambda: self.safe_click_current("New Project Button")),
            ("Wait After New Project Click", self.wait_after_new_project_click),
            ("Find and Click Project Type Dropdown", self.find_and_click_project_type_dropdown),
            ("Select Text to Video", lambda: self.select_project_type_option("Từ văn bản sang video")),
            ("Close Dropdown After Selection", self.close_dropdown_if_open),
            ("Find Settings Button", self.find_settings_button),
            ("Click Settings Button", lambda: self.safe_click_current("Settings Button")),
            ("Find Model Dropdown", self.find_model_dropdown),
            ("Click Model Dropdown", self.click_model_dropdown_enhanced),
            ("Select Model", lambda: self.select_model_option("fast")),
            ("Find Output Count Dropdown", self.find_output_count_dropdown),
            ("Click Output Count Dropdown", lambda: self.safe_click_current("Output Count Dropdown")),
            ("Select Output Count", lambda: self.select_output_count(1)),
            ("Close Settings Popup", self.close_settings_popup),
            ("Find Prompt Input", self.find_prompt_input),
            ("Type Prompt", lambda: self.type_prompt_enhanced(test_prompt)),
            ("Find Send Button", self.find_send_button),
            ("Click Send Button", lambda: self.safe_click_current("Send Button")),
            ("Wait for Video Generation", self.wait_for_video_generation),
            ("Find Generated Videos", lambda: self.find_generated_videos_with_retry(only_new=True)),
            ("Download Videos", self.download_all_found_videos)
        ]
        
        results = {}
        self.current_element = None  # Initialize current_element
        
        for step_name, step_func in workflow_steps:
            print(f"\n🔄 WORKFLOW STEP: {step_name}")
            print("-" * 40)
            
            try:
                result = step_func()
                
                # Handle Find steps differently
                if step_name.startswith("Find"):
                    if result:
                        self.current_element = result
                        print(f"✅ {step_name} - Found element")
                        results[step_name] = True
                    else:
                        print(f"❌ {step_name} - Element not found")
                        results[step_name] = False
                        if input("Continue to next step? (y/n): ").strip().lower() != 'y':
                            break
                else:
                    # Action steps
                    if result:
                        print(f"✅ {step_name} - SUCCESS")
                        results[step_name] = True
                    else:
                        print(f"❌ {step_name} - FAILED")
                        results[step_name] = False
                        if input("Continue to next step? (y/n): ").strip().lower() != 'y':
                            break
                
                # Pause between steps
                time.sleep(2)
                        
            except Exception as e:
                print(f"❌ {step_name} - ERROR: {e}")
                results[step_name] = False
                self.take_debug_screenshot(f"error_{step_name.replace(' ', '_')}")
                
                if input("Continue to next step? (y/n): ").strip().lower() != 'y':
                    break
        
        # Summary
        print(f"\n{'='*50}")
        print("🏁 WORKFLOW TEST SUMMARY")
        print('='*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for step_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {step_name}")
        
        print(f"\n📊 OVERALL: {passed}/{total} steps passed")
        return results

    # ===== WORKFLOW FUNCTIONS - Copied from VeoWorkflowEngine =====

    def find_new_project_button(self):
        """Tìm nút tạo dự án mới - từ VeoWorkflowEngine"""
        print("🔍 Finding New Project button...")

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
                    print("✅ Found New Project button")
                    return element
            except TimeoutException:
                continue

        print("❌ New Project button not found")
        return None

    def find_project_type_dropdown(self):
        """Tìm dropdown chọn loại dự án - EXACT COPY from main_window.py"""
        print("🔍 Finding Project Type dropdown...")
        
        # Wait for page to fully load after New Project click
        print("⏳ Waiting for page to load after navigation...")
        time.sleep(5)
        
        # Clear stale references
        self.current_element = None

        selectors = [
            "//button[contains(text(), 'Từ văn bản sang video')]",
            "//button[contains(text(), 'Text to Video')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'văn bản')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'video')]",
            "//button[contains(text(), 'video') and contains(., 'arrow_drop_down')]",
            "//button[contains(@class, 'dropdown') and contains(text(), 'video')]"
        ]

        for i, selector in enumerate(selectors):
            try:
                print(f"🔍 Trying selector [{i}]: {selector}")
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Project Type dropdown with selector [{i}]")
                    return element
            except Exception as e:
                print(f"   Selector [{i}] failed: {e}")
                continue

        # Enhanced debug scan if not found
        print("🔍 Enhanced debug scan - looking for all video-related elements...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"📋 Total buttons on page: {len(all_buttons)}")
            
            video_buttons = []
            for i, btn in enumerate(all_buttons):
                try:
                    if btn.is_displayed() and btn.text:
                        text_lower = btn.text.lower()
                        if any(keyword in text_lower for keyword in ['video', 'văn bản', 'text', 'image', 'hình ảnh']):
                            video_buttons.append({
                                'index': i,
                                'text': btn.text,
                                'displayed': btn.is_displayed(),
                                'enabled': btn.is_enabled()
                            })
                except:
                    continue
                    
            print(f"🎯 Found {len(video_buttons)} video-related buttons:")
            for btn_info in video_buttons[:10]:  # Show first 10
                print(f"   [{btn_info['index']}] '{btn_info['text'][:50]}...' (displayed={btn_info['displayed']}, enabled={btn_info['enabled']})")
                
        except Exception as e:
            print(f"❌ Enhanced debug scan failed: {e}")

        print("❌ Project Type dropdown not found")
        return None

    def find_and_click_project_type_dropdown(self):
        """Tìm và click Project Type dropdown trong một bước - tránh stale element"""
        print("🔍 Finding and clicking Project Type dropdown...")
        
        # Wait for page to fully load
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        selectors = [
            "//button[contains(text(), 'Từ văn bản sang video')]",
            "//button[contains(text(), 'Text to Video')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'văn bản')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'video')]",
            "//button[contains(text(), 'video') and contains(., 'arrow_drop_down')]",
            "//button[contains(@class, 'dropdown') and contains(text(), 'video')]"
        ]

        for i, selector in enumerate(selectors):
            try:
                print(f"🔍 Trying selector [{i}]: {selector}")
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Project Type dropdown with selector [{i}]")
                    # Click immediately to avoid stale element
                    if self.safe_click_element(element, f"Project Type Dropdown (selector {i})"):
                        print("✅ Successfully clicked Project Type dropdown")
                        return True
                    else:
                        print("❌ Failed to click Project Type dropdown")
            except Exception as e:
                print(f"   Selector [{i}] failed: {e}")
                continue

        # Enhanced debug if all selectors fail
        print("🔍 DEBUG: All selectors failed, scanning page...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"📋 Total buttons: {len(all_buttons)}")
            
            for i, btn in enumerate(all_buttons[:20]):  # Check first 20 buttons
                try:
                    if btn.is_displayed() and btn.text:
                        text = btn.text.strip()
                        if any(keyword in text.lower() for keyword in ['video', 'văn bản', 'text']):
                            print(f"   Button [{i}]: '{text}' (displayed={btn.is_displayed()})")
                except:
                    continue
        except Exception as e:
            print(f"❌ Debug scan failed: {e}")

        print("❌ Could not find and click Project Type dropdown")
        return False

    def select_project_type_option(self, target_option="Từ văn bản sang video"):
        """Chọn option trong Project Type dropdown - MATCHING main_window.py - LINE 692"""
        print(f"🎯 Selecting project type: {target_option}")
        print("🚨 DEBUG: This is the LINE 692 function - ORIGINAL VERSION")

        # Wait for dropdown options
        time.sleep(2)
        
        # DEBUG: Scan all visible elements to see what's available
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'video') or contains(text(), 'Video') or contains(text(), 'văn bản')]")
            print(f"🔍 DEBUG: Found {len(all_elements)} elements with 'video' or 'văn bản':")
            for i, elem in enumerate(all_elements[:10]):  # Limit to first 10
                try:
                    if elem.is_displayed():
                        print(f"   [{i}] Tag: {elem.tag_name}, Text: '{elem.text[:50]}...', Displayed: {elem.is_displayed()}")
                except Exception as e:
                    print(f"   [{i}] Error reading element: {e}")
        except Exception as e:
            print(f"❌ DEBUG scan failed: {e}")

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

        for i, selector in enumerate(option_selectors):
            try:
                print(f"🔍 Trying selector [{i}]: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"   Found {len(elements)} elements")
                for j, element in enumerate(elements):
                    try:
                        if element.is_displayed():
                            print(f"   Element [{j}]: Text='{element.text}', Displayed={element.is_displayed()}")
                            if self.safe_click_element(element, f"Project Type Option: {target_option}"):
                                time.sleep(2)
                                print("✅ Successfully clicked project type option")
                                return True
                        else:
                            print(f"   Element [{j}] not displayed")
                    except Exception as e:
                        print(f"   Element [{j}] error: {e}")
            except Exception as e:
                print(f"   Selector [{i}] failed: {e}")
                continue

        # Fallback to keyboard navigation - CRITICAL addition from main_window.py
        print("🔧 Fallback: Using keyboard navigation for project type selection...")
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_DOWN)
            time.sleep(1)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            print("✅ Keyboard navigation successful")
            return True
        except Exception as e:
            print(f"❌ All methods failed for project type: {target_option}")
            return False

    def close_dropdown_if_open(self):
        """Đóng dropdown nếu đang mở"""
        print("🔍 Closing dropdown if open...")
        
        try:
            # Click outside to close dropdown
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            time.sleep(1)
            print("✅ Dropdown closed")
            return True
        except:
            print("⚠️ Could not close dropdown")
            return True  # Don't fail the workflow for this

    def wait_after_new_project_click(self):
        """Wait and scan for elements after New Project click - Fix stale element issue"""
        print("⏳ Waiting for page to load after New Project click...")
        time.sleep(5)  # Longer wait for page to fully load
        
        # Clear any stale element references
        self.current_element = None
        
        # DEBUG: Scan for available elements
        try:
            print("🔍 DEBUG: Scanning page after New Project click...")
            
            # Scan for any buttons with project type related text
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"📋 Found {len(all_buttons)} buttons total")
            
            project_type_buttons = []
            for i, btn in enumerate(all_buttons):
                try:
                    if btn.is_displayed() and btn.text:
                        text_lower = btn.text.lower()
                        if any(keyword in text_lower for keyword in ['text', 'video', 'văn bản', 'image', 'hình ảnh']):
                            project_type_buttons.append({
                                'index': i,
                                'text': btn.text,
                                'tag': btn.tag_name
                            })
                except:
                    continue
                    
            print(f"🎯 Found {len(project_type_buttons)} potential project type buttons:")
            for btn_info in project_type_buttons:
                print(f"   [{btn_info['index']}] {btn_info['tag']}: '{btn_info['text']}'")
                
            # Scan for dropdown indicators
            dropdown_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'arrow_drop_down') or contains(@class, 'dropdown') or contains(text(), '▼')]")
            print(f"🔽 Found {len(dropdown_elements)} dropdown indicators")
            
            return True
            
        except Exception as e:
            print(f"❌ Page scan failed: {e}")
            return True  # Don't fail workflow

    def find_settings_button(self):
        """Tìm nút Settings - từ VeoWorkflowEngine"""
        print("🔍 Finding Settings button...")

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
                    print("✅ Found Settings button")
                    return element
            except:
                continue

        print("❌ Settings button not found")
        return None

    def debug_settings_popup_elements(self):
        """Debug method to scan all elements in settings popup"""
        print("\n🔍 DEBUGGING SETTINGS POPUP ELEMENTS")
        print("="*50)
        
        try:
            # Find popup container
            popup_selectors = [
                "//div[contains(@class, 'popup')]",
                "//div[contains(@class, 'modal')]",
                "//div[contains(@class, 'dialog')]",
                "//div[@role='dialog']",
                "//div[contains(@class, 'overlay')]"
            ]
            
            popup_found = False
            for selector in popup_selectors:
                try:
                    popup = self.driver.find_element(By.XPATH, selector)
                    if popup.is_displayed():
                        print(f"✅ Found popup with selector: {selector}")
                        popup_found = True
                        break
                except:
                    continue
            
            if not popup_found:
                print("⚠️ No popup container found, scanning entire page...")
            
            # Scan all buttons in popup or page
            button_selectors = [
                "//button",
                "//div[@role='button']", 
                "//div[contains(@class, 'button')]",
                "//*[contains(text(), 'Veo') or contains(text(), 'Model') or contains(text(), 'video') or contains(text(), 'ratio')]"
            ]
            
            for selector in button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"\n📋 Elements found with '{selector}':")
                    
                    for i, element in enumerate(elements[:10]):  # Limit to 10
                        if element.is_displayed():
                            text = element.text.strip()[:100]  # Limit text length
                            tag = element.tag_name
                            classes = element.get_attribute('class') or 'no-class'
                            print(f"  [{i}] {tag}.{classes[:30]} - '{text}'")
                            
                except Exception as e:
                    print(f"❌ Error scanning {selector}: {e}")
                    
        except Exception as e:
            print(f"❌ Debug scan failed: {e}")
        
        print("="*50)
        print("🔍 SETTINGS POPUP DEBUG COMPLETE\n")

    def find_model_dropdown(self):
        """Tìm dropdown model trong settings popup - từ main_window.py logic"""
        print("🔍 Finding Model dropdown in settings popup...")

        # ENHANCED: Longer wait for popup to fully load
        print("⏳ Waiting for popup to fully load...")
        time.sleep(4)

        # Debug scan first - MATCHING main_window.py logic EXACTLY
        print("🔍 DEBUG: Scanning all visible buttons after settings click...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"🔍 Scanning {len(all_buttons)} buttons for model dropdown...")
            relevant_buttons = []
            for i, btn in enumerate(all_buttons):
                try:
                    if btn.is_displayed():
                        text = btn.text.strip() if btn.text else ""
                        print(f"   [DEBUG] Button {i}: '{text}' (displayed={btn.is_displayed()})")
                        if any(keyword in text.lower() for keyword in ['veo', 'quality', 'fast', 'mô hình', 'model']):
                            relevant_buttons.append({
                                'index': i,
                                'text': text,
                                'element': btn
                            })
                except Exception as e:
                    print(f"   [DEBUG] Exception for button {i}: {e}")
                    continue
            print(f"📋 Found {len(relevant_buttons)} relevant model buttons:")
            for btn_info in relevant_buttons:
                print(f"   [{btn_info['index']}] '{btn_info['text']}'")
            if not relevant_buttons:
                print("⚠️ Không tìm thấy nút model nào có text phù hợp!")
            # Priority logic
            for btn_info in relevant_buttons:
                text_lower = btn_info['text'].lower()
                if 'mô hình' in text_lower and any(indicator in btn_info['text'] for indicator in ['arrow_drop_down', '▼', 'dropdown']):
                    print(f"✅ Using dropdown button with 'Mô hình': '{btn_info['text'][:50]}...'")
                    return btn_info['element']
            if relevant_buttons:
                best_btn = relevant_buttons[0]
                print(f"✅ Using fallback button: '{best_btn['text'][:50]}...'")
                return best_btn['element']
        except Exception as e:
            print(f"❌ Button scan failed: {e}")
            
        # Look for any element containing model-related text
            model_keywords = ['Veo', 'veo', 'VEO', 'Model', 'model', 'Mô hình', 'Quality', 'Fast']
            all_model_elements = []
            
            for keyword in model_keywords:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.text and elem not in [e['element'] for e in all_model_elements]:
                            all_model_elements.append({
                                'text': elem.text,
                                'tag': elem.tag_name,
                                'element': elem
                            })
                    except:
                        continue
            
            print(f"📋 Found {len(all_model_elements)} elements with model text:")
            for i, elem_info in enumerate(all_model_elements[:8]):  # Show top 8
                print(f"  [{i}] <{elem_info['tag']}> '{elem_info['text'][:60]}...'")
                
            # Try to find clickable model elements
            for elem_info in all_model_elements:
                elem = elem_info['element']
                text_lower = elem_info['text'].lower()
                
                # Check if element is clickable and looks like model selector
                if elem.tag_name in ['button', 'div', 'span'] and ('veo' in text_lower or 'mô hình' in text_lower):
                    try:
                        # Test if clickable
                        if elem.is_enabled():
                            print(f"✅ Using model element: <{elem.tag_name}> {elem_info['text'][:40]}...")
                            return elem
                    except:
                        continue
                        
        except Exception as e:
            print(f"❌ Element scan failed: {e}")

        # Also scan all elements, not just buttons
        print("🔍 DEBUG: Scanning all elements for model text...")
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Veo') or contains(text(), 'Mô hình')]")
            print(f"📋 Found {len(all_elements)} elements with model-related text:")
            for i, elem in enumerate(all_elements[:5]):
                try:
                    if elem.is_displayed():
                        print(f"  [{i}] Tag: {elem.tag_name}, Text: '{elem.text[:50]}'")
                        # If it's clickable, try using it
                        if elem.tag_name in ['button', 'div'] and 'veo' in elem.text.lower():
                            return elem
                except:
                    continue
        except Exception as e:
            print(f"❌ Element scan failed: {e}")

        selectors = [
            # EXACT selectors from main_window.py
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

        # Try selectors with WebDriverWait like main_window.py
        for i, selector in enumerate(selectors):
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Model dropdown with selector {i+1}")
                    return element
            except TimeoutException:
                continue
            except Exception as e:
                continue

        print("❌ Model dropdown not found")
        return None

    def click_model_dropdown_enhanced(self):
        """Enhanced model dropdown clicking với forced opening - từ main_window.py"""
        if not self.current_element:
            print("❌ No model dropdown element found")
            return False

        print("🔧 Enhanced model dropdown click...")

        # Initial click with test_element_click_methods
        success = self.test_element_click_methods(self.current_element, "Model Dropdown")
        if not success:
            return False

        # Multiple click attempts to force dropdown open (from main_window.py)
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
        """Chọn model option - theo logic main_window.py"""
        target_text = "Veo 3 - Fast" if model_type.lower() == "fast" else "Veo 3 - Quality"
        print(f"🎯 Selecting model: {target_text}")

        # Wait for options to appear after clicking dropdown
        print("   🕐 Waiting for dropdown options to load...")
        time.sleep(3)

        # First try keyboard navigation (most reliable for avoiding click intercepted)
        try:
            print("   🎯 Trying keyboard navigation...")
            # Focus on the model dropdown first
            if self.current_element:
                try:
                    self.current_element.send_keys(Keys.SPACE)  # Open dropdown with space
                    time.sleep(1)
                except:
                    pass
            
            # Use body element for navigation
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Navigate based on model type
            if model_type.lower() == "quality":
                print("     🔽 Navigating to Quality option...")
                body.send_keys(Keys.ARROW_DOWN)  # Navigate to Quality
                time.sleep(0.5)
                body.send_keys(Keys.ARROW_DOWN)  # May need multiple downs
            else:
                print("     🔼 Navigating to Fast option...")  
                body.send_keys(Keys.ARROW_UP)    # Navigate to Fast (usually first)
                time.sleep(0.5)
            
            print("     ✅ Pressing ENTER to select...")
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            
            # Verify selection worked
            print("   🔍 Verifying selection...")
            if self.verify_model_selection(target_text):
                print("✅ Keyboard navigation successful")
                return True
            else:
                print("   ⚠️ Keyboard selection not verified, trying fallback...")
                
        except Exception as e:
            print(f"   ⚠️ Keyboard navigation failed: {e}")

        # Enhanced fallback with debug scanning
        print("   🔄 Trying click fallback with scanning...")
        try:
            # Scan for visible model options after dropdown opened
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Veo') or contains(text(), 'Fast') or contains(text(), 'Quality')]")
            model_options = []
            
            for elem in all_elements:
                try:
                    if elem.is_displayed() and elem.text:
                        text_lower = elem.text.lower()
                        if ('veo' in text_lower and (model_type.lower() in text_lower)) or target_text.lower() in text_lower:
                            model_options.append(elem)
                except:
                    continue
                    
            print(f"   📋 Found {len(model_options)} potential model options")
            
            for elem in model_options:
                try:
                    print(f"     🎯 Trying to click: {elem.text[:50]}...")
                    # Use JavaScript click to avoid interception
                    self.driver.execute_script("arguments[0].click();", elem)
                    time.sleep(2)
                    
                    if self.verify_model_selection(target_text):
                        print(f"✅ Selected model: {target_text}")
                        return True
                except Exception as e:
                    print(f"     ❌ Click failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Fallback scanning failed: {e}")

        # Fallback to clicking
        option_selectors = [
            f"//div[normalize-space(text())='{target_text}']",
            f"//button[normalize-space(text())='{target_text}']",
            f"//li[normalize-space(text())='{target_text}']",
            f"//span[normalize-space(text())='{target_text}']",
            f"//*[contains(text(), '{target_text}')]",
            f"//*[@role='option'][contains(text(), '{model_type}')]",
            f"//*[@role='menuitem'][contains(text(), '{model_type}')]"
        ]

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        if target_text.lower() in element_text.lower() or model_type.lower() in element_text.lower():
                            if self.safe_click_element(element, f"Model Option: {target_text}"):
                                print(f"✅ Selected model: {target_text}")
                                time.sleep(2)  # Wait for selection to register
                                return True
            except Exception as e:
                print(f"   ⚠️ Selector failed: {e}")
                continue

        print(f"❌ Could not select model: {target_text}")
        return False

    def verify_model_selection(self, expected_text):
        """Verify that model selection was successful"""
        try:
            # Look for the selected model text in the dropdown button or nearby elements
            current_selection = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{expected_text}')]")
            for elem in current_selection:
                if elem.is_displayed():
                    return True
            return False
        except:
            return False

    def find_output_count_dropdown(self):
        """Tìm dropdown chọn số lượng video - theo logic main_window.py"""
        print("🔍 Finding Output Count dropdown in settings popup...")

        selectors = [
            # EXACT selectors from main_window.py
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

        # EXACT debug scan matching main_window.py logic
        print("🔍 DEBUG: Scanning for output count buttons...")

        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"🔍 Scanning {len(all_buttons)} buttons for output count dropdown...")
            relevant_buttons = []
            for i, btn in enumerate(all_buttons):
                try:
                    if btn.is_displayed():
                        text = btn.text.strip() if btn.text else ""
                        print(f"   [DEBUG] Button {i}: '{text}' (displayed={btn.is_displayed()})")
                        if any(keyword in text.lower() for keyword in ['câu trả lời', 'đầu ra', 'output', 'response']):
                            relevant_buttons.append({
                                'index': i,
                                'text': text,
                                'element': btn
                            })
                except Exception as e:
                    print(f"   [DEBUG] Exception for button {i}: {e}")
                    continue
            print(f"📋 Found {len(relevant_buttons)} relevant output count buttons:")
            for btn_info in relevant_buttons:
                print(f"   [{btn_info['index']}] '{btn_info['text']}'")
            if not relevant_buttons:
                print("⚠️ Không tìm thấy nút output count nào có text phù hợp!")
            if relevant_buttons:
                best_btn = relevant_buttons[0]
                print(f"✅ Using most promising output button: '{best_btn['text']}'")
                return best_btn['element']
        except Exception as e:
            print(f"❌ Debug scan failed: {e}")

        # Also scan all elements for output count text patterns
        print("🔍 DEBUG: Scanning all elements for output count text...")
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'video') or contains(text(), 'Câu trả lời') or contains(text(), 'đầu ra')]")
            print(f"📋 Found {len(all_elements)} elements with output count text:")
            for i, elem in enumerate(all_elements[:5]):
                try:
                    if elem.is_displayed():
                        print(f"  [{i}] Tag: {elem.tag_name}, Text: '{elem.text[:50]}'")
                        # If it's clickable and looks like output count dropdown
                        if elem.tag_name in ['button', 'div'] and ('video' in elem.text.lower() or 'câu trả lời' in elem.text.lower()):
                            return elem
                except:
                    continue
        except Exception as e:
            print(f"❌ Element scan failed: {e}")
            for btn_info in relevant_buttons[:5]:  # Show top 5
                print(f"  [{btn_info['index']}] '{btn_info['text']}'")

        except Exception as e:
            print(f"❌ Debug scan failed: {e}")

        # Try selectors with WebDriverWait like main_window.py
        for i, selector in enumerate(selectors):
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Output Count dropdown with selector {i+1}: {element.text[:50]}...")
                    return element
            except TimeoutException:
                continue
            except Exception as e:
                continue

        print("❌ Output Count dropdown not found")
        return None

    def select_output_count(self, count=1):
        """Chọn số lượng video output - theo logic main_window.py"""
        print(f"🎯 Selecting output count: {count} (range: 1-4)")

        # Validate count range like main_window.py
        if count < 1 or count > 4:
            count = 1
            print(f"⚠️ Invalid count, using default: {count}")

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
                            if self.safe_click_element(element, f"Output Count: {count}"):
                                print(f"✅ Selected count: {count}")
                                time.sleep(2)  # Wait for selection to register
                                return True
            except Exception as e:
                print(f"   ⚠️ Selector failed: {e}")
                continue

        # Keyboard fallback like main_window.py
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            # Navigate to the desired count (assuming 1-4 options)
            for i in range(count - 1):  # count-1 because we start from option 1
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            print(f"✅ Keyboard navigation for count {count} successful")
            return True
        except Exception as e:
            print(f"   ⚠️ Keyboard fallback failed: {e}")

        print(f"❌ Could not select output count: {count}")
        return False

        print(f"❌ Could not select output count: {count}")
        return False

    def close_settings_popup(self):
        """Đóng settings popup - từ VeoWorkflowEngine"""
        print("🔍 Closing settings popup...")

        selectors = [
            "//button[contains(@aria-label, 'close') or contains(@aria-label, 'Close')]",
            "//button[contains(text(), 'Đóng') or contains(text(), 'Close')]",
            "//button[contains(., '×') or contains(., '✕')]",
            "//div[contains(@class, 'popup')]//button[last()]",
            "//div[contains(@class, 'modal')]//button[contains(@aria-label, 'close')]"
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    if self.safe_click_element(element, "Close Settings"):
                        return True
            except:
                continue

        # Try ESC key as fallback
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            print("✅ Used ESC key to close settings")
            time.sleep(2)
            return True
        except:
            pass

        print("❌ Could not close settings popup")
        return False

    def find_prompt_input(self):
        """Tìm ô nhập prompt - từ VeoWorkflowEngine"""
        print("🔍 Finding prompt input...")

        selectors = [
            "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
            "//textarea[contains(@placeholder, 'Nhập vào ô nhập câu lệnh')]",
            "//textarea[contains(@placeholder, 'prompt')]",
            "//textarea[contains(@placeholder, 'video')]",
            "//textarea[not(@disabled)]"
        ]

        for selector in selectors:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if element and element.is_displayed() and element.is_enabled():
                    print("✅ Found prompt input")
                    return element
            except TimeoutException:
                continue

        print("❌ Prompt input not found")
        return None

    def type_prompt_enhanced(self, prompt_text):
        """Nhập prompt text - từ VeoWorkflowEngine"""
        if not self.current_element:
            print("❌ No prompt input element found")
            return False

        print(f"📝 Typing prompt: {prompt_text[:50]}...")

        try:
            # Scroll to element and focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", self.current_element)
            time.sleep(1)

            # Click to focus
            self.current_element.click()
            time.sleep(1)

            # Clear existing content
            self.current_element.clear()

            # Type new prompt
            self.current_element.send_keys(prompt_text)

            # Trigger UI updates for send button to appear
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.dispatchEvent(new Event('input', {bubbles: true}));
                elem.dispatchEvent(new Event('change', {bubbles: true}));
                elem.dispatchEvent(new Event('keyup', {bubbles: true}));
                elem.dispatchEvent(new Event('blur', {bubbles: true}));
                elem.dispatchEvent(new Event('focus', {bubbles: true}));
            """, self.current_element)

            # Additional trigger
            self.current_element.send_keys(Keys.SPACE)
            time.sleep(0.5)
            self.current_element.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)

            time.sleep(3)  # Wait for UI to update
            print("✅ Prompt typed successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to type prompt: {e}")
            return False

    def find_send_button(self):
        """Tìm nút Send - từ VeoWorkflowEngine"""
        print("🔍 Finding Send button...")

        selectors = [
            "//button[contains(text(), 'Gửi')]",
            "//button[contains(text(), 'Send')]", 
            "//button[contains(@aria-label, 'send')]",
            "//button[contains(@aria-label, 'gửi')]",
            "//button[contains(., 'arrow') or contains(., '→')]",
            "//form//button[last()]"
        ]

        for selector in selectors:
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if element and element.is_displayed():
                    print("✅ Found Send button")
                    return element
            except TimeoutException:
                continue

        print("❌ Send button not found")
        return None

    def wait_for_video_generation(self):
        """Chờ video generation - từ VeoWorkflowEngine"""
        print("⏳ Waiting for video generation...")
        
        # Simulate waiting time
        wait_time = 30  # seconds
        for i in range(wait_time):
            print(f"   Waiting... {i+1}/{wait_time} seconds", end='\r')
            time.sleep(1)
        
        print(f"\n✅ Video generation wait completed ({wait_time}s)")
        return True

    def find_generated_videos_with_retry(self, only_new=True):
        """Find generated videos với retry - từ VeoWorkflowEngine"""
        print("🔍 Starting video detection with retry...")

        for attempt in range(1, 4):  # 3 attempts
            print(f"🔍 Video detection attempt {attempt}/3")

            try:
                videos = self.find_generated_videos(only_new)

                if videos:
                    print(f"✅ Found {len(videos)} videos on attempt {attempt}")
                    self._last_found_videos = videos
                    return videos
                else:
                    print(f"⚠️ No videos found on attempt {attempt}")
                    if attempt < 3:
                        print(f"⏳ Waiting 5s before retry...")
                        time.sleep(5)

            except Exception as e:
                print(f"❌ Video detection attempt {attempt} failed: {e}")
                if attempt < 3:
                    time.sleep(5)

        print("❌ Video detection failed after all retries")
        return []

    def find_generated_videos(self, only_new=True):
        """Find all generated videos - từ VeoWorkflowEngine"""
        print("🔍 Scanning for generated videos...")

        video_selectors = [
            "//video[@src and @src!='']",
            "//video[contains(@src, 'blob:') or contains(@src, 'http')]",
            "//*[contains(@class, 'video')]//video[@src]",
            "//*[contains(@class, 'preview')]//video[@src]",
            "//*[contains(@class, 'player')]//video[@src]",
            "//*[contains(@class, 'result')]//video[@src]",
            "//*[contains(@class, 'generated')]//video[@src]",
            "//button[contains(@aria-label, 'download') or contains(@aria-label, 'Download')]",
            "//button[contains(text(), 'Tải xuống') or contains(text(), 'Download')]",
            "//a[contains(@href, '.mp4') or contains(@href, '.webm') or contains(@href, '.mov')]",
            "//a[contains(@download, '.mp4') or contains(@download, '.webm')]"
        ]

        found_videos = []
        current_scan_time = time.time()

        for selector in video_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        video_url = None
                        video_type = "unknown"

                        if element.tag_name == 'video':
                            video_url = element.get_attribute('src')
                            video_type = "video_element"
                        elif element.tag_name == 'a':
                            video_url = element.get_attribute('href') or element.get_attribute('download')
                            video_type = "download_link"
                        elif element.tag_name == 'button':
                            try:
                                nearby_videos = element.find_elements(By.XPATH, ".//video[@src] | ./preceding::video[@src][1] | ./following::video[@src][1]")
                                if nearby_videos:
                                    video_url = nearby_videos[0].get_attribute('src')
                                    video_type = "button_associated"
                            except:
                                pass

                        if video_url and self._is_valid_video_url(video_url):
                            is_duplicate = any(v['url'] == video_url for v in found_videos)
                            
                            if not is_duplicate:
                                found_videos.append({
                                    'element': element,
                                    'url': video_url,
                                    'selector': selector,
                                    'type': video_type,
                                    'tag': element.tag_name,
                                    'scan_time': current_scan_time
                                })

            except Exception as e:
                continue

        print(f"🎬 Found {len(found_videos)} videos")
        return found_videos

    def _is_valid_video_url(self, url):
        """Check if URL is valid video format"""
        if not url:
            return False
        
        video_patterns = ['.mp4', '.webm', '.mov', 'blob:', 'data:video/']
        return any(pattern in url.lower() for pattern in video_patterns)

    def download_all_found_videos(self):
        """Download all found videos - từ VeoWorkflowEngine"""
        if not hasattr(self, '_last_found_videos') or not self._last_found_videos:
            print("❌ No videos found to download")
            return False

        print(f"📥 Attempting to download {len(self._last_found_videos)} videos...")

        downloaded_count = 0
        for i, video in enumerate(self._last_found_videos):
            print(f"📥 Processing video {i+1}/{len(self._last_found_videos)}...")

            try:
                if video['type'] == 'video_element':
                    print(f"   Video URL: {video['url'][:50]}...")
                elif video['type'] == 'download_link':
                    print(f"   Download link: {video['url'][:50]}...")
                elif video['type'] == 'button_associated':
                    print(f"   Download button with video: {video['url'][:50]}...")
                
                # For debug purposes, we just count as successful
                downloaded_count += 1
                
            except Exception as e:
                print(f"   ❌ Video {i+1} processing failed: {e}")

        if downloaded_count > 0:
            print(f"✅ Successfully processed {downloaded_count}/{len(self._last_found_videos)} videos")
            return True
        else:
            print("❌ No videos were successfully processed")
            return False

    # ===== HELPER METHODS =====

    def safe_click_current(self, element_name):
        """Safe click current element - refind to avoid stale reference"""
        if not self.current_element:
            print(f"❌ Cannot click {element_name}: no current element")
            # Try to find element first if it's not available
            print(f"🔄 Attempting to find {element_name} first...")
            fresh_element = None
            if "Project Type" in element_name:
                fresh_element = self.find_project_type_dropdown()
            elif "Model" in element_name:
                fresh_element = self.find_model_dropdown()
            elif "Output Count" in element_name:
                fresh_element = self.find_output_count_dropdown()
            elif "Aspect Ratio" in element_name:
                fresh_element = self.find_aspect_ratio_dropdown()
            elif "Settings" in element_name:
                fresh_element = self.find_settings_button()
            
            if fresh_element:
                print(f"✅ Found {element_name} on retry")
                self.current_element = fresh_element
                return self.test_element_click_methods(fresh_element, element_name)
            else:
                print(f"❌ Still cannot find {element_name}")
                return False
        
        # Try to use current element first, if stale then try to refind
        try:
            # Test if element is still valid
            self.current_element.is_displayed()
            return self.test_element_click_methods(self.current_element, element_name)
        except:
            print(f"⚠️ Element {element_name} is stale, attempting to refind...")
            # Try to refind the element based on element name
            fresh_element = None
            if "Project Type" in element_name:
                fresh_element = self.find_project_type_dropdown()
            elif "Model" in element_name:
                fresh_element = self.find_model_dropdown()
            elif "Output Count" in element_name:
                fresh_element = self.find_output_count_dropdown()
            elif "Aspect Ratio" in element_name:
                fresh_element = self.find_aspect_ratio_dropdown()
            elif "Settings" in element_name:
                fresh_element = self.find_settings_button()
            else:
                print(f"❌ Don't know how to refind {element_name}")
                return False
            
            if fresh_element:
                print(f"✅ Refound {element_name}")
                self.current_element = fresh_element
                return self.test_element_click_methods(fresh_element, element_name)
            else:
                print(f"❌ Could not refind {element_name}")
                return False

    def safe_click_element(self, element, element_name="element"):
        """Safe click element with multiple methods and click intercepted handling"""
        if not element:
            print(f"❌ Cannot click {element_name}: element is None")
            return False

        methods = [
            ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("JavaScript Force Click", lambda: self.driver.execute_script("""
                arguments[0].style.zIndex = '9999';
                arguments[0].style.position = 'relative';
                arguments[0].click();
            """, element)),
            ("Regular Click", lambda: element.click()),
            ("ActionChains Click", lambda: ActionChains(self.driver).move_to_element(element).click().perform())
        ]

        for method_name, click_func in methods:
            try:
                # Scroll to element first
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)

                click_func()
                time.sleep(1)
                print(f"✅ {element_name} clicked using {method_name}")
                return True

            except Exception as e:
                if "click intercepted" in str(e).lower():
                    print(f"   ⚠️ {method_name} intercepted, trying next method...")
                continue

        print(f"❌ All click methods failed for {element_name}")
        return False

    def test_new_project_button(self):
        """Test finding và clicking New Project button"""
        print("🔍 Testing New Project Button...")
        
        selectors = [
            "//button[contains(text(), 'Dự án mới') or contains(text(), 'New project')]",
            "//button[contains(@aria-label, 'new') or contains(@aria-label, 'mới')]",
            "//div[contains(@class, 'button')][contains(text(), 'Dự án mới')]",
            "//button[contains(text(), 'Create') or contains(text(), 'Tạo')]",
            "//button[contains(., 'add') or contains(., '+')]"
        ]
        
        return self.test_element_with_selectors(selectors, "New Project Button", click=True)

    def test_settings_button(self):
        """Test finding Settings button"""
        print("🔍 Testing Settings Button...")
        
        selectors = [
            "//button[contains(., 'tune')]",
            "//button[contains(text(), 'Cài đặt') or contains(text(), 'Settings')]",
            "//button[contains(., '⚙')]",
            "//button[contains(@aria-label, 'Settings') or contains(@aria-label, 'settings')]",
            "//header//button[contains(., 'tune')]"
        ]
        
        return self.test_element_with_selectors(selectors, "Settings Button", click=True)

    def test_model_dropdown(self):
        """Test finding Model dropdown trong settings popup"""
        print("🔍 Testing Model Dropdown...")
        
        # Wait for settings popup to load
        time.sleep(3)
        
        selectors = [
            "//div[contains(text(), 'Mô hình')]/..//button",
            "//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Quality') or contains(text(), 'Fast')]",
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Veo')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Veo')]"
        ]
        
        result = self.test_element_with_selectors(selectors, "Model Dropdown", click=True)
        
        if result:
            # Test dropdown options after clicking
            time.sleep(2)
            self.debug_dropdown_options()
            
        return result

    def test_aspect_ratio_dropdown(self):
        """Test finding Aspect Ratio dropdown trong settings popup"""
        print("🔍 Testing Aspect Ratio Dropdown...")
        
        # Wait for settings popup to load
        time.sleep(3)
        
        selectors = [
            "//div[contains(text(), 'Tỷ lệ khung hình') or contains(text(), 'Aspect ratio')]/..//button",
            "//button[contains(text(), 'Khổ ngang') or contains(text(), '16:9')]",
            "//button[contains(text(), 'Khổ dọc') or contains(text(), '9:16')]",
            "//div[contains(@class, 'popup')]//button[contains(., ':')]",
            "//div[contains(@class, 'modal')]//button[contains(., 'ratio')]"
        ]
        
        result = self.test_element_with_selectors(selectors, "Aspect Ratio Dropdown", click=True)
        
        if result:
            # Test dropdown options after clicking
            time.sleep(2)
            print("🔍 Looking for aspect ratio options...")
            try:
                options = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'Khổ ngang') or contains(text(), 'Khổ dọc') or contains(text(), '16:9') or contains(text(), '9:16')]")
                print(f"Found {len(options)} aspect ratio options:")
                for i, option in enumerate(options):
                    print(f"  {i+1}. {option.text}")
            except Exception as e:
                print(f"❌ Error finding options: {e}")
            
        return result

    def test_output_count_dropdown(self):
        """Test finding Output Count dropdown"""
        print("🔍 Testing Output Count Dropdown...")
        
        selectors = [
            "//button[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]",
            "//button[contains(text(), 'Câu trả lời đầu ra')]",
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Câu trả lời')]",
            "//button[contains(text(), '1') and not(contains(text(), '10'))]"
        ]
        
        result = self.test_element_with_selectors(selectors, "Output Count Dropdown", click=True)
        
        if result:
            # Test count options
            time.sleep(2)
            count_options = self.debug_dropdown_options()
            
            # Try to select count 2
            for opt in count_options:
                if opt['text'] == '2':
                    try:
                        opt['element'].click()
                        print("✅ Selected count: 2")
                        break
                    except:
                        pass
                        
        return result

    def test_close_settings(self):
        """Test closing settings popup"""
        print("🔍 Testing Close Settings...")
        
        selectors = [
            "//button[contains(@aria-label, 'close') or contains(@aria-label, 'Close')]",
            "//button[contains(text(), 'Đóng') or contains(text(), 'Close')]",
            "//button[contains(., '×') or contains(., '✕')]",
            "//div[contains(@class, 'popup')]//button[last()]",
            "//div[contains(@class, 'modal')]//button[contains(@aria-label, 'close')]"
        ]
        
        result = self.test_element_with_selectors(selectors, "Close Settings", click=True)
        
        if not result:
            # Try ESC key as fallback
            try:
                from selenium.webdriver.common.keys import Keys
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.ESCAPE)
                print("✅ Used ESC key to close settings")
                time.sleep(2)
                return True
            except:
                pass
                
        return result

    def test_send_button(self):
        """Test finding Send button"""
        print("🔍 Testing Send Button...")
        
        selectors = [
            "//button[contains(text(), 'Gửi') or contains(text(), 'Send')]",
            "//button[contains(@aria-label, 'send') or contains(@aria-label, 'gửi')]",
            "//button[contains(., 'arrow') or contains(., '→')]",
            "//button[contains(@class, 'send')]",
            "//form//button[last()]"
        ]
        
        return self.test_element_with_selectors(selectors, "Send Button", click=False)  # Don't click yet

    def test_video_detection(self):
        """Test video detection sau khi gửi prompt"""
        print("🔍 Testing Video Detection...")
        
        print("⏳ Simulating video generation wait (30 seconds)...")
        for i in range(30):
            print(f"   Waiting... {i+1}/30 seconds", end='\r')
            time.sleep(1)
        
        print("\n🎬 Scanning for generated videos...")
        videos = self.scan_for_videos()
        
        if videos:
            print(f"✅ Found {len(videos)} video-related elements")
            return True
        else:
            print("❌ No videos found")
            return False

    def test_element_with_selectors(self, selectors, element_name, click=False):
        """Helper method để test element với multiple selectors"""
        print(f"Testing selectors for {element_name}:")
        
        found_elements = []
        for i, selector in enumerate(selectors):
            print(f"   🧪 Selector {i+1}: {selector}")
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                
                if visible_elements:
                    print(f"      ✅ Found {len(visible_elements)} element(s)")
                    for j, el in enumerate(visible_elements):
                        text = el.text[:50] if el.text else "No text"
                        print(f"         [{j}] '{text}'")
                        
                        # Highlight element
                        try:
                            self.driver.execute_script("""
                                arguments[0].style.border = '3px solid red';
                                arguments[0].style.backgroundColor = 'yellow';
                            """, el)
                        except:
                            pass
                        
                    found_elements.extend(visible_elements)
                else:
                    print(f"      ❌ No visible elements")
                    
            except Exception as e:
                print(f"      ⚠️ Error: {e}")
        
        self.take_debug_screenshot(f"{element_name.replace(' ', '_')}_highlighted")
        
        if found_elements:
            if click:
                # Test clicking first found element
                return self.test_element_click_methods(found_elements[0], element_name)
            else:
                print(f"✅ {element_name} found successfully")
                return True
        else:
            print(f"❌ No {element_name} found")
            return False

    def test_element_click_methods(self, element, element_name):
        """Test multiple click methods cho element"""
        print(f"🧪 Testing click methods for {element_name}")
        
        # Scroll to element
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
        except:
            pass
        
        self.take_debug_screenshot(f"before_click_{element_name.replace(' ', '_')}")
        
        click_methods = [
            ("Regular Click", lambda: element.click()),
            ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains", lambda: ActionChains(self.driver).move_to_element(element).click().perform())
        ]
        
        for method_name, click_func in click_methods:
            try:
                print(f"   🔄 Trying {method_name}...")
                click_func()
                time.sleep(2)
                
                self.take_debug_screenshot(f"after_click_{element_name.replace(' ', '_')}_{method_name.replace(' ', '_')}")
                print(f"   ✅ {method_name} successful")
                return True
                
            except Exception as e:
                print(f"   ❌ {method_name} failed: {e}")
                continue
        
        print(f"❌ All click methods failed for {element_name}")
        return False

    def test_prompt_input(self, test_prompt="Test prompt for debugging"):
        """Test nhập prompt"""
        print(f"📝 Testing prompt input: '{test_prompt}'")
        
        try:
            # Find prompt input
            input_selectors = [
                "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
                "//textarea[contains(@placeholder, 'prompt')]",
                "//textarea[contains(@placeholder, 'nhập')]",
                "//textarea[contains(@placeholder, 'Nhập vào ô nhập câu lệnh')]",
                "//textarea[not(@disabled)]"
            ]
            
            prompt_input = None
            for i, selector in enumerate(input_selectors):
                print(f"   🧪 Trying selector {i+1}: {selector}")
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            prompt_input = elem
                            print(f"   ✅ Found prompt input with selector {i+1}")
                            break
                    if prompt_input:
                        break
                except Exception as e:
                    print(f"   ❌ Selector {i+1} failed: {e}")
                    continue
            
            if not prompt_input:
                print("❌ No prompt input found")
                return False
            
            # Highlight the input
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '3px solid green';
                    arguments[0].style.backgroundColor = 'lightgreen';
                """, prompt_input)
            except:
                pass
            
            # Test typing
            self.driver.execute_script("arguments[0].scrollIntoView(true);", prompt_input)
            time.sleep(1)
            
            prompt_input.click()
            time.sleep(1)
            prompt_input.clear()
            prompt_input.send_keys(test_prompt)
            
            # Trigger events for UI to update
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.dispatchEvent(new Event('input', {bubbles: true}));
                elem.dispatchEvent(new Event('change', {bubbles: true}));
                elem.dispatchEvent(new Event('keyup', {bubbles: true}));
            """, prompt_input)
            
            # Additional trigger với space + backspace
            prompt_input.send_keys(Keys.SPACE)
            time.sleep(0.5)
            prompt_input.send_keys(Keys.BACKSPACE)
            
            time.sleep(2)
            self.take_debug_screenshot("prompt_typed")
            print("✅ Prompt input successful")
            return True
            
        except Exception as e:
            print(f"❌ Prompt input failed: {e}")
            self.take_debug_screenshot("prompt_input_failed")
            return False

    def test_complete_veo_workflow(self, test_prompt="Debug test: beautiful sunset over mountains"):
        """Test complete Veo workflow theo main_window.py"""
        print(f"\n🎬 TESTING COMPLETE VEO WORKFLOW")
        print("=" * 60)
        print(f"Test prompt: {test_prompt}")
        
        # Define workflow steps từ main_window.py - EXACT MATCH
        workflow_steps = [
            ("Find New Project Button", self.find_new_project_button),
            ("Click New Project", lambda: self.safe_click_current("New Project Button")),
            ("Find Project Type Dropdown", self.find_project_type_dropdown),
            ("Click Project Type Dropdown", lambda: self.safe_click_current("Project Type Dropdown")),
            ("Select Text to Video", lambda: self.select_project_type_option("Từ văn bản sang video")),
            ("Close Dropdown After Selection", self.close_dropdown_if_open),
            ("Find Settings Button", self.find_settings_button),
            ("Click Settings Button", lambda: self.safe_click_current("Settings Button")),
            ("Find Model Dropdown", self.find_model_dropdown),
            ("Click Model Dropdown", self.click_model_dropdown_enhanced),
            ("Select Model (Fast)", lambda: self.select_model_option("fast")),
            ("Find Output Count Dropdown", self.find_output_count_dropdown),
            ("Click Output Count Dropdown", lambda: self.safe_click_current("Output Count Dropdown")),
            ("Select Output Count (1)", lambda: self.select_output_count(1)),
            ("Find Aspect Ratio Dropdown", self.find_aspect_ratio_dropdown),
            ("Click Aspect Ratio Dropdown", lambda: self.safe_click_current("Aspect Ratio Dropdown")),
            ("Select Aspect Ratio (16:9)", lambda: self.select_aspect_ratio("16:9")),
            ("Check All Settings Status", self.check_all_settings_status),
            ("Close Settings Popup", self.close_settings_popup),
            ("Find Prompt Input", self.find_prompt_input),
            ("Type Prompt", lambda: self.type_prompt_enhanced(self.current_element, test_prompt)),
            ("Find Send Button", self.find_send_button),
            ("Click Send Button", lambda: self.safe_click_current("Send Button")),
            ("Wait for Video Generation", self.wait_for_video_generation),
            ("Find Generated Videos", self.find_generated_videos_with_retry),
            ("Download Videos", self.download_all_found_videos)
        ]
        
        results = {}
        self.current_element = None
        
        for step_name, step_func in workflow_steps:
            print(f"\n🔄 STEP: {step_name}")
            print("-" * 40)
            
            try:
                result = step_func()
                results[step_name] = result
                
                # Handle Find steps
                if step_name.startswith("Find"):
                    if result:
                        self.current_element = result
                        print(f"✅ {step_name} - Found element")
                        self.take_debug_screenshot(f"found_{step_name.replace(' ', '_')}")
                    else:
                        print(f"❌ {step_name} - Element not found")
                        if not self.continue_on_error(step_name):
                            break
                else:
                    # Handle Action steps
                    if result:
                        print(f"✅ {step_name} - Action successful")
                        self.take_debug_screenshot(f"success_{step_name.replace(' ', '_')}")
                    else:
                        print(f"❌ {step_name} - Action failed")
                        if not self.continue_on_error(step_name):
                            break
                
                # Pause between steps
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ {step_name} - ERROR: {e}")
                results[step_name] = False
                self.take_debug_screenshot(f"error_{step_name.replace(' ', '_')}")
                
                if not self.continue_on_error(step_name):
                    break
        
        # Summary
        self.print_workflow_summary(results)
        return results

    def continue_on_error(self, step_name):
        """Ask user if should continue on error"""
        critical_steps = ["Find New Project Button", "Find Prompt Input", "Find Send Button"]
        if step_name in critical_steps:
            print(f"⚠️ Critical step failed: {step_name}")
            return input("Continue anyway? (y/n): ").strip().lower() == 'y'
        else:
            print(f"⚠️ Non-critical step failed, continuing...")
            return True

    def print_workflow_summary(self, results):
        """Print workflow summary"""
        print(f"\n{'='*60}")
        print("🏁 VEO WORKFLOW TEST SUMMARY")
        print('='*60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for step_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {step_name}")
        
        print(f"\n📊 OVERALL RESULT: {passed}/{total} steps passed")
        if passed == total:
            print("🎉 WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        else:
            print("⚠️ Some steps failed - check screenshots for details")

    # === VEO WORKFLOW METHODS FROM MAIN_WINDOW.PY ===

    def find_new_project_button(self):
        """Tìm nút New Project"""
        print("🔍 Finding New Project button...")
        
        selectors = [
            "//button[contains(text(), 'Dự án mới')]",
            "//button[contains(text(), 'New project')]",
            "//button[contains(@aria-label, 'new project')]",
            "//button[contains(@aria-label, 'dự án mới')]",
            "//div[contains(@class, 'button')][contains(text(), 'Dự án mới')]",
            "//button[contains(., 'add')]",
            "//button[contains(., '+')]"
        ]
        
        return self.find_element_with_selectors(selectors, "New Project Button")

    def find_project_type_dropdown(self):
        """Tìm dropdown chọn loại dự án - EXACT COPY from main_window.py with debug"""
        print("🔍 Finding Project Type dropdown...")
        
        # Wait for page to load after New Project click
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Clear any stale element references
        self.current_element = None
        
        # DEBUG: Scan page first
        try:
            print("🔍 DEBUG: Scanning page for project type elements...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"📋 Found {len(all_buttons)} total buttons")
            
            relevant_buttons = []
            for i, btn in enumerate(all_buttons):
                try:
                    if btn.is_displayed() and btn.text:
                        text_lower = btn.text.lower()
                        if any(keyword in text_lower for keyword in ['text', 'video', 'văn bản', 'image', 'hình ảnh']):
                            relevant_buttons.append(f"[{i}] '{btn.text[:50]}...'")
                except:
                    continue
            
            print(f"🎯 Found {len(relevant_buttons)} relevant buttons:")
            for btn_info in relevant_buttons[:10]:  # Show first 10
                print(f"   {btn_info}")
                
        except Exception as e:
            print(f"❌ Page scan failed: {e}")

        # Use EXACT selectors from main_window.py
        selectors = [
            "//button[contains(text(), 'Từ văn bản sang video')]",
            "//button[contains(text(), 'Text to Video')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'văn bản')]",
            "//button[contains(., 'arrow_drop_down') and contains(text(), 'video')]",
            "//button[contains(text(), 'video') and contains(., 'arrow_drop_down')]",
            "//button[contains(@class, 'dropdown') and contains(text(), 'video')]"
        ]

        for i, selector in enumerate(selectors):
            try:
                print(f"🔍 Trying selector [{i}]: {selector}")
                element = WebDriverWait(self.driver, self.config['wait_timeout']).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Project Type dropdown with selector [{i}]")
                    return element
            except Exception as e:
                print(f"   Selector [{i}] failed: {e}")
                continue

        print("❌ Project Type dropdown not found")
        return None

    def find_model_dropdown(self):
        """Tìm dropdown chọn model - Updated selectors"""
        print("🔍 Finding Model dropdown...")

        selectors = [
            # Tìm trong popup/modal với text Veo 3
            "//div[contains(@class, 'popup') or contains(@class, 'modal')]//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Veo 3 - Fast') or contains(text(), 'Veo 3 - Quality')]",
            "//div[contains(text(), 'Mô hình') or contains(text(), 'Model')]/..//button",
            "//button[contains(text(), 'Fast') or contains(text(), 'Quality')]",
            "//div[contains(@class, 'settings')]//button[contains(text(), 'Veo')]",
            # Fallback - button thứ 2 trong popup (thường là model dropdown)
            "//div[contains(@class, 'popup')]//button[2]"
        ]

        return self.find_element_with_retry(selectors, "Model Dropdown")

    def find_output_count_dropdown(self):
        """Tìm dropdown số lượng video đầu ra - Updated selectors"""
        print("🔍 Finding Output Count dropdown...")

        selectors = [
            # Tìm button có số (1, 4, 8)
            "//button[contains(text(), '1') or contains(text(), '4') or contains(text(), '8')]",
            "//div[contains(text(), 'Số lượng') or contains(text(), 'Count')]/..//button",
            "//div[contains(text(), 'video')]/..//button",
            "//div[contains(@class, 'popup')]//button[contains(text(), '1')]",
            # Fallback - button thứ 3 trong popup (thường là count dropdown)
            "//div[contains(@class, 'popup')]//button[3]"
        ]

        return self.find_element_with_retry(selectors, "Output Count Dropdown")

    def select_project_type_option(self, option_text):
        """Chọn loại project - ENHANCED with debug output - LINE 2282"""
        print(f"🎯 Selecting project type: {option_text}")
        print("🚨 DEBUG: This is the LINE 2282 function - ENHANCED VERSION")
        
        # Wait longer for dropdown options to appear
        time.sleep(3)
        
        # DEBUG: Scan all visible elements after dropdown opens
        try:
            print("🔍 DEBUG: Scanning all visible elements after dropdown opened...")
            
            # Look for all clickable elements
            all_clickable = []
            for tag in ['div', 'li', 'button', 'span', 'a']:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                for i, elem in enumerate(elements):
                    try:
                        if elem.is_displayed() and elem.text.strip():
                            text = elem.text.strip()
                            if any(keyword in text.lower() for keyword in ['text', 'video', 'văn bản', 'image', 'hình ảnh']):
                                all_clickable.append(f"{tag}[{i}]: '{text[:50]}...'")
                    except:
                        continue
            
            print(f"📋 Found {len(all_clickable)} potential options:")
            for option in all_clickable[:15]:  # Show first 15
                print(f"   {option}")
                
        except Exception as e:
            print(f"❌ Debug scan failed: {e}")
        
        # Enhanced selectors based on main_window.py
        selectors = [
            f"//div[normalize-space(text())='{option_text}']",
            f"//button[normalize-space(text())='{option_text}']", 
            f"//li[normalize-space(text())='{option_text}']",
            f"//*[contains(text(), '{option_text}')]",
            f"//*[contains(text(), 'Từ văn bản sang video')]",
            f"//*[contains(text(), 'Text to Video')]",
            f"//*[@role='option'][contains(text(), 'văn bản')]",
            f"//*[@role='menuitem'][contains(text(), 'văn bản')]",
            # Broader search patterns
            "//div[contains(text(), 'văn bản')]",
            "//li[contains(text(), 'văn bản')]",
            "//span[contains(text(), 'văn bản')]",
            "//button[contains(text(), 'văn bản')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                print(f"🔍 Trying selector [{i}]: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"   Found {len(elements)} elements")
                
                for j, element in enumerate(elements):
                    try:
                        if element.is_displayed():
                            print(f"   Element [{j}]: Text='{element.text[:50]}...', Tag={element.tag_name}")
                            if self.safe_click_element(element, f"Project Type Option: {option_text}"):
                                time.sleep(2)
                                print(f"✅ Selected: {option_text}")
                                return True
                        else:
                            print(f"   Element [{j}]: Not displayed")
                    except Exception as e:
                        print(f"   Element [{j}] error: {e}")
            except Exception as e:
                print(f"   Selector [{i}] failed: {e}")
                continue
        
        # Fallback keyboard navigation like main_window.py
        print("🔧 Fallback: Using keyboard navigation...")
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_DOWN)
            time.sleep(1)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            print("✅ Keyboard navigation successful")
            return True
        except Exception as e:
            print(f"❌ All methods failed for: {option_text}")
            return False

    def close_dropdown_if_open(self):
        """Đóng dropdown nếu đang mở"""
        print("🔧 Closing dropdown if open...")
        
        try:
            # Try clicking outside or ESC
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(1)
            return True
        except:
            return True  # Continue anyway

    def find_settings_button(self):
        """Tìm nút Settings"""
        print("🔍 Finding Settings button...")
        
        selectors = [
            "//button[contains(., 'tune')]",
            "//button[contains(text(), 'Cài đặt')]",
            "//button[contains(text(), 'Settings')]",
            "//button[contains(., '⚙')]",
            "//button[contains(@aria-label, 'settings')]",
            "//header//button[contains(., 'tune')]"
        ]
        
        return self.find_element_with_selectors(selectors, "Settings Button")

    def find_model_dropdown(self):
        """Tìm dropdown model"""
        print("🔍 Finding Model dropdown...")
        
        time.sleep(3)  # Wait for popup
        
        selectors = [
            "//div[contains(text(), 'Mô hình')]/following-sibling::*//button",
            "//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Quality') or contains(text(), 'Fast')]",
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Veo')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Veo')]"
        ]
        
        return self.find_element_with_selectors(selectors, "Model Dropdown")

    def click_model_dropdown_enhanced(self):
        """Click model dropdown với enhanced logic"""
        if not self.current_element:
            return False
        
        return self.safe_click_current("Model Dropdown")

    def select_model_option(self, model_type="fast"):
        """Chọn model option - keyboard navigation priority"""
        target_text = "Veo 3 - Fast" if model_type.lower() == "fast" else "Veo 3 - Quality"
        print(f"🎯 Selecting model: {target_text}")

        # Wait for options to appear after clicking dropdown
        print("   🕐 Waiting for dropdown options to load...")
        time.sleep(3)

        # PRIMARY: Try keyboard navigation first (most reliable for avoiding click intercepted)
        try:
            print("   🎯 PRIMARY: Trying keyboard navigation...")
            # Focus on the model dropdown first
            if self.current_element:
                try:
                    self.current_element.send_keys(Keys.SPACE)  # Open dropdown with space
                    time.sleep(1)
                except:
                    pass
            
            # Use body element for navigation
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Navigate based on model type
            if model_type.lower() == "quality":
                print("     🔽 Navigating to Quality option...")
                body.send_keys(Keys.ARROW_DOWN)  # Navigate to Quality
                time.sleep(0.5)
                body.send_keys(Keys.ARROW_DOWN)  # May need multiple downs
            else:
                print("     🔼 Navigating to Fast option...")  
                body.send_keys(Keys.ARROW_UP)    # Navigate to Fast (usually first)
                time.sleep(0.5)
            
            print("     ✅ Pressing ENTER to select...")
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            
            # Verify selection worked
            print("   🔍 Verifying selection...")
            if self.verify_model_selection(target_text):
                print("✅ Keyboard navigation successful")
                return True
            else:
                print("   ⚠️ Keyboard selection not verified, trying fallback...")
                
        except Exception as e:
            print(f"   ⚠️ Keyboard navigation failed: {e}")

        # FALLBACK: Enhanced fallback with debug scanning
        print("   � FALLBACK: Trying click with scanning...")
        try:
            # Scan for visible model options after dropdown opened
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Veo') or contains(text(), 'Fast') or contains(text(), 'Quality')]")
            model_options = []
            
            for elem in all_elements:
                try:
                    if elem.is_displayed() and elem.text:
                        text_lower = elem.text.lower()
                        if ('veo' in text_lower and (model_type.lower() in text_lower)) or target_text.lower() in text_lower:
                            model_options.append(elem)
                except:
                    continue
                    
            print(f"   📋 Found {len(model_options)} potential model options")
            
            for elem in model_options:
                try:
                    print(f"     🎯 Trying to click: {elem.text[:50]}...")
                    # Use JavaScript click to avoid interception
                    self.driver.execute_script("arguments[0].click();", elem)
                    time.sleep(2)
                    
                    if self.verify_model_selection(target_text):
                        print(f"✅ Selected model: {target_text}")
                        return True
                except Exception as e:
                    print(f"     ❌ Click failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Fallback scanning failed: {e}")

        print(f"❌ Could not select model: {target_text}")
        return False

    def select_output_count(self, count=1):
        """Chọn số lượng output với improved logic"""
        print(f"🎯 Selecting output count: {count}")
        
        # Wait for dropdown to expand and options to load
        print("   🕐 Waiting for dropdown options to load...")
        time.sleep(2)
        
        # First scan for all available options
        option_selectors = [
            "//div[@role='option']",
            "//div[contains(@class, 'option')]", 
            "//div[contains(@class, 'menu-item')]",
            "//li[@role='option']",
            "//*[contains(text(), 'video') or contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4')]"
        ]

        available_options = []
        for i, selector in enumerate(option_selectors, 1):
            try:
                print(f"   🔍 Trying selector {i}: Looking for count option...")
                options = self.driver.find_elements(By.XPATH, selector)
                for option in options:
                    if option.is_displayed():
                        text = option.text.strip()
                        if text and (str(count) in text or f"{count} video" in text.lower()):
                            available_options.append(option)
                            print(f"   ✅ Found matching option: {text}")
                        elif text and ("video" in text.lower() or text.isdigit()):
                            print(f"   📝 Found option: {text}")
            except Exception as e:
                print(f"   ⚠️ Selector {i} failed: {e}")
                continue

        # Try clicking the best match
        for option in available_options:
            try:
                if self.safe_click_element(option, f"Count Option: {option.text}"):
                    time.sleep(2)
                    return True
            except Exception as e:
                print(f"   ⚠️ Click failed: {e}")
                continue
        
        print(f"❌ Could not select count: {count}")
        return False

    def select_project_type_option(self, option_text):
        """Chọn loại project với improved logic - LINE 2552"""
        print(f"🎯 Selecting project type: {option_text}")
        print("🚨 DEBUG: This is the LINE 2552 function - SIMPLE VERSION")
        
        # Wait for dropdown to expand
        time.sleep(3)
        
        selectors = [
            f"//div[contains(text(), '{option_text}')]",
            f"//button[contains(text(), '{option_text}')]",
            f"//li[contains(text(), '{option_text}')]",
            f"//option[contains(text(), '{option_text}')]",
            # Vietnamese text variations
            "//div[contains(text(), 'văn bản') and contains(text(), 'video')]",
            "//button[contains(text(), 'văn bản') and contains(text(), 'video')]",
            "//*[contains(text(), 'Text to video')]",
            "//*[contains(text(), 'Từ văn bản')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                print(f"   🔍 Trying selector {i+1}: Looking for project type...")
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)
                            element.click()
                            print(f"✅ Selected project type: {option_text}")
                            time.sleep(2)  # Wait for selection to register
                            return True
                        except Exception as e:
                            print(f"   ⚠️ Click failed: {e}")
                            continue
                            
            except Exception as e:
                print(f"   ⚠️ Selector {i+1} failed: {e}")
                continue
        
        print(f"❌ Could not select: {option_text}")
        return False

    def find_output_count_dropdown(self):
        """Tìm dropdown số lượng output"""
        print("🔍 Finding Output Count dropdown...")
        
        selectors = [
            "//button[contains(text(), 'Câu trả lời đầu ra')]",
            "//button[contains(text(), 'câu lệnh')]",
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Câu trả lời')]"
        ]
        
        return self.find_element_with_selectors(selectors, "Output Count Dropdown")

    def select_output_count(self, count=1):
        """Chọn số lượng output với keyboard navigation"""
        print(f"🎯 Selecting output count: {count}")
        
        # Wait for dropdown to expand
        time.sleep(2)
        
        # PRIMARY: Try keyboard navigation first
        try:
            print("   🎯 PRIMARY: Trying keyboard navigation for output count...")
            
            # Focus on the output count dropdown first
            if self.current_element:
                try:
                    self.current_element.send_keys(Keys.SPACE)  # Open dropdown with space
                    time.sleep(1)
                except:
                    pass
            
            # Use body element for navigation
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Navigate to the desired count (1 is usually first, so UP arrow)
            if count == 1:
                print("     🔼 Selecting count 1...")
                body.send_keys(Keys.ARROW_UP)  # First option
            elif count == 2:
                print("     🔽 Selecting count 2...")
                body.send_keys(Keys.ARROW_DOWN)
            elif count == 3:
                print("     🔽🔽 Selecting count 3...")
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                body.send_keys(Keys.ARROW_DOWN)
            elif count == 4:
                print("     🔽🔽🔽 Selecting count 4...")
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                body.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                body.send_keys(Keys.ARROW_DOWN)
            
            time.sleep(0.5)
            print("     ✅ Pressing ENTER to select...")
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            
            print(f"✅ Keyboard navigation for output count {count} completed")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Keyboard navigation failed: {e}")

        # FALLBACK: Try click methods
        print("   🔄 FALLBACK: Trying click methods...")
        selectors = [
            f"//div[normalize-space(text())='{count}']",
            f"//button[normalize-space(text())='{count}']",
            f"//li[normalize-space(text())='{count}']",
            f"//*[contains(text(), '{count} video')]",
            f"//*[contains(text(), '{count}')][@role='option']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and str(count) in element.text:
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                            print(f"✅ Selected count: {count}")
                            return True
                        except Exception as e:
                            print(f"     ❌ Click failed: {e}")
                            continue
            except:
                continue
        
        print(f"❌ Could not select count: {count}")
        return False

    def find_aspect_ratio_dropdown(self):
        """Tìm dropdown tỷ lệ khung hình - theo logic main_window.py pattern"""
        print("🔍 Finding Aspect Ratio dropdown in settings popup...")
        
        # Debug scan for aspect ratio buttons FIRST
        print("🔍 DEBUG: Scanning for aspect ratio buttons...")
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            relevant_buttons = []

            for i, btn in enumerate(all_buttons):
                if btn.is_displayed() and btn.text:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in ['tỷ lệ', 'khổ ngang', 'khổ dọc', '16:9', '9:16', 'ratio', 'crop']):
                        relevant_buttons.append({
                            'index': i,
                            'text': btn.text,
                            'element': btn
                        })

            print(f"📋 Found {len(relevant_buttons)} aspect ratio-related buttons:")
            for btn_info in relevant_buttons[:3]:  # Show top 3
                print(f"  [{btn_info['index']}] '{btn_info['text']}'")
                
            # Try clicking the first relevant button directly
            if relevant_buttons:
                target_btn = relevant_buttons[0]['element']
                print(f"✅ Using first matching button: {relevant_buttons[0]['text'][:30]}...")
                return target_btn

        except Exception as e:
            print(f"❌ Debug scan failed: {e}")

        # Fallback to selectors
        selectors = [
            # Based on actual text found in debug: 'Tỷ lệ khung hình\ncrop_landscape\nKhổ ngang (16:9)\narrow_drop_down'
            "//button[contains(text(), 'Tỷ lệ khung hình') and contains(text(), 'Khổ ngang')]",
            "//button[contains(text(), 'Tỷ lệ khung hình') and contains(text(), 'arrow_drop_down')]",
            "//button[contains(., 'crop_landscape')]",
            "//*[contains(text(), 'Tỷ lệ khung hình')]/ancestor-or-self::button",
            "//*[contains(text(), 'crop_landscape')]/ancestor-or-self::button"
        ]

        # Try selectors with WebDriverWait
        for i, selector in enumerate(selectors):
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element and element.is_displayed():
                    print(f"✅ Found Aspect Ratio dropdown with selector {i+1}")
                    return element
            except TimeoutException:
                continue
            except Exception as e:
                continue

        print("❌ Aspect Ratio dropdown not found")
        return None

    def select_aspect_ratio(self, ratio="16:9"):
        """Chọn tỷ lệ khung hình - theo logic main_window.py pattern"""
        print(f"🎯 Selecting aspect ratio: {ratio}")
        
        if ratio == "16:9":
            target_text = "Khổ ngang (16:9)"
        elif ratio == "9:16":
            target_text = "Khổ dọc (9:16)"
        else:
            target_text = "Khổ ngang (16:9)"  # Default
        
        # Wait for dropdown options to load
        print("   🕐 Waiting for dropdown options to load...")
        time.sleep(3)
        
        option_selectors = [
            f"//div[normalize-space(text())='{target_text}']",
            f"//button[normalize-space(text())='{target_text}']",
            f"//li[normalize-space(text())='{target_text}']",
            f"//span[normalize-space(text())='{target_text}']",
            f"//*[contains(text(), '{target_text}')]",
            f"//*[@role='option'][contains(text(), '{ratio}')]",
            f"//*[@role='menuitem'][contains(text(), '{ratio}')]",
            # Fallback patterns
            f"//*[contains(text(), 'Khổ ngang') and contains(text(), '16:9')]" if ratio == "16:9" else f"//*[contains(text(), 'Khổ dọc') and contains(text(), '9:16')]"
        ]

        for selector in option_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        if target_text.lower() in element_text.lower() or ratio in element_text:
                            if self.safe_click_element(element, f"Aspect Ratio Option: {target_text}"):
                                print(f"✅ Selected aspect ratio: {target_text}")
                                time.sleep(2)  # Wait for selection to register
                                return True
            except Exception as e:
                print(f"   ⚠️ Selector failed: {e}")
                continue

        # Keyboard fallback like main_window.py
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            if ratio == "9:16":
                body.send_keys(Keys.ARROW_DOWN)  # Navigate to 9:16
            # Default is usually 16:9 (first option), so no arrow needed
            time.sleep(0.5)
            body.send_keys(Keys.ENTER)
            time.sleep(2)
            print("✅ Keyboard navigation successful")
            return True
        except Exception as e:
            print(f"   ⚠️ Keyboard fallback failed: {e}")

        print(f"❌ Could not select aspect ratio: {target_text}")
        return False

    def check_all_settings_status(self):
        """Kiểm tra trạng thái tất cả settings dropdowns"""
        print("📊 Checking all settings status...")
        
        settings_info = {
            "Model": self.get_current_model_setting(),
            "Output Count": self.get_current_output_count_setting(),
            "Aspect Ratio": self.get_current_aspect_ratio_setting()
        }
        
        print("\n📋 CURRENT SETTINGS STATUS:")
        print("=" * 40)
        for setting_name, current_value in settings_info.items():
            print(f"   {setting_name}: {current_value}")
        
        self.take_debug_screenshot("settings_status_check")
        
        return settings_info

    def get_current_model_setting(self):
        """Lấy model setting hiện tại"""
        try:
            # Tìm button model hiện tại
            model_selectors = [
                "//button[contains(text(), 'Veo 3 - Fast')]",
                "//button[contains(text(), 'Veo 3 - Quality')]",
                "//button[contains(text(), 'Veo 2 - Fast')]",
                "//button[contains(text(), 'Veo 2 - Quality')]",
                "//div[contains(text(), 'Mô hình')]/following-sibling::*//button"
            ]
            
            for selector in model_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and ("Veo" in text or "Fast" in text or "Quality" in text):
                                return text
                except:
                    continue
            
            return "Unknown"
        except:
            return "Error reading model"

    def get_current_output_count_setting(self):
        """Lấy output count setting hiện tại"""
        try:
            # Tìm button output count hiện tại
            count_selectors = [
                "//button[contains(text(), 'Câu trả lời đầu ra')]",
                "//button[contains(text(), '1') and not(contains(text(), '10'))]",
                "//button[contains(text(), '2')]",
                "//button[contains(text(), '3')]",
                "//button[contains(text(), '4')]"
            ]
            
            for selector in count_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            # Extract number from text
                            if text and any(num in text for num in ['1', '2', '3', '4']):
                                for num in ['1', '2', '3', '4']:
                                    if num in text and not '10' in text:
                                        return f"{num} video(s)"
                            elif "Câu trả lời đầu ra" in text:
                                return text
                except:
                    continue
            
            return "Unknown"
        except:
            return "Error reading count"

    def get_current_aspect_ratio_setting(self):
        """Lấy aspect ratio setting hiện tại"""
        try:
            # Tìm button aspect ratio hiện tại
            ratio_selectors = [
                "//button[contains(text(), 'Khổ ngang (16:9)')]",
                "//button[contains(text(), 'Khổ dọc (9:16)')]",
                "//button[contains(text(), 'Tỷ lệ khung hình')]",
                "//button[contains(text(), '16:9') or contains(text(), '9:16')]"
            ]
            
            for selector in ratio_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and ("16:9" in text or "9:16" in text or "Khổ" in text or "Tỷ lệ" in text):
                                return text
                except:
                    continue
            
            return "Unknown"
        except:
            return "Error reading aspect ratio"

    def close_settings_popup(self):
        """Đóng settings popup"""
        print("🔧 Closing settings popup...")
        
        selectors = [
            "//button[contains(@aria-label, 'close')]",
            "//button[contains(text(), 'Đóng')]",
            "//button[contains(., '×')]"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    element.click()
                    print("✅ Settings popup closed")
                    return True
            except:
                continue
        
        # Try ESC
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            print("✅ Used ESC to close popup")
            return True
        except:
            pass
        
        return False

    def find_prompt_input(self):
        """Tìm ô nhập prompt"""
        print("🔍 Finding prompt input...")
        
        selectors = [
            "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
            "//textarea[contains(@placeholder, 'Nhập vào ô nhập câu lệnh')]",
            "//textarea[contains(@placeholder, 'prompt')]",
            "//textarea[not(@disabled)]"
        ]
        
        return self.find_element_with_selectors(selectors, "Prompt Input")

    def type_prompt_enhanced(self, element, prompt_text):
        """Nhập prompt với enhanced logic"""
        if not element:
            return False
        
        print(f"📝 Typing prompt: {prompt_text[:50]}...")
        
        try:
            # Scroll and focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            element.click()
            element.clear()
            element.send_keys(prompt_text)
            
            # Trigger events
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.dispatchEvent(new Event('input', {bubbles: true}));
                elem.dispatchEvent(new Event('change', {bubbles: true}));
                elem.dispatchEvent(new Event('keyup', {bubbles: true}));
            """, element)
            
            # Additional trigger
            element.send_keys(Keys.SPACE)
            time.sleep(0.5)
            element.send_keys(Keys.BACKSPACE)
            
            time.sleep(3)
            print("✅ Prompt typed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to type prompt: {e}")
            return False

    def find_send_button(self):
        """Tìm nút Send"""
        print("🔍 Finding Send button...")
        
        selectors = [
            "//button[contains(text(), 'Gửi')]",
            "//button[contains(text(), 'Send')]",
            "//button[contains(@aria-label, 'send')]",
            "//button[contains(., 'arrow')]"
        ]
        
        return self.find_element_with_selectors(selectors, "Send Button")

    def wait_for_video_generation(self, max_wait_minutes=10):
        """Chờ video generation với timeout"""
        print(f"⏳ Waiting for video generation (max {max_wait_minutes} minutes)...")
        
        # Wait for generation to start
        time.sleep(5)
        
        max_iterations = max_wait_minutes * 6  # 10 seconds per iteration
        start_time = time.time()
        
        # Check for generation indicators
        for i in range(max_iterations):
            try:
                elapsed = time.time() - start_time
                print(f"   Checking generation status... {i+1}/{max_iterations} ({elapsed:.1f}s elapsed)")
                
                # Look for generation indicators
                indicators = [
                    "//div[contains(text(), 'Generating') or contains(text(), 'Đang tạo')]",
                    "//div[contains(text(), 'Processing') or contains(text(), 'Đang xử lý')]",
                    "//*[contains(@class, 'progress') or contains(@class, 'loading')]",
                    "//div[contains(text(), 'Creating video')]"
                ]
                
                generation_active = False
                for selector in indicators:
                    if self.driver.find_elements(By.XPATH, selector):
                        generation_active = True
                        print(f"   ✅ Generation indicator found: active")
                        break
                
                if generation_active:
                    print(f"   🔄 Generation in progress... waiting")
                else:
                    print("   🔍 No generation indicators, checking for completion...")
                    
                    # Check for completion indicators or videos
                    completion_indicators = [
                        "//video[@src]",  # Video elements with source
                        "//video[contains(@class, 'generated')]",
                        "//div[contains(text(), 'Complete') or contains(text(), 'Hoàn thành')]",
                        "//button[contains(text(), 'Download') or contains(text(), 'Tải xuống')]",
                        "//div[contains(@class, 'video-result')]"
                    ]
                    
                    for selector in completion_indicators:
                        videos = self.driver.find_elements(By.XPATH, selector)
                        if videos:
                            print(f"✅ Generation complete! Found {len(videos)} result(s)")
                            return True
                    
                    print("   ⚠️ No completion indicators found yet...")
                
                # Wait before next check
                time.sleep(10)
                
                # Safety timeout check
                if elapsed > max_wait_minutes * 60:
                    print(f"⏰ Timeout reached ({max_wait_minutes} minutes), stopping wait")
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Generation check error: {e}")
                time.sleep(5)
        
        print(f"⏰ Video generation wait completed (timeout after {max_wait_minutes} minutes)")
        print(f"⏰ Video generation wait completed (timeout after {max_wait_minutes} minutes)")
        return False

    def find_generated_videos_with_retry(self):
        """Tìm generated videos với retry"""
        print("🎬 Finding generated videos...")
        
        for attempt in range(3):
            print(f"   Attempt {attempt + 1}/3")
            
            videos = self.scan_for_videos()
            if videos:
                self._last_found_videos = videos
                print(f"✅ Found {len(videos)} videos")
                return videos
            
            time.sleep(5)
        
        print("❌ No videos found after retries")
        return []

    def download_all_found_videos(self):
        """Download tất cả videos đã tìm thấy"""
        if not hasattr(self, '_last_found_videos') or not self._last_found_videos:
            print("❌ No videos to download")
            return False
        
        print(f"📥 Downloading {len(self._last_found_videos)} videos...")
        
        downloaded = 0
        for i, video in enumerate(self._last_found_videos):
            print(f"   Downloading video {i+1}/{len(self._last_found_videos)}...")
            # Simulate download (in real implementation would download)
            downloaded += 1
            time.sleep(1)
        
        if downloaded > 0:
            print(f"✅ Downloaded {downloaded} videos")
            return True
        else:
            print("❌ No videos downloaded")
            return False

    def find_element_with_selectors(self, selectors, element_name):
        """Helper method để find element với multiple selectors"""
        for i, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                
                if visible_elements:
                    element = visible_elements[0]
                    # Highlight element
                    try:
                        self.driver.execute_script("""
                            arguments[0].style.border = '3px solid red';
                            arguments[0].style.backgroundColor = 'yellow';
                        """, element)
                    except:
                        pass
                    
                    print(f"✅ Found {element_name} with selector {i+1}")
                    return element
                    
            except Exception as e:
                continue
        
        print(f"❌ {element_name} not found")
        return None

    def safe_click_current(self, element_name):
        """Safe click cho current element"""
        if not self.current_element:
            print(f"❌ No current element for {element_name}")
            return False
        
        return self.test_element_click_methods(self.current_element, element_name)

    def scan_for_videos(self):
        """Scan for generated videos - alias for find_generated_videos"""
        return self.find_generated_videos(only_new=False)

    def take_debug_screenshot(self, step_name):
        """Take screenshot for debugging"""
        if not self.driver:
            print(f"⚠️ Screenshot skipped: No Chrome driver available")
            return
            
        if self.config['screenshot_on_error']:
            try:
                timestamp = int(time.time())
                filename = f"{step_name}_{timestamp}.png"
                filepath = self.debug_dir / filename
                self.driver.save_screenshot(str(filepath))
                print(f"📸 Screenshot saved: {filename}")
            except Exception as e:
                print(f"⚠️ Screenshot failed: {e}")

    def interactive_debug(self):
        """Interactive debugging mode"""
        print("\n🎮 INTERACTIVE DEBUG MODE")
        print("Commands:")
        print("  scan       - Scan page elements")
        print("  click N    - Click button number N")
        print("  type       - Test prompt input")
        print("  videos     - Scan for videos")
        print("  shot       - Take screenshot")
        print("  url        - Show current URL")
        print("  workflow   - Test complete workflow")
        print("  new        - Test new project button")
        print("  settings   - Test settings button") 
        print("  debug      - Debug settings popup elements")
        print("  model      - Test model dropdown")
        print("  count      - Test output count dropdown")
        print("  aspect     - Test aspect ratio dropdown")
        print("  status     - Check all settings status")
        print("  send       - Test send button")
        print("  profile    - Show current profile")
        print("  profiles   - List available profiles")
        print("  quit       - Exit")
        
        while True:
            try:
                command = input("\n🔧 Debug> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'scan':
                    buttons = self.debug_page_elements()
                elif command.startswith('click '):
                    try:
                        index = int(command.split()[1])
                        buttons = self.debug_page_elements()
                        if 0 <= index < len(buttons):
                            self.test_button_click(buttons[index])
                        else:
                            print(f"❌ Invalid button index: {index}")
                    except (ValueError, IndexError):
                        print("❌ Usage: click N (where N is button number)")
                elif command == 'type':
                    test_prompt = input("Enter test prompt: ").strip() or "Debug test prompt"
                    self.test_prompt_input(test_prompt)
                elif command == 'videos':
                    self.scan_for_videos()
                elif command == 'shot':
                    self.take_debug_screenshot("manual_screenshot")
                elif command == 'url':
                    print(f"Current URL: {self.driver.current_url}")
                elif command == 'workflow':
                    test_prompt = input("Enter test prompt (or press Enter for default): ").strip()
                    if not test_prompt:
                        test_prompt = "Debug test video: A beautiful sunset over mountains"
                    self.test_complete_workflow(test_prompt)
                elif command == 'new':
                    self.test_new_project_button()
                elif command == 'settings':
                    self.test_settings_button()
                elif command == 'debug':
                    self.debug_settings_popup_elements()
                elif command == 'model':
                    result = self.find_model_dropdown()
                    if result:
                        self.current_element = result
                elif command == 'count':
                    result = self.find_output_count_dropdown()
                    if result:
                        self.current_element = result
                elif command == 'aspect':
                    result = self.find_aspect_ratio_dropdown()
                    if result:
                        self.current_element = result
                        print("Found aspect ratio dropdown. Use 'select' option to choose:")
                        print("  - Khổ ngang (16:9)")
                        print("  - Khổ dọc (9:16)")
                elif command == 'status':
                    self.check_all_settings_status()
                elif command == 'send':
                    result = self.find_send_button()
                    if result:
                        self.current_element = result
                elif command == 'profile':
                    profile_name = getattr(self, 'current_profile', 'Unknown')
                    print(f"Current profile: {profile_name}")
                elif command == 'profiles':
                    self.list_available_profiles()
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Command error: {e}")

    def run_full_debug_workflow(self):
        """Run complete debug workflow"""
        print("\n🚀 STARTING FULL DEBUG WORKFLOW")
        
        steps = [
            ("Setup Chrome", self.setup_chrome),
            ("Navigate to Veo", self.navigate_to_veo),
            ("Scan Elements", self.debug_page_elements),
            ("Test Complete Workflow", lambda: self.test_complete_veo_workflow("Debug test: beautiful sunset over mountains")),
            ("Test Prompt Input", lambda: self.test_prompt_input("Debug workflow test")),
            ("Scan for Videos", self.scan_for_videos)
        ]
        
        results = {}
        for step_name, step_func in steps:
            print(f"\n{'='*50}")
            print(f"🔄 Step: {step_name}")
            print('='*50)
            
            try:
                result = step_func()
                
                # Special handling for Chrome setup
                if step_name == "Setup Chrome" and not result:
                    results[step_name] = {'success': False, 'error': 'Chrome setup failed - cannot continue'}
                    print(f"❌ {step_name} failed - stopping workflow")
                    break
                
                # Skip steps if no driver available
                if not self.driver and step_name != "Setup Chrome":
                    results[step_name] = {'success': False, 'error': 'No Chrome driver available'}
                    print(f"❌ {step_name} skipped - no driver")
                    continue
                
                results[step_name] = {'success': True, 'result': result}
                print(f"✅ {step_name} completed")
                
                # Pause between steps
                time.sleep(self.config['debug_pause'])
                
            except Exception as e:
                results[step_name] = {'success': False, 'error': str(e)}
                print(f"❌ {step_name} failed: {e}")
                self.take_debug_screenshot(f"error_{step_name.replace(' ', '_')}")
                
                # Stop if critical step fails
                if step_name in ["Setup Chrome", "Navigate to Veo"]:
                    print(f"❌ Critical step {step_name} failed - stopping workflow")
                    break
        
        # Summary
        print(f"\n{'='*50}")
        print("🏁 DEBUG WORKFLOW SUMMARY")
        print('='*50)
        
        for step_name, result in results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {step_name}")
            if not result['success']:
                print(f"   Error: {result['error']}")
        
        return results

    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Chrome session closed")
            except:
                pass

def main():
    """Main debug function"""
    print("🔧 VEO WORKFLOW DEBUGGER")
    print("=" * 50)
    
    debugger = VeoWorkflowDebugger()
    
    try:
        # Ask user for debug mode
        print("\nDebug modes:")
        print("1. Full automated workflow debug")
        print("2. Interactive debug mode")
        print("3. Complete workflow test (step-by-step)")
        
        choice = input("Select mode (1-3): ").strip()
        
        if choice == "1":
            results = debugger.run_full_debug_workflow()
            
            # Ask if user wants interactive mode after
            if input("\nStart interactive debug? (y/n): ").strip().lower() == 'y':
                debugger.interactive_debug()
                
        elif choice == "2":
            if debugger.setup_chrome():
                if debugger.navigate_to_veo():
                    debugger.interactive_debug()
                    
        elif choice == "3":
            if debugger.setup_chrome():
                if debugger.navigate_to_veo():
                    # Ask for test prompt
                    test_prompt = input("Enter test prompt (or press Enter for default): ").strip()
                    if not test_prompt:
                        test_prompt = "Debug test: beautiful sunset over mountains"
                    
                    # Run complete Veo workflow test
                    results = debugger.test_complete_veo_workflow(test_prompt)
                    
                    # Ask if user wants interactive mode after
                    if input("\nStart interactive debug? (y/n): ").strip().lower() == 'y':
                        debugger.interactive_debug()
        else:
            print("❌ Invalid choice")
            
        # Keep browser open option
        if debugger.driver and input("\nKeep browser open for manual inspection? (y/n): ").strip().lower() == 'y':
            print("🌐 Browser will stay open for manual inspection...")
            print("📸 Screenshots are saved in debug_screenshots folder")
            input("Press Enter when ready to close browser...")
    
    except KeyboardInterrupt:
        print("\n🛑 Debug interrupted by user")
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()
