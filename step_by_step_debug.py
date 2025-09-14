#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 VEO WORKFLOW STEP-BY-STEP DEBUGGER
Debug từng bước cụ thể trong automation workflow với manual confirmation
"""

import os
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class VeoStepByStepDebugger:
    """Debug từng bước workflow với user confirmation"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.current_step = 0
        self.screenshots_dir = Path("debug_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def setup_chrome_with_profile(self, profile_name="debug_profile"):
        """Setup Chrome với profile debug"""
        print(f"🚀 Setting up Chrome with profile: {profile_name}")
        
        # Determine profile path based on exe mode
        if getattr(sys, 'frozen', False):
            profile_base = Path.home() / "AppData/Local/ClausoNet4.0/profiles"
        else:
            profile_base = Path("chrome_profiles")
        
        profile_path = profile_base / profile_name
        profile_path.mkdir(parents=True, exist_ok=True)
        
        options = Options()
        options.add_argument(f"--user-data-dir={str(profile_path.absolute())}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1400,900")
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except ImportError:
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(3)
        self.wait = WebDriverWait(self.driver, 15)
        
        # Anti-detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome setup complete")
        return True
    
    def take_screenshot(self, step_name):
        """Take screenshot với step number"""
        self.current_step += 1
        filename = f"step_{self.current_step:02d}_{step_name}.png"
        filepath = self.screenshots_dir / filename
        self.driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot: {filename}")
        
    def wait_for_user_confirmation(self, message, auto_continue=False):
        """Wait cho user confirmation"""
        if auto_continue:
            print(f"🤖 AUTO MODE: {message}")
            time.sleep(2)
            return True
        
        response = input(f"\n⏸️ {message}\nPress Enter to continue, 's' for screenshot, 'q' to quit: ").strip().lower()
        
        if response == 'q':
            return False
        elif response == 's':
            self.take_screenshot("manual_check")
        return True
    
    def debug_navigation(self):
        """Debug navigation step"""
        print("\n🌐 STEP 1: Navigation to Google Veo")
        print("-" * 40)
        
        try:
            veo_url = "https://labs.google/fx/vi/tools/flow"
            print(f"Navigating to: {veo_url}")
            
            self.driver.get(veo_url)
            
            # Wait for page load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(3)
            
            self.take_screenshot("navigation_complete")
            
            print(f"✅ Current URL: {self.driver.current_url}")
            print(f"✅ Page Title: {self.driver.title}")
            
            if not self.wait_for_user_confirmation("Navigation completed. Check if page loaded correctly."):
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            self.take_screenshot("navigation_failed")
            return False
    
    def debug_new_project_button(self):
        """Debug finding và clicking New Project button"""
        print("\n🔍 STEP 2: Find New Project Button")
        print("-" * 40)
        
        selectors = [
            "//button[contains(text(), 'Dự án mới') or contains(text(), 'New project')]",
            "//button[contains(@aria-label, 'new') or contains(@aria-label, 'mới')]",
            "//button[contains(., 'add') or contains(., '+')]",
            "//div[contains(@class, 'button')][contains(text(), 'Dự án mới')]",
            "//button[contains(text(), 'Create') or contains(text(), 'Tạo')]"
        ]
        
        print("Testing selectors for New Project button:")
        found_elements = []
        
        for i, selector in enumerate(selectors):
            print(f"\n🧪 Selector {i+1}: {selector}")
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                
                if visible_elements:
                    print(f"   ✅ Found {len(visible_elements)} element(s)")
                    for j, el in enumerate(visible_elements):
                        text = el.text[:50] if el.text else "No text"
                        aria_label = el.get_attribute('aria-label') or "No aria-label"
                        print(f"      [{j}] Text: '{text}' | Aria: '{aria_label[:30]}'")
                        
                        # Highlight element
                        self.driver.execute_script("""
                            arguments[0].style.border = '3px solid red';
                            arguments[0].style.backgroundColor = 'yellow';
                        """, el)
                        
                    found_elements.extend(visible_elements)
                else:
                    print("   ❌ No visible elements found")
                    
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        self.take_screenshot("new_project_buttons_highlighted")
        
        if found_elements:
            print(f"\n📊 Total found elements: {len(found_elements)}")
            
            # Let user choose which element to test
            for i, el in enumerate(found_elements[:5]):  # Show first 5
                text = el.text[:30] if el.text else "No text"
                print(f"   [{i}] '{text}'")
            
            if not self.wait_for_user_confirmation("Elements highlighted in red/yellow. Choose element to test click?"):
                return False
            
            try:
                choice = input("Enter element number to test (0-4) or press Enter for first element: ").strip()
                index = int(choice) if choice.isdigit() else 0
                
                if 0 <= index < len(found_elements):
                    return self.test_element_click(found_elements[index], "New Project Button")
                else:
                    return self.test_element_click(found_elements[0], "New Project Button")
                    
            except (ValueError, IndexError):
                return self.test_element_click(found_elements[0], "New Project Button")
        else:
            print("❌ No New Project button found")
            return False
    
    def debug_settings_button(self):
        """Debug finding Settings button"""
        print("\n🔍 STEP 3: Find Settings Button")
        print("-" * 40)
        
        selectors = [
            "//button[contains(., 'tune')]",
            "//button[contains(text(), 'Cài đặt') or contains(text(), 'Settings')]",
            "//button[contains(., '⚙')]",
            "//button[contains(@aria-label, 'Settings') or contains(@aria-label, 'settings')]",
            "//header//button[contains(., 'tune')]",
            "//nav//button[last()]"
        ]
        
        return self.debug_element_selection(selectors, "Settings Button", "settings_button")
    
    def debug_model_dropdown(self):
        """Debug finding Model dropdown"""
        print("\n🔍 STEP 4: Find Model Dropdown")
        print("-" * 40)
        
        selectors = [
            "//div[contains(text(), 'Mô hình')]/..//button",
            "//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Quality') or contains(text(), 'Fast')]",
            "//div[contains(@class, 'popup')]//button[contains(text(), 'Veo')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), 'Veo')]"
        ]
        
        return self.debug_element_selection(selectors, "Model Dropdown", "model_dropdown")
    
    def debug_prompt_input(self):
        """Debug finding và testing Prompt Input"""
        print("\n📝 STEP 5: Find Prompt Input")
        print("-" * 40)
        
        selectors = [
            "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
            "//textarea[contains(@placeholder, 'prompt') or contains(@placeholder, 'nhập')]",
            "//textarea[not(@disabled)]",
            "//input[@type='text'][not(@disabled)]",
            "//div[contains(@contenteditable, 'true')]"
        ]
        
        found_element = self.debug_element_selection(selectors, "Prompt Input", "prompt_input", click_test=False)
        
        if found_element:
            # Test typing
            test_prompt = "This is a debug test prompt"
            print(f"\n📝 Testing prompt typing: '{test_prompt}'")
            
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", found_element)
                time.sleep(1)
                
                found_element.click()
                found_element.clear()
                found_element.send_keys(test_prompt)
                
                # Trigger events
                self.driver.execute_script("""
                    var elem = arguments[0];
                    elem.dispatchEvent(new Event('input', {bubbles: true}));
                    elem.dispatchEvent(new Event('change', {bubbles: true}));
                """, found_element)
                
                self.take_screenshot("prompt_typed")
                
                if not self.wait_for_user_confirmation("Prompt typed. Check if it appears correctly."):
                    return False
                    
                print("✅ Prompt typing test successful")
                return True
                
            except Exception as e:
                print(f"❌ Prompt typing failed: {e}")
                return False
        
        return False
    
    def debug_element_selection(self, selectors, element_name, screenshot_prefix, click_test=True):
        """Generic element selection debugging"""
        print(f"Testing selectors for {element_name}:")
        found_elements = []
        
        for i, selector in enumerate(selectors):
            print(f"\n🧪 Selector {i+1}: {selector}")
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                
                if visible_elements:
                    print(f"   ✅ Found {len(visible_elements)} element(s)")
                    for j, el in enumerate(visible_elements):
                        text = el.text[:50] if el.text else "No text"
                        print(f"      [{j}] '{text}'")
                        
                        # Highlight element
                        self.driver.execute_script("""
                            arguments[0].style.border = '3px solid blue';
                            arguments[0].style.backgroundColor = 'lightblue';
                        """, el)
                        
                    found_elements.extend(visible_elements)
                else:
                    print("   ❌ No visible elements found")
                    
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        self.take_screenshot(f"{screenshot_prefix}_highlighted")
        
        if found_elements:
            if not self.wait_for_user_confirmation(f"{element_name} elements highlighted. Continue?"):
                return False
            
            if click_test:
                # Test clicking first element
                return self.test_element_click(found_elements[0], element_name)
            else:
                return found_elements[0]
        else:
            print(f"❌ No {element_name} found")
            return False
    
    def test_element_click(self, element, element_name):
        """Test clicking an element với multiple methods"""
        print(f"\n🧪 Testing click on {element_name}")
        
        # Scroll to element
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(1)
        
        self.take_screenshot(f"before_click_{element_name.replace(' ', '_')}")
        
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
                
                self.take_screenshot(f"after_click_{element_name.replace(' ', '_')}_{method_name.replace(' ', '_')}")
                
                print(f"   ✅ {method_name} successful")
                
                if not self.wait_for_user_confirmation(f"{method_name} completed. Check page state."):
                    return False
                    
                return True
                
            except Exception as e:
                print(f"   ❌ {method_name} failed: {e}")
                continue
        
        print(f"❌ All click methods failed for {element_name}")
        return False
    
    def run_step_by_step_debug(self):
        """Run complete step-by-step debug"""
        print("🎯 VEO WORKFLOW STEP-BY-STEP DEBUGGER")
        print("=" * 50)
        
        # Ask for auto mode
        auto_mode = input("Run in auto mode? (y/n): ").strip().lower() == 'y'
        
        steps = [
            ("Navigation", self.debug_navigation),
            ("New Project Button", self.debug_new_project_button),
            ("Settings Button", self.debug_settings_button),
            ("Model Dropdown", self.debug_model_dropdown),
            ("Prompt Input", self.debug_prompt_input)
        ]
        
        results = {}
        for step_name, step_func in steps:
            print(f"\n{'='*50}")
            print(f"🔄 DEBUGGING: {step_name}")
            print('='*50)
            
            try:
                if auto_mode:
                    # Modify wait_for_user_confirmation behavior
                    original_wait = self.wait_for_user_confirmation
                    self.wait_for_user_confirmation = lambda msg: self.wait_for_user_confirmation(msg, auto_continue=True)
                
                result = step_func()
                results[step_name] = result
                
                if result:
                    print(f"✅ {step_name} - SUCCESS")
                else:
                    print(f"❌ {step_name} - FAILED")
                    if not auto_mode and input("Continue to next step? (y/n): ").strip().lower() != 'y':
                        break
                
            except Exception as e:
                print(f"❌ {step_name} - ERROR: {e}")
                results[step_name] = False
                if not auto_mode and input("Continue to next step? (y/n): ").strip().lower() != 'y':
                    break
        
        # Summary
        print(f"\n{'='*50}")
        print("🏁 DEBUG SUMMARY")
        print('='*50)
        
        for step_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {step_name}")
        
        print(f"\n📁 Screenshots saved to: {self.screenshots_dir.absolute()}")
        
        return results
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Chrome closed")
            except:
                pass

def main():
    """Main function"""
    debugger = VeoStepByStepDebugger()
    
    try:
        if not debugger.setup_chrome_with_profile():
            print("❌ Chrome setup failed")
            return
        
        debugger.run_step_by_step_debug()
        
        # Keep browser open for manual inspection
        if input("\nKeep browser open for manual inspection? (y/n): ").strip().lower() == 'y':
            print("Browser will stay open. Close manually when done.")
            input("Press Enter when ready to close...")
        
    except KeyboardInterrupt:
        print("\n🛑 Debug interrupted by user")
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()
