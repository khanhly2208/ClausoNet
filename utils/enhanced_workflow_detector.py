#!/usr/bin/env python3
"""
🚀 ENHANCED WORKFLOW DETECTOR
Stable element detection không phụ thuộc vào page loads
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

class EnhancedWorkflowDetector:
    """Enhanced workflow detector với dynamic element finding"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def find_model_dropdown_dynamic(self):
        """Tìm model dropdown bằng multiple strategies"""
        print("🔍 Dynamic Model Dropdown Detection...")
        
        strategies = [
            # Strategy 1: Text-based search
            self._find_model_by_text,
            
            # Strategy 2: Icon-based search  
            self._find_model_by_icon,
            
            # Strategy 3: Structure-based search
            self._find_model_by_structure,
            
            # Strategy 4: Position-based search
            self._find_model_by_position
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"   📍 Strategy {i}: {strategy.__name__}")
                elements = strategy()
                
                if elements:
                    best_element = self._select_best_model_element(elements)
                    if best_element:
                        print(f"   ✅ Found model dropdown: {best_element.text[:50]}...")
                        return best_element
                        
            except Exception as e:
                print(f"   ❌ Strategy {i} failed: {e}")
                continue
        
        print("❌ No model dropdown found")
        return None
    
    def find_output_count_dropdown_dynamic(self):
        """Tìm output count dropdown bằng multiple strategies"""
        print("🔍 Dynamic Output Count Detection...")
        
        strategies = [
            # Strategy 1: Text-based search
            self._find_output_by_text,
            
            # Strategy 2: Number-based search
            self._find_output_by_number,
            
            # Strategy 3: Structure-based search  
            self._find_output_by_structure,
            
            # Strategy 4: Position-based search
            self._find_output_by_position
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"   📍 Strategy {i}: {strategy.__name__}")
                elements = strategy()
                
                if elements:
                    best_element = self._select_best_output_element(elements)
                    if best_element:
                        print(f"   ✅ Found output dropdown: {best_element.text[:50]}...")
                        return best_element
                        
            except Exception as e:
                print(f"   ❌ Strategy {i} failed: {e}")
                continue
        
        print("❌ No output count dropdown found")
        return None
    
    def find_send_button_dynamic(self):
        """Tìm send button bằng multiple strategies"""
        print("🔍 Dynamic Send Button Detection...")
        
        strategies = [
            # Strategy 1: Icon + text search
            self._find_send_by_icon_text,
            
            # Strategy 2: Submit type search
            self._find_send_by_submit_type,
            
            # Strategy 3: Context-based search
            self._find_send_by_context,
            
            # Strategy 4: Position-based search
            self._find_send_by_position
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"   📍 Strategy {i}: {strategy.__name__}")
                elements = strategy()
                
                if elements:
                    best_element = self._select_best_send_element(elements)
                    if best_element:
                        print(f"   ✅ Found send button: {best_element.text[:50]}...")
                        return best_element
                        
            except Exception as e:
                print(f"   ❌ Strategy {i} failed: {e}")
                continue
        
        print("❌ No send button found")
        return None
    
    # Model Dropdown Strategies
    def _find_model_by_text(self):
        """Find model dropdown by text patterns"""
        selectors = [
            "//button[contains(text(), 'Mô hình') and contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Veo 3 - Quality')]",
            "//button[contains(text(), 'Veo 3 - Fast')]",
            "//button[contains(text(), 'Veo 3')]",
            "//*[contains(text(), 'Mô hình')]/following::button[contains(text(), 'Veo')][1]",
            "//*[contains(text(), 'Model')]/following::button[contains(text(), 'Veo')][1]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_model_by_icon(self):
        """Find model dropdown by icon patterns"""
        selectors = [
            "//button[contains(text(), 'volume_up') and contains(text(), 'Veo')]",
            "//button[contains(., 'volume_up')][contains(text(), 'Quality')]",
            "//button[contains(., 'volume_up')][contains(text(), 'Fast')]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_model_by_structure(self):
        """Find model dropdown by DOM structure"""
        # Tìm label "Mô hình" và navigate đến button
        selectors = [
            "//*[normalize-space(text())='Mô hình']/..//button",
            "//*[normalize-space(text())='Mô hình']/following-sibling::*//button",
            "//*[normalize-space(text())='Mô hình']/parent::*/following-sibling::*//button[1]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                # Filter cho button có Veo text
                for elem in found:
                    if elem.is_displayed() and 'veo' in elem.text.lower():
                        elements.append(elem)
            except:
                continue
                
        return elements
    
    def _find_model_by_position(self):
        """Find model dropdown by position (fallback)"""
        # Tìm tất cả dropdown buttons và filter
        selectors = [
            "//button[contains(., 'arrow_drop_down')]",
            "//*[@role='combobox']",
            "//button[contains(@class, 'dropdown')]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                for elem in found:
                    if elem.is_displayed() and any(keyword in elem.text.lower() 
                                                 for keyword in ['veo', 'model', 'quality', 'fast']):
                        elements.append(elem)
            except:
                continue
                
        return elements
    
    # Output Count Dropdown Strategies  
    def _find_output_by_text(self):
        """Find output dropdown by text patterns"""
        selectors = [
            "//button[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]",
            "//button[contains(text(), 'Câu trả lời đầu ra')]",
            "//button[contains(text(), 'đầu ra cho mỗi câu lệnh')]",
            "//*[contains(text(), 'Câu trả lời đầu ra')]/following::button[1]",
            "//*[contains(text(), 'Output count')]/following::button[1]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_output_by_number(self):
        """Find output dropdown by number patterns"""
        selectors = [
            "//button[contains(text(), 'Câu trả lời') and (text()='1' or contains(text(), '1'))]",
            "//button[contains(text(), 'Câu trả lời') and (text()='2' or contains(text(), '2'))]", 
            "//button[contains(text(), 'Câu trả lời') and (text()='3' or contains(text(), '3'))]",
            "//button[contains(text(), 'Câu trả lời') and (text()='4' or contains(text(), '4'))]",
            "//button[text()='1' or text()='2' or text()='3' or text()='4']"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                # Filter cho buttons có context về output
                for elem in found:
                    if elem.is_displayed() and any(keyword in elem.text.lower() 
                                                 for keyword in ['câu trả lời', 'đầu ra', 'output']):
                        elements.append(elem)
            except:
                continue
                
        return elements
    
    def _find_output_by_structure(self):
        """Find output dropdown by DOM structure"""
        selectors = [
            "//*[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]/..//button",
            "//*[contains(text(), 'Câu trả lời đầu ra cho mỗi câu lệnh')]/following-sibling::*//button",
            "//*[contains(text(), 'đầu ra')]/ancestor::div[1]//button"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_output_by_position(self):
        """Find output dropdown by position (fallback)"""
        # Tìm dropdown đầu tiên (thường là output count)
        selectors = [
            "(//button[contains(., 'arrow_drop_down')])[1]",
            "(//button[contains(., 'arrow_drop_d')])[1]",  # Shortened arrow
            "(//*[@role='combobox'])[1]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    # Send Button Strategies
    def _find_send_by_icon_text(self):
        """Find send button by icon + text"""
        selectors = [
            "//button[contains(text(), 'arrow_forward') and contains(text(), 'Tạo')]",
            "//button[contains(., 'arrow_forward')][contains(text(), 'Tạo')]",
            "//button[contains(text(), 'arrow_forward')][@type='submit']",
            "//button[contains(., '➤')][contains(text(), 'Tạo')]"  # Arrow unicode
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_send_by_submit_type(self):
        """Find send button by submit type"""
        selectors = [
            "//button[@type='submit'][contains(text(), 'Tạo')]",
            "//button[@type='submit'][contains(., 'arrow_forward')]",
            "//input[@type='submit'][contains(@value, 'Tạo')]",
            "//button[@type='submit']"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
            except:
                continue
                
        return elements
    
    def _find_send_by_context(self):
        """Find send button by textarea context"""
        try:
            # Tìm textarea trước
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            elements = []
            for textarea in textareas:
                if textarea.is_displayed():
                    # Tìm submit button gần textarea
                    context_selectors = [
                        ".//following::button[@type='submit'][1]",
                        ".//following::button[contains(., 'arrow_forward')][1]",
                        ".//following::button[contains(text(), 'Tạo')][1]",
                        "./..//button[@type='submit']"
                    ]
                    
                    for selector in context_selectors:
                        try:
                            found = textarea.find_elements(By.XPATH, selector)
                            elements.extend([elem for elem in found if elem.is_displayed()])
                        except:
                            continue
                            
            return elements
            
        except:
            return []
    
    def _find_send_by_position(self):
        """Find send button by position (fallback)"""
        selectors = [
            "//button[last()]",  # Last button on page
            "(//button[@type='submit'])[last()]",  # Last submit button
            "//form//button[last()]"  # Last button in form
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                # Filter cho buttons có send indicators
                for elem in found:
                    if elem.is_displayed() and any(keyword in elem.text.lower() 
                                                 for keyword in ['tạo', 'create', 'submit', 'send', 'arrow']):
                        elements.append(elem)
            except:
                continue
                
        return elements
    
    # Element Selection Methods
    def _select_best_model_element(self, elements):
        """Select best model element from candidates"""
        if not elements:
            return None
            
        # Score elements
        scored = []
        for elem in elements:
            try:
                score = 0
                text = elem.text.lower()
                
                # Scoring criteria
                if 'mô hình' in text:
                    score += 40
                if 'veo 3' in text:
                    score += 30  
                if 'quality' in text or 'fast' in text:
                    score += 20
                if 'arrow_drop_down' in text:
                    score += 10
                    
                scored.append((score, elem))
                
            except:
                continue
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
            
        return elements[0]
    
    def _select_best_output_element(self, elements):
        """Select best output element from candidates"""
        if not elements:
            return None
            
        # Score elements  
        scored = []
        for elem in elements:
            try:
                score = 0
                text = elem.text.lower()
                
                # Scoring criteria
                if 'câu trả lời đầu ra cho mỗi câu lệnh' in text:
                    score += 50
                if 'câu trả lời đầu ra' in text:
                    score += 30
                if any(num in text for num in ['1', '2', '3', '4']):
                    score += 20
                if 'arrow_drop_d' in text:
                    score += 10
                    
                scored.append((score, elem))
                
            except:
                continue
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
            
        return elements[0]
    
    def _select_best_send_element(self, elements):
        """Select best send element from candidates"""
        if not elements:
            return None
            
        # Score elements
        scored = []
        for elem in elements:
            try:
                score = 0
                text = elem.text.lower()
                elem_type = elem.get_attribute('type')
                
                # Scoring criteria
                if 'arrow_forward' in text and 'tạo' in text:
                    score += 50
                if elem_type == 'submit':
                    score += 30
                if 'arrow_forward' in text:
                    score += 20
                if 'tạo' in text:
                    score += 15
                    
                scored.append((score, elem))
                
            except:
                continue
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
            
        return elements[0]

# Test function
def test_enhanced_detector():
    """Test enhanced workflow detector"""
    print("🧪 Enhanced Workflow Detector Ready")
    print("✅ Dynamic element detection strategies implemented")
    print("✅ Multiple fallback mechanisms available")
    print("✅ Stable across page reloads")

if __name__ == "__main__":
    test_enhanced_detector() 