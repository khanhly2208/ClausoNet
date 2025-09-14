#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 QUICK VEO ELEMENT TESTER
Test nhanh các selector và elements trong Google Veo interface
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_chrome():
    """Quick Chrome setup"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,800")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except ImportError:
        return webdriver.Chrome(options=options)

def test_selectors(driver):
    """Test các selector chính trong Veo workflow"""
    print("🔍 Testing key selectors...")
    
    selectors_to_test = {
        "New Project Button": [
            "//button[contains(text(), 'Dự án mới') or contains(text(), 'New project')]",
            "//button[contains(@aria-label, 'new') or contains(@aria-label, 'mới')]",
            "//button[contains(., 'add') or contains(., '+')]"
        ],
        "Settings Button": [
            "//button[contains(., 'tune')]",
            "//button[contains(text(), 'Cài đặt') or contains(text(), 'Settings')]",
            "//button[contains(., '⚙')]"
        ],
        "Model Dropdown": [
            "//button[contains(text(), 'Veo 3')]",
            "//button[contains(text(), 'Quality') or contains(text(), 'Fast')]",
            "//div[contains(text(), 'Mô hình')]/..//button"
        ],
        "Output Count": [
            "//button[contains(text(), 'Câu trả lời đầu ra')]",
            "//button[contains(text(), '1') and not(contains(text(), '10'))]"
        ],
        "Prompt Input": [
            "//textarea[@id='PINHOLE_TEXT_AREA_ELEMENT_ID']",
            "//textarea[contains(@placeholder, 'prompt') or contains(@placeholder, 'nhập')]",
            "//textarea[not(@disabled)]"
        ],
        "Send Button": [
            "//button[contains(text(), 'Gửi') or contains(text(), 'Send')]",
            "//button[contains(@aria-label, 'send') or contains(@aria-label, 'gửi')]",
            "//button[contains(., 'arrow') or contains(., '→')]"
        ]
    }
    
    results = {}
    for element_name, selectors in selectors_to_test.items():
        print(f"\n🧪 Testing {element_name}:")
        found_elements = []
        
        for i, selector in enumerate(selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                visible_elements = [el for el in elements if el.is_displayed()]
                
                if visible_elements:
                    print(f"   ✅ Selector {i+1}: Found {len(visible_elements)} element(s)")
                    for j, el in enumerate(visible_elements[:3]):  # Show first 3
                        text = el.text[:30] if el.text else "No text"
                        print(f"      [{j}] '{text}' | tag: {el.tag_name}")
                    found_elements.extend(visible_elements)
                else:
                    print(f"   ❌ Selector {i+1}: No visible elements")
                    
            except Exception as e:
                print(f"   ⚠️ Selector {i+1}: Error - {e}")
        
        results[element_name] = found_elements
        print(f"   📊 Total found for {element_name}: {len(found_elements)}")
    
    return results

def test_page_state(driver):
    """Test page state và các thông tin cơ bản"""
    print("\n📊 PAGE STATE INFO:")
    print(f"URL: {driver.current_url}")
    print(f"Title: {driver.title}")
    
    # Count basic elements
    buttons = driver.find_elements(By.TAG_NAME, "button")
    visible_buttons = [b for b in buttons if b.is_displayed()]
    print(f"Buttons: {len(visible_buttons)}/{len(buttons)} visible")
    
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    visible_textareas = [t for t in textareas if t.is_displayed()]
    print(f"Textareas: {len(visible_textareas)}/{len(textareas)} visible")
    
    videos = driver.find_elements(By.TAG_NAME, "video")
    visible_videos = [v for v in videos if v.is_displayed()]
    print(f"Videos: {len(visible_videos)}/{len(videos)} visible")

def quick_workflow_test(driver):
    """Test quick workflow steps"""
    print("\n🚀 QUICK WORKFLOW TEST:")
    
    steps = [
        ("Navigate to Veo", lambda: driver.get("https://labs.google/fx/vi/tools/flow")),
        ("Wait for load", lambda: WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete")),
        ("Test selectors", lambda: test_selectors(driver)),
        ("Page state check", lambda: test_page_state(driver))
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = step_func()
            print(f"✅ {step_name} - Success")
            if step_name == "Test selectors":
                # Show summary of found elements
                if isinstance(result, dict):
                    found_count = sum(len(elements) for elements in result.values())
                    print(f"   📊 Total elements found: {found_count}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ {step_name} - Failed: {e}")
            break

def main():
    """Main function"""
    print("🔧 QUICK VEO ELEMENT TESTER")
    print("=" * 40)
    
    driver = None
    try:
        print("🚀 Setting up Chrome...")
        driver = setup_chrome()
        
        print("✅ Chrome ready")
        quick_workflow_test(driver)
        
        # Keep browser open for manual inspection
        print("\n⏸️ Browser will stay open for 60 seconds for manual inspection...")
        print("You can manually inspect the page now.")
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                print("🔒 Browser closed")
            except:
                pass

if __name__ == "__main__":
    main()
