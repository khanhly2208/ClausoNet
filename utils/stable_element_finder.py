#!/usr/bin/env python3
"""
🎯 STABLE ELEMENT FINDER
Tìm elements stable không phụ thuộc index hay dynamic classes
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

class StableElementFinder:
    """Find elements using stable patterns independent of page loads"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def find_model_dropdown_stable(self):
        """Tìm model dropdown bằng stable patterns"""
        print("🔍 Finding Model Dropdown (Stable Method)...")
        
        # 🎯 STRATEGY 1: Text-based với multiple fallbacks
        text_strategies = [
            "//button[contains(text(), 'Mô hình') and contains(text(), 'Veo')]",
            "//*[contains(text(), 'Mô hình')]/following-sibling::*//button[contains(text(), 'Veo')]",
            "//*[contains(text(), 'Mô hình')]/parent::*/following-sibling::*//button",
            "//*[normalize-space(text())='Mô hình']/..//button",
            "//*[normalize-space(text())='Mô hình']/following::button[1]"
        ]
        
        for strategy in text_strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                for elem in elements:
                    if elem.is_displayed() and self._is_model_dropdown(elem):
                        print(f"✅ Found model dropdown via text strategy")
                        return elem
            except:
                continue
        
        # 🎯 STRATEGY 2: Icon-based detection
        icon_strategies = [
            "//button[contains(., 'volume_up') and contains(text(), 'Veo')]",
            "//*[contains(text(), 'volume_up')]/ancestor-or-self::button[contains(text(), 'Veo')]"
        ]
        
        for strategy in icon_strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                for elem in elements:
                    if elem.is_displayed() and self._is_model_dropdown(elem):
                        print(f"✅ Found model dropdown via icon strategy")
                        return elem
            except:
                continue
        
        # 🎯 STRATEGY 3: Content-based scanning
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in all_buttons:
            try:
                if button.is_displayed() and self._is_model_dropdown(button):
                    print(f"✅ Found model dropdown via content scanning")
                    return button
            except:
                continue
        
        print("❌ Model dropdown not found")
        return None
    
    def find_output_count_dropdown_stable(self):
        """Tìm output count dropdown bằng stable patterns"""
        print("🔍 Finding Output Count Dropdown (Stable Method)...")
        
        # 🎯 STRATEGY 1: Full text patterns
        text_strategies = [
            "//button[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]",
            "//*[contains(text(), 'Câu trả lời đầu ra')]/following-sibling::*//button",
            "//*[contains(text(), 'đầu ra cho mỗi câu lệnh')]/parent::*/following-sibling::*//button",
            "//*[normalize-space(text())='Câu trả lời đầu ra cho mỗi câu lệnh']/..//button",
            "//*[contains(text(), 'Câu trả lời đầu ra')]/following::button[1]"
        ]
        
        for strategy in text_strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                for elem in elements:
                    if elem.is_displayed() and self._is_output_count_dropdown(elem):
                        print(f"✅ Found output count dropdown via text strategy")
                        return elem
            except:
                continue
        
        # 🎯 STRATEGY 2: Number-based detection
        number_strategies = [
            "//button[contains(text(), 'Câu trả lời') and (contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4'))]",
            "//*[contains(text(), 'đầu ra')]/following::button[contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4')]"
        ]
        
        for strategy in number_strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                for elem in elements:
                    if elem.is_displayed() and self._is_output_count_dropdown(elem):
                        print(f"✅ Found output count dropdown via number strategy")
                        return elem
            except:
                continue
        
        # 🎯 STRATEGY 3: Content-based scanning
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in all_buttons:
            try:
                if button.is_displayed() and self._is_output_count_dropdown(button):
                    print(f"✅ Found output count dropdown via content scanning")
                    return button
            except:
                continue
        
        print("❌ Output count dropdown not found")
        return None
    
    def find_send_button_stable(self):
        """Tìm send button bằng stable patterns"""
        print("🔍 Finding Send Button (Stable Method)...")
        
        # 🎯 STRATEGY 1: Icon + text combination
        icon_text_strategies = [
            "//button[contains(text(), 'arrow_forward') and contains(text(), 'Tạo')]",
            "//button[@type='submit'][contains(text(), 'Tạo')]",
            "//button[contains(., 'arrow_forward')][@type='submit']"
        ]
        
        for strategy in icon_text_strategies:
            try:
                elements = self.driver.find_elements(By.XPATH, strategy)
                for elem in elements:
                    if elem.is_displayed() and self._is_send_button(elem):
                        print(f"✅ Found send button via icon+text strategy")
                        return elem
            except:
                continue
        
        # 🎯 STRATEGY 2: Context-based (near textarea)
        try:
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if textarea.is_displayed():
                    # Find submit button near textarea
                    context_strategies = [
                        ".//following::button[@type='submit'][1]",
                        ".//following::button[contains(., 'arrow_forward')][1]",
                        ".//following::button[contains(text(), 'Tạo')][1]",
                        "./..//button[@type='submit']"
                    ]
                    
                    for strategy in context_strategies:
                        try:
                            elements = textarea.find_elements(By.XPATH, strategy)
                            for elem in elements:
                                if elem.is_displayed() and self._is_send_button(elem):
                                    print(f"✅ Found send button via context strategy")
                                    return elem
                        except:
                            continue
        except:
            pass
        
        # 🎯 STRATEGY 3: Content-based scanning
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in all_buttons:
            try:
                if button.is_displayed() and self._is_send_button(button):
                    print(f"✅ Found send button via content scanning")
                    return button
            except:
                continue
        
        print("❌ Send button not found")
        return None
    
    def _is_model_dropdown(self, element):
        """Check if element is model dropdown"""
        try:
            text = element.text.lower()
            
            # Must contain model indicators
            model_indicators = ['mô hình', 'model', 'veo']
            has_model_indicator = any(indicator in text for indicator in model_indicators)
            
            # Must contain version indicators
            version_indicators = ['veo 3', 'quality', 'fast']
            has_version_indicator = any(indicator in text for indicator in version_indicators)
            
            # Must be dropdown
            is_dropdown = 'arrow_drop' in text or element.get_attribute('role') == 'combobox'
            
            return has_model_indicator and (has_version_indicator or is_dropdown)
            
        except:
            return False
    
    def _is_output_count_dropdown(self, element):
        """Check if element is output count dropdown"""
        try:
            text = element.text.lower()
            
            # Must contain output indicators
            output_indicators = ['câu trả lời', 'đầu ra', 'output']
            has_output_indicator = any(indicator in text for indicator in output_indicators)
            
            # Must contain count indicators
            count_indicators = ['1', '2', '3', '4', 'cho mỗi câu lệnh']
            has_count_indicator = any(indicator in text for indicator in count_indicators)
            
            # Must be dropdown
            is_dropdown = 'arrow_drop' in text or element.get_attribute('role') == 'combobox'
            
            return has_output_indicator and (has_count_indicator or is_dropdown)
            
        except:
            return False
    
    def _is_send_button(self, element):
        """Check if element is send button"""
        try:
            text = element.text.lower()
            element_type = element.get_attribute('type')
            
            # Must contain send indicators
            send_indicators = ['arrow_forward', 'tạo', 'create', 'submit', 'send']
            has_send_indicator = any(indicator in text for indicator in send_indicators)
            
            # Submit type is strong indicator
            is_submit_type = element_type == 'submit'
            
            # Icon + text combination is strongest
            has_icon_text = 'arrow_forward' in text and 'tạo' in text
            
            return has_send_indicator or is_submit_type or has_icon_text
            
        except:
            return False
    
    def click_element_stable(self, element, element_name="element"):
        """Click element với multiple strategies"""
        if not element:
            print(f"❌ Cannot click {element_name}: element is None")
            return False
        
        print(f"🖱️ Clicking {element_name}...")
        
        # Multiple click strategies
        click_strategies = [
            ("Direct Click", lambda: element.click()),
            ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains Click", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
            ("ScrollIntoView + Click", lambda: self._scroll_and_click(element)),
            ("Offset Click", lambda: ActionChains(self.driver).move_to_element_with_offset(element, 5, 5).click().perform())
        ]
        
        for strategy_name, click_func in click_strategies:
            try:
                print(f"   📍 Trying: {strategy_name}")
                
                # Ensure element is ready
                if not element.is_displayed() or not element.is_enabled():
                    print(f"   ❌ Element not ready for {strategy_name}")
                    continue
                
                # Clear any overlays
                self._clear_overlays()
                
                # Execute click
                click_func()
                time.sleep(1)
                
                print(f"   ✅ {strategy_name} successful!")
                return True
                
            except Exception as e:
                print(f"   ❌ {strategy_name} failed: {e}")
                continue
        
        print(f"❌ All click strategies failed for {element_name}")
        return False
    
    def _scroll_and_click(self, element):
        """Scroll to element and click"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
    
    def _clear_overlays(self):
        """Clear potential overlays"""
        try:
            # Press Escape
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.3)
            
            # Click body to clear focus
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            time.sleep(0.3)
            
        except:
            pass

def test_stable_finder():
    """Test function"""
    print("🧪 Stable Element Finder Ready")
    print("✅ Model dropdown detection - Multiple strategies")
    print("✅ Output count dropdown detection - Multiple strategies") 
    print("✅ Send button detection - Multiple strategies")
    print("✅ Stable clicking - Multiple strategies")
    print("✅ Independent of page loads and dynamic classes")

if __name__ == "__main__":
    test_stable_finder() 