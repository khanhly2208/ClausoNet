"""
Google Veo 3 Automation Module
Automatically creates videos on Google Veo 3 using Selenium WebDriver
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .profile_manager import ChromeProfileManager

class VeoAutomation:
    """Automates video creation on Google Veo 3"""
    
    # XPath selectors based on user's workflow
    SELECTORS = {
        # Multiple selectors for better reliability
        "new_project": [
            "//button[contains(text(), 'New project') or contains(text(), 'Create')]",
            "button[aria-label*='New project']",
            "//main//button:first-child"
        ],
        "type_dropdown": [
            "//button[contains(text(), 'Text to Video')]",
            "button[aria-label*='type']",
            "//button[.//span[contains(text(), 'Text to Video')]]"
        ],
        "settings_button": [
            "//button[contains(text(), 'Settings')]",
            "button[aria-label*='settings']",
            "//button[contains(@class, 'settings')]"
        ],
        "model_dropdown": [
            "//button[.//span[contains(text(), 'Veo')]]",
            "button[aria-label*='model']",
            "//button[contains(text(), 'Quality') or contains(text(), 'Fast')]"
        ],
        "count_dropdown": [
            "//button[.//span[contains(text(), '1') or contains(text(), '2')]]",
            "button[aria-label*='count']",
            "//button[contains(@class, 'count')]"
        ],
        "prompt_textarea": [
            "#PINHOLE_TEXT_AREA_ELEMENT_ID",
            "textarea[placeholder]",
            "//textarea[contains(@aria-label, 'prompt')]"
        ],
        "create_button": [
            "//button[contains(text(), 'Create') or contains(text(), 'Generate')]",
            "button[aria-label*='Create video']",
            "//button[contains(@class, 'primary')]"
        ]
    }
    
    # Dropdown option mappings
    TYPE_OPTIONS = {
        "Text to Video": "text-to-video",
        "Image to Video": "image-to-video"
    }
    
    MODEL_OPTIONS = {
        "Veo 3 Fast": "veo-3-fast",
        "Veo 3 Quality": "veo-3-quality", 
        "Veo 2 Fast": "veo-2-fast",
        "Veo 2 Quality": "veo-2-quality"
    }
    
    COUNT_OPTIONS = {
        "1": "1",
        "2": "2", 
        "3": "3",
        "4": "4"
    }
    
    def __init__(self, profile_name: str, headless: bool = False):
        """
        Initialize Veo Automation
        
        Args:
            profile_name: Chrome profile name to use
            headless: Run in headless mode
        """
        self.profile_name = profile_name
        self.headless = headless
        self.driver = None
        self.wait = None
        self.profile_manager = ChromeProfileManager()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def setup_chrome(self) -> bool:
        """Setup Chrome WebDriver with profile"""
        try:
            self.logger.info(f"🚀 Setting up Chrome with profile: {self.profile_name}")
            
            # Get profile path
            profile_path = self.profile_manager.get_profile_path(self.profile_name)
            if not os.path.exists(profile_path):
                self.logger.error(f"❌ Profile not found: {profile_path}")
                return False
            
            # Close existing Chrome instances
            self.profile_manager.close_all_chrome_instances()
            time.sleep(2)
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument("--profile-directory=Default")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-features=ProfilePicker")
            chrome_options.add_argument("--disable-features=ChromeAccountManagement")
            chrome_options.add_argument("--disable-signin-promo")
            chrome_options.add_argument("--disable-sync-preferences")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Setup ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
            except Exception as e:
                self.logger.warning(f"⚠️ WebDriver-manager failed: {e}")
                service = None
            
            # Create WebDriver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            self.logger.info("✅ Chrome setup complete!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chrome setup failed: {e}")
            return False
    
    def wait_and_click(self, xpath_or_list, timeout: int = 30) -> bool:
        """Wait for element and click it - supports multiple selectors"""
        # Check if driver is initialized
        if not self.driver:
            self.logger.error("❌ WebDriver not initialized. Call setup_chrome() first.")
            return False
        
        # Convert single xpath to list for uniform processing
        if isinstance(xpath_or_list, str):
            xpaths = [xpath_or_list]
        else:
            xpaths = xpath_or_list
        
        # Try each selector until one works
        for i, xpath in enumerate(xpaths):
            try:
                self.logger.debug(f"🔍 Trying selector {i+1}/{len(xpaths)}: {xpath[:100]}...")
                element = WebDriverWait(self.driver, timeout if i == 0 else 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                element.click()
                self.logger.info(f"✅ Clicked element with selector {i+1}: {xpath}")
                return True
            except TimeoutException:
                if i == len(xpaths) - 1:  # Last selector failed
                    self.logger.error(f"❌ Timeout waiting for element with all {len(xpaths)} selectors")
                    # Log current page state for debugging
                    try:
                        current_url = self.driver.current_url
                        page_title = self.driver.title
                        self.logger.error(f"🔍 Current URL: {current_url}")
                        self.logger.error(f"🔍 Page title: {page_title}")
                        
                        # Check if any buttons exist at all
                        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        self.logger.error(f"🔍 Found {len(all_buttons)} buttons on page")
                        
                        # Log first few button texts for debugging
                        for idx, btn in enumerate(all_buttons[:5]):
                            try:
                                btn_text = btn.text.strip()
                                btn_class = btn.get_attribute("class") or ""
                                self.logger.error(f"🔍 Button {idx+1}: '{btn_text}' (class: {btn_class[:50]})")
                            except:
                                pass
                    except:
                        pass
                else:
                    self.logger.debug(f"⚠️ Selector {i+1} failed, trying next: {xpath[:100]}...")
                continue
            except Exception as e:
                if i == len(xpaths) - 1:  # Last selector failed
                    self.logger.error(f"❌ Error clicking element: {e}")
                else:
                    self.logger.debug(f"⚠️ Selector {i+1} error, trying next: {e}")
                continue
        
        return False
    
    def wait_and_fill(self, xpath: str, text: str, timeout: int = 30) -> bool:
        """Wait for element and fill with text"""
        # Check if driver is initialized
        if not self.driver or not self.wait:
            self.logger.error("❌ WebDriver not initialized. Call setup_chrome() first.")
            return False
        
        try:
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            element.clear()
            element.send_keys(text)
            self.logger.info(f"✅ Filled element {xpath} with text: {text[:50]}...")
            return True
        except TimeoutException:
            self.logger.error(f"❌ Timeout waiting for element: {xpath}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error filling element {xpath}: {e}")
            return False
    
    def select_dropdown_option(self, option_text: str) -> bool:
        """Select option from dropdown by text"""
        try:
            # Try to find option by text
            option_xpath = f"//*[contains(text(), '{option_text}')]"
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            element.click()
            self.logger.info(f"✅ Selected dropdown option: {option_text}")
            return True
        except TimeoutException:
            self.logger.error(f"❌ Timeout selecting option: {option_text}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error selecting option {option_text}: {e}")
            return False
    
    def navigate_to_veo(self) -> bool:
        """Navigate to Google Veo Flow"""
        try:
            self.logger.info("🌐 Navigating to Google Veo Flow...")
            self.driver.get("https://labs.google/fx/vi/tools/flow")
            
            # Wait for page to fully load
            if not self.wait_for_page_load():
                self.logger.warning("⚠️ Page loading timeout, continuing anyway...")
            
            # Check if page is refreshing (with timeout to prevent infinite loops)
            refresh_attempts = 0
            max_refresh_attempts = 2  # Reduced from 3 to 2
            refresh_start_time = time.time()
            max_refresh_time = 30  # Maximum 30 seconds for refresh detection
            
            while refresh_attempts < max_refresh_attempts and (time.time() - refresh_start_time) < max_refresh_time:
                is_refreshing = self.check_for_page_refresh()
                
                if not is_refreshing:
                    self.logger.info("✅ Page appears stable, no refresh detected")
                    break
                
                refresh_attempts += 1
                self.logger.info(f"🔄 Page might be refreshing, waiting... (attempt {refresh_attempts}/{max_refresh_attempts})")
                time.sleep(3)  # Reduced from 5 to 3 seconds
                
                if not self.wait_for_page_load(timeout=15):  # Reduced timeout
                    self.logger.warning("⚠️ Page still loading after refresh wait")
                    break  # Break if page won't load
            
            if refresh_attempts >= max_refresh_attempts:
                self.logger.warning("⚠️ Refresh detection limit reached, proceeding anyway...")
            elif (time.time() - refresh_start_time) >= max_refresh_time:
                self.logger.warning("⚠️ Refresh detection timeout, proceeding anyway...")
            
            self.logger.info("✅ Navigated to Veo Flow!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False
    
    def create_video_project(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create video project on Veo 3
        
        Args:
            config: {
                'type': 'Text to Video' | 'Image to Video',
                'model': 'Veo 3 Fast' | 'Veo 3 Quality' | etc.,
                'count': '1' | '2' | '3' | '4',
                'prompt': 'Generated prompt from Gemini AI'
            }
            
        Returns:
            Dict with success status and details
        """
        result = {
            'success': False,
            'error': None,
            'details': {},
            'steps_completed': []
        }
        
        try:
            self.logger.info("🎬 Starting video project creation...")
            
            # Step 1: Click "Dự án mới" button
            self.logger.info("📝 Step 1: Creating new project...")
            if not self.wait_and_click(self.SELECTORS["new_project"]):
                result['error'] = "Failed to click new project button"
                return result
            result['steps_completed'].append("new_project")
            
            # Wait for page load
            time.sleep(5)
            
            # Step 2: Select generation type
            self.logger.info(f"🎯 Step 2: Selecting type: {config.get('type', 'Text to Video')}")
            if not self.wait_and_click(self.SELECTORS["type_dropdown"]):
                result['error'] = "Failed to click type dropdown"
                return result
            
            time.sleep(1)
            if not self.select_dropdown_option(config.get('type', 'Text to Video')):
                result['error'] = f"Failed to select type: {config.get('type')}"
                return result
            result['steps_completed'].append("type_selection")
            
            # Step 3: Open settings
            self.logger.info("⚙️ Step 3: Opening settings...")
            if not self.wait_and_click(self.SELECTORS["settings_button"]):
                result['error'] = "Failed to click settings button"
                return result
            result['steps_completed'].append("settings_opened")
            
            time.sleep(2)
            
            # Step 4: Select model
            self.logger.info(f"🤖 Step 4: Selecting model: {config.get('model', 'Veo 3 Fast')}")
            if not self.wait_and_click(self.SELECTORS["model_dropdown"]):
                result['error'] = "Failed to click model dropdown"
                return result
            
            time.sleep(1)
            if not self.select_dropdown_option(config.get('model', 'Veo 3 Fast')):
                result['error'] = f"Failed to select model: {config.get('model')}"
                return result
            result['steps_completed'].append("model_selected")
            
            # Step 5: Select video count
            self.logger.info(f"🔢 Step 5: Selecting count: {config.get('count', '1')}")
            if not self.wait_and_click(self.SELECTORS["count_dropdown"]):
                result['error'] = "Failed to click count dropdown"
                return result
            
            time.sleep(1)
            if not self.select_dropdown_option(config.get('count', '1')):
                result['error'] = f"Failed to select count: {config.get('count')}"
                return result
            result['steps_completed'].append("count_selected")
            
            # Step 6: Fill prompt
            prompt = config.get('prompt', '')
            if not prompt:
                result['error'] = "No prompt provided"
                return result
                
            self.logger.info(f"✍️ Step 6: Filling prompt: {prompt[:50]}...")
            if not self.wait_and_fill(self.SELECTORS["prompt_textarea"], prompt):
                result['error'] = "Failed to fill prompt textarea"
                return result
            result['steps_completed'].append("prompt_filled")
            
            time.sleep(2)
            
            # Step 7: Create video
            self.logger.info("🎬 Step 7: Creating video...")
            if not self.wait_and_click(self.SELECTORS["create_button"]):
                result['error'] = "Failed to click create button"
                return result
            result['steps_completed'].append("video_created")
            
            # Success!
            result['success'] = True
            result['details'] = {
                'type': config.get('type'),
                'model': config.get('model'),
                'count': config.get('count'),
                'prompt_length': len(prompt)
            }
            
            self.logger.info("🎉 Video project created successfully!")
            
        except Exception as e:
            result['error'] = f"Automation error: {str(e)}"
            self.logger.error(f"❌ Automation failed: {e}")
        
        return result
    
    def load_cookies_from_profile(self) -> bool:
        """Load cookies from profile using CDP"""
        try:
            self.logger.info("🍪 Loading cookies from profile...")
            
            # Try to load cookies from saved file first (more reliable)
            cookies_file = Path(f"data/profile_cookies/{self.profile_name}.json")
            if cookies_file.exists():
                try:
                    with open(cookies_file, 'r', encoding='utf-8') as f:
                        cookies_data = json.load(f)
                    
                    # Add cookies to current session
                    for cookie in cookies_data:
                        try:
                            # Convert to Selenium cookie format
                            selenium_cookie = {
                                'name': cookie['name'],
                                'value': cookie['value'],
                                'domain': cookie['domain'],
                                'path': cookie.get('path', '/'),
                            }
                            if 'expires' in cookie and cookie['expires'] > 0:
                                selenium_cookie['expiry'] = int(cookie['expires'])
                            
                            self.driver.add_cookie(selenium_cookie)
                        except Exception as cookie_error:
                            self.logger.debug(f"⚠️ Could not add cookie {cookie['name']}: {cookie_error}")
                    
                    self.logger.info(f"✅ Loaded {len(cookies_data)} cookies from file")
                    return True
                    
                except Exception as file_error:
                    self.logger.warning(f"⚠️ Could not load cookies from file: {file_error}")
            
            # Fallback to CDP (if file method fails)
            try:
                from .cdp_client import CDPClient
                cdp = CDPClient()
                
                # Extract cookies for Veo domains
                veo_urls = [
                    "https://labs.google.com",
                    "https://accounts.google.com",
                    "https://google.com"
                ]
                
                cookies = cdp.extract_cookies_sync(veo_urls)
                if cookies:
                    # Add cookies to current session
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie({
                                'name': cookie['name'],
                                'value': cookie['value'],
                                'domain': cookie.get('domain', '.google.com'),
                                'path': cookie.get('path', '/'),
                                'secure': cookie.get('secure', True),
                                'httpOnly': cookie.get('httpOnly', False)
                            })
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to add cookie {cookie['name']}: {e}")
                    
                    self.logger.info(f"✅ Loaded {len(cookies)} cookies")
                    return True
                    
            except Exception as cdp_error:
                self.logger.warning(f"⚠️ CDP cookie extraction failed: {cdp_error}")
            
            self.logger.warning("⚠️ No cookies found")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load cookies: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for page to finish loading"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait a bit more for dynamic content
            time.sleep(3)
            
            self.logger.info("✅ Page loading complete")
            return True
        except Exception as e:
            self.logger.error(f"❌ Page loading timeout: {e}")
            return False
    
    def check_for_page_refresh(self) -> bool:
        """Check if page is refreshing/reloading"""
        try:
            # Check if we're still on the expected URL
            current_url = self.driver.current_url
            expected_urls = [
                "https://labs.google.com",
                "https://labs.google/fx",
                "https://labs.google/fx/vi/tools/flow"
            ]
            
            # Check if current URL matches any expected pattern
            url_matches = any(current_url.startswith(expected) for expected in expected_urls)
            
            if not url_matches:
                self.logger.warning(f"⚠️ Unexpected URL: {current_url}")
                return True
            
            # Check for loading indicators
            loading_indicators = [
                "//div[contains(@class, 'loading')]",
                "//div[contains(@class, 'spinner')]",
                "//*[contains(text(), 'Loading')]",
                "//*[contains(text(), 'Please wait')]",
                "//div[contains(@class, 'loader')]",
                "//*[@role='progressbar']"
            ]
            
            for indicator in loading_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements and any(elem.is_displayed() for elem in elements):
                        self.logger.info(f"🔄 Page is loading (found indicator: {indicator})")
                        return True
                except:
                    continue
            
            # Additional check: see if page has basic content
            try:
                # If page has buttons or main content, it's likely not refreshing
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                main_content = self.driver.find_elements(By.TAG_NAME, "main")
                
                if len(buttons) > 0 or len(main_content) > 0:
                    self.logger.debug(f"🔍 Page has content: {len(buttons)} buttons, {len(main_content)} main elements")
                    return False  # Page has content, probably not refreshing
                else:
                    self.logger.debug(f"🔍 Page appears empty, might be loading...")
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            self.logger.error(f"❌ Error checking page refresh: {e}")
            return False
    
    def check_login_status(self) -> bool:
        """Check if user is logged in to Google Veo"""
        try:
            # Look for login indicators
            login_indicators = [
                "//button[contains(text(), 'Sign in')]",
                "//a[contains(text(), 'Sign in')]",
                "//*[contains(@class, 'signin')]"
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        self.logger.warning("⚠️ User not logged in")
                        return False
                except NoSuchElementException:
                    continue
            
            self.logger.info("✅ User appears to be logged in")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking login status: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("✅ Chrome driver cleaned up")
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")
    
    def run_full_automation(self, prompt_file: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full automation workflow
        
        Args:
            prompt_file: Path to file containing Gemini-generated prompts
            config: Video generation configuration
            
        Returns:
            Dict with results
        """
        result = {
            'success': False,
            'error': None,
            'videos_created': 0,
            'details': []
        }
        
        try:
            # Setup Chrome
            if not self.setup_chrome():
                result['error'] = "Failed to setup Chrome"
                return result
            
            # Navigate to Veo
            if not self.navigate_to_veo():
                result['error'] = "Failed to navigate to Veo"
                return result
            
            # Load cookies (optional - may already be in profile)
            self.load_cookies_from_profile()
            
            # Check login status
            if not self.check_login_status():
                result['error'] = "User not logged in to Google Veo"
                return result
            
            # Load prompts from file
            if not os.path.exists(prompt_file):
                result['error'] = f"Prompt file not found: {prompt_file}"
                return result
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts_content = f.read()
            
            # Parse prompts (assuming one prompt per line or JSON format)
            prompts = []
            try:
                # Try JSON first
                prompts_data = json.loads(prompts_content)
                if isinstance(prompts_data, list):
                    prompts = prompts_data
                elif isinstance(prompts_data, dict) and 'prompts' in prompts_data:
                    prompts = prompts_data['prompts']
                else:
                    prompts = [prompts_content.strip()]
            except json.JSONDecodeError:
                # Fallback to text format
                prompts = [line.strip() for line in prompts_content.split('\n') if line.strip()]
            
            if not prompts:
                result['error'] = "No prompts found in file"
                return result
            
            # Create videos for each prompt
            for i, prompt in enumerate(prompts):
                self.logger.info(f"🎬 Creating video {i+1}/{len(prompts)}")
                
                video_config = config.copy()
                video_config['prompt'] = prompt
                
                video_result = self.create_video_project(video_config)
                result['details'].append({
                    'prompt_index': i,
                    'prompt': prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    'result': video_result
                })
                
                if video_result['success']:
                    result['videos_created'] += 1
                    self.logger.info(f"✅ Video {i+1} created successfully")
                else:
                    self.logger.error(f"❌ Video {i+1} failed: {video_result['error']}")
                
                # Wait between videos
                if i < len(prompts) - 1:
                    time.sleep(5)
            
            result['success'] = result['videos_created'] > 0
            
        except Exception as e:
            result['error'] = f"Full automation error: {str(e)}"
            self.logger.error(f"❌ Full automation failed: {e}")
        
        finally:
            self.cleanup()
        
        return result

# Example usage functions
def create_video_from_prompts(profile_name: str, prompt_file: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to create videos from prompt file
    
    Args:
        profile_name: Chrome profile to use
        prompt_file: Path to Gemini-generated prompts
        config: Video configuration
        
    Returns:
        Automation results
    """
    automation = VeoAutomation(profile_name)
    return automation.run_full_automation(prompt_file, config)

def test_veo_automation(profile_name: str) -> Dict[str, Any]:
    """
    Test function for Veo automation
    
    Args:
        profile_name: Chrome profile to use
        
    Returns:
        Test results
    """
    test_config = {
        'type': 'Text to Video',
        'model': 'Veo 3 Fast',
        'count': '1',
        'prompt': 'A beautiful sunset over the ocean with gentle waves'
    }
    
    automation = VeoAutomation(profile_name)
    
    # Setup and navigate
    if not automation.setup_chrome():
        return {'success': False, 'error': 'Chrome setup failed'}
    
    if not automation.navigate_to_veo():
        return {'success': False, 'error': 'Navigation failed'}
    
    # Test video creation
    result = automation.create_video_project(test_config)
    automation.cleanup()
    
    return result 