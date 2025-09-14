#!/usr/bin/env python3
"""
🎯 DYNAMIC ELEMENT DETECTOR
Tìm elements ổn định theo workflow, không phụ thuộc vào index hay dynamic classes
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

class DynamicElementDetector:
    """Detect elements dynamically based on stable patterns"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
        # 🎯 STABLE ELEMENT PATTERNS - Independent of page loads
        self.STABLE_PATTERNS = {
            'model_dropdown': {
                'strategies': [
                    # Text-based (most stable)
                    ("Text Pattern", self._find_by_text_pattern, {
                        'texts': ['Mô hình', 'Model', 'Veo 3'],
                        'element_type': 'button'
                    }),
                    
                    # Structure-based  
                    ("Label Navigation", self._find_by_label_navigation, {
                        'label_text': 'Mô hình',
                        'target_element': 'button'
                    }),
                    
                    # Icon-based
                    ("Icon Pattern", self._find_by_icon_pattern, {
                        'icons': ['volume_up'],
                        'context_texts': ['Veo 3', 'Quality', 'Fast']
                    }),
                    
                    # Position-based (fallback)
                    ("Position Pattern", self._find_by_position, {
                        'context': 'model dropdown - usually 2nd dropdown in form'
                    })
                ]
            },
            
            'output_count_dropdown': {
                'strategies': [
                    # Text-based (most stable)
                    ("Text Pattern", self._find_by_text_pattern, {
                        'texts': ['Câu trả lời đầu ra', 'đầu ra cho mỗi câu lệnh', 'Output'],
                        'element_type': 'button'
                    }),
                    
                    # Number-based
                    ("Number Pattern", self._find_by_number_pattern, {
                        'numbers': ['1', '2', '3', '4'],
                        'context_texts': ['Câu trả lời', 'đầu ra']
                    }),
                    
                    # Structure-based
                    ("Label Navigation", self._find_by_label_navigation, {
                        'label_text': 'Câu trả lời đầu ra cho mỗi câu lệnh',
                        'target_element': 'button'
                    }),
                    
                    # Position-based (fallback) 
                    ("Position Pattern", self._find_by_position, {
                        'context': 'output count - usually 1st dropdown in form'
                    })
                ]
            },
            
            'send_button': {
                'strategies': [
                    # Icon + text pattern
                    ("Icon Text Pattern", self._find_by_icon_text, {
                        'icon': 'arrow_forward',
                        'text': 'Tạo',
                        'element_type': 'button'
                    }),
                    
                    # Context-based
                    ("Context Pattern", self._find_by_context, {
                        'context_element': 'textarea',
                        'relationship': 'following',
                        'target_attributes': ['type="submit"', 'arrow_forward']
                    }),
                    
                    # Submit button pattern
                    ("Submit Pattern", self._find_by_submit_pattern, {
                        'submit_indicators': ['submit', 'arrow_forward', 'Tạo']
                    })
                ]
            }
        }
    
    def find_element_by_workflow_step(self, step_name, timeout=10):
        """Find element using multiple strategies for a workflow step"""
        
        if step_name not in self.STABLE_PATTERNS:
            raise ValueError(f"Unknown workflow step: {step_name}")
        
        patterns = self.STABLE_PATTERNS[step_name]
        
        print(f"🔍 Dynamic detection for: {step_name}")
        
        for strategy_name, strategy_func, params in patterns['strategies']:
            try:
                print(f"   📍 Trying: {strategy_name}")
                
                elements = strategy_func(params, timeout=timeout)
                
                if elements:
                    # Validate elements
                    valid_elements = self._validate_elements(elements, step_name)
                    
                    if valid_elements:
                        best_element = self._select_best_element(valid_elements, step_name)
                        print(f"   ✅ Found with {strategy_name}: {best_element.text[:50]}...")
                        return best_element
                        
            except Exception as e:
                print(f"   ❌ {strategy_name} failed: {e}")
                continue
        
        print(f"❌ No elements found for {step_name}")
        return None
    
    def _find_by_text_pattern(self, params, timeout=5):
        """Find elements by text patterns"""
        elements = []
        texts = params['texts']
        element_type = params.get('element_type', '*')
        
        for text in texts:
            try:
                # Multiple text search strategies
                selectors = [
                    f"//{element_type}[contains(text(), '{text}')]",
                    f"//*[contains(text(), '{text}')]/ancestor-or-self::{element_type}",
                    f"//*[contains(text(), '{text}')]/descendant::{element_type}",
                    f"//*[contains(text(), '{text}')]/following-sibling::{element_type}[1]"
                ]
                
                for selector in selectors:
                    found = self.driver.find_elements(By.XPATH, selector)
                    elements.extend([elem for elem in found if elem.is_displayed()])
                    
            except Exception:
                continue
                
        return elements
    
    def _find_by_label_navigation(self, params, timeout=5):
        """Find elements by navigating from labels"""
        elements = []
        label_text = params['label_text']
        target_element = params['target_element']
        
        try:
            # Find label and navigate to associated button
            label_selectors = [
                f"//*[contains(text(), '{label_text}')]/following::{target_element}[1]",
                f"//*[contains(text(), '{label_text}')]/..//{target_element}",
                f"//*[contains(text(), '{label_text}')]/parent::*/following-sibling::*//{target_element}",
                f"//*[contains(text(), '{label_text}')]/ancestor::div[1]//{target_element}"
            ]
            
            for selector in label_selectors:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
                
        except Exception:
            pass
            
        return elements
    
    def _find_by_icon_pattern(self, params, timeout=5):
        """Find elements by icon patterns"""
        elements = []
        icons = params['icons']
        context_texts = params.get('context_texts', [])
        
        for icon in icons:
            try:
                # Find elements with icon and context
                icon_selectors = [
                    f"//button[contains(text(), '{icon}')]",
                    f"//*[contains(text(), '{icon}')]/ancestor-or-self::button"
                ]
                
                for selector in icon_selectors:
                    found = self.driver.find_elements(By.XPATH, selector)
                    for elem in found:
                        if elem.is_displayed():
                            # Check if has context text
                            if any(ctx in elem.text for ctx in context_texts):
                                elements.append(elem)
                                
            except Exception:
                continue
                
        return elements
    
    def _find_by_number_pattern(self, params, timeout=5):
        """Find elements by number patterns"""
        elements = []
        numbers = params['numbers']
        context_texts = params.get('context_texts', [])
        
        for number in numbers:
            try:
                # Find buttons with numbers and context
                selectors = [
                    f"//button[contains(text(), '{number}')]",
                    f"//button[text()='{number}']"
                ]
                
                for selector in selectors:
                    found = self.driver.find_elements(By.XPATH, selector)
                    for elem in found:
                        if elem.is_displayed():
                            # Check context
                            if any(ctx in elem.text for ctx in context_texts):
                                elements.append(elem)
                                
            except Exception:
                continue
                
        return elements
    
    def _find_by_icon_text(self, params, timeout=5):
        """Find elements by icon + text combination"""
        elements = []
        icon = params['icon']
        text = params['text']
        element_type = params.get('element_type', 'button')
        
        try:
            # Find elements with both icon and text
            selectors = [
                f"//{element_type}[contains(text(), '{icon}') and contains(text(), '{text}')]",
                f"//{element_type}[contains(., '{icon}')][contains(., '{text}')]"
            ]
            
            for selector in selectors:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend([elem for elem in found if elem.is_displayed()])
                
        except Exception:
            pass
            
        return elements
    
    def _find_by_context(self, params, timeout=5):
        """Find elements by relationship to context elements"""
        elements = []
        context_element = params['context_element']
        relationship = params['relationship']
        target_attributes = params.get('target_attributes', [])
        
        try:
            # Find context element first
            context_elements = self.driver.find_elements(By.TAG_NAME, context_element)
            
            for ctx_elem in context_elements:
                if ctx_elem.is_displayed():
                    # Find related elements
                    for attr in target_attributes:
                        if 'type=' in attr:
                            attr_selector = f"//{relationship}::button[@{attr}]"
                        else:
                            attr_selector = f"//{relationship}::button[contains(text(), '{attr}')]"
                            
                        try:
                            related = ctx_elem.find_elements(By.XPATH, attr_selector)
                            elements.extend([elem for elem in related if elem.is_displayed()])
                        except:
                            continue
                            
        except Exception:
            pass
            
        return elements
    
    def _find_by_submit_pattern(self, params, timeout=5):
        """Find submit buttons by common patterns"""
        elements = []
        submit_indicators = params['submit_indicators']
        
        try:
            for indicator in submit_indicators:
                selectors = [
                    f"//button[@type='submit'][contains(text(), '{indicator}')]",
                    f"//button[contains(text(), '{indicator}')]",
                    f"//input[@type='submit'][contains(@value, '{indicator}')]"
                ]
                
                for selector in selectors:
                    found = self.driver.find_elements(By.XPATH, selector)
                    elements.extend([elem for elem in found if elem.is_displayed()])
                    
        except Exception:
            pass
            
        return elements
    
    def _find_by_position(self, params, timeout=5):
        """Find elements by position patterns (fallback)"""
        elements = []
        context = params['context']
        
        try:
            # Generic fallback patterns
            if 'dropdown' in context:
                # Find dropdown buttons
                dropdown_selectors = [
                    "//button[contains(., 'arrow_drop_down')]",
                    "//button[contains(@class, 'dropdown')]",
                    "//*[@role='combobox']"
                ]
                
                for selector in dropdown_selectors:
                    found = self.driver.find_elements(By.XPATH, selector)
                    elements.extend([elem for elem in found if elem.is_displayed()])
                    
        except Exception:
            pass
            
        return elements
    
    def _validate_elements(self, elements, step_name):
        """Validate found elements for specific workflow step"""
        valid_elements = []
        
        for elem in elements:
            try:
                if not elem.is_displayed() or not elem.is_enabled():
                    continue
                
                # Step-specific validation
                if step_name == 'model_dropdown':
                    if any(keyword in elem.text.lower() for keyword in ['veo', 'model', 'mô hình']):
                        valid_elements.append(elem)
                        
                elif step_name == 'output_count_dropdown':
                    if any(keyword in elem.text.lower() for keyword in ['câu trả lời', 'đầu ra', 'output']) or \
                       any(num in elem.text for num in ['1', '2', '3', '4']):
                        valid_elements.append(elem)
                        
                elif step_name == 'send_button':
                    if any(keyword in elem.text.lower() for keyword in ['tạo', 'create', 'submit', 'arrow_forward']):
                        valid_elements.append(elem)
                        
                else:
                    valid_elements.append(elem)
                    
            except StaleElementReferenceException:
                continue
                
        return valid_elements
    
    def _select_best_element(self, elements, step_name):
        """Select best element from valid candidates"""
        if not elements:
            return None
            
        if len(elements) == 1:
            return elements[0]
        
        # Score elements based on step-specific criteria
        scored_elements = []
        
        for elem in elements:
            try:
                score = 0
                text = elem.text.lower()
                
                # Step-specific scoring
                if step_name == 'model_dropdown':
                    if 'veo 3' in text:
                        score += 50
                    if 'mô hình' in text:
                        score += 30
                    if 'quality' in text or 'fast' in text:
                        score += 20
                        
                elif step_name == 'output_count_dropdown':
                    if 'câu trả lời đầu ra' in text:
                        score += 50
                    if any(num in text for num in ['1', '2', '3', '4']):
                        score += 30
                        
                elif step_name == 'send_button':
                    if 'arrow_forward' in text and 'tạo' in text:
                        score += 50
                    if elem.get_attribute('type') == 'submit':
                        score += 30
                
                # General scoring
                if 'arrow_drop_down' in text:
                    score += 10
                    
                scored_elements.append((score, elem))
                
            except Exception:
                continue
        
        # Return highest scored element
        if scored_elements:
            scored_elements.sort(key=lambda x: x[0], reverse=True)
            return scored_elements[0][1]
            
        return elements[0]  # Fallback to first element

def test_dynamic_detector():
    """Test function for dynamic detector"""
    print("🧪 Testing Dynamic Element Detector")
    
    # This would be integrated with actual WebDriver
    # detector = DynamicElementDetector(driver)
    # model_elem = detector.find_element_by_workflow_step('model_dropdown')
    # output_elem = detector.find_element_by_workflow_step('output_count_dropdown')
    # send_elem = detector.find_element_by_workflow_step('send_button')
    
    print("✅ Dynamic detector ready for integration")

if __name__ == "__main__":
    test_dynamic_detector() 