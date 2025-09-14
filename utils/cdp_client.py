#!/usr/bin/env python3
"""
Chrome DevTools Protocol Client
Real-time communication với Chrome để extract cookies
"""

import json
import asyncio
import websockets
import requests
import time
from typing import Dict, List, Any
import threading

class CDPClient:
    def __init__(self, port=9222):
        self.port = port
        self.ws_url = None
        self.websocket = None
        self.message_id = 0
        self.responses = {}
        self.debug_port_url = f"http://localhost:{port}"
        
    def start_chrome_with_debug(self, chrome_exe, profile_path, veo_url=None):
        """Launch Chrome với debug port enabled"""
        import subprocess
        
        # Close existing Chrome processes
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
        except:
            pass
        
        # Launch Chrome with remote debugging
        args = [
            chrome_exe,
            f"--user-data-dir={profile_path}",
            f"--remote-debugging-port={self.port}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=TranslateUI",
            "--disable-default-apps"
        ]
        
        if veo_url:
            args.append(veo_url)
            
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for Chrome to start
        for i in range(10):
            try:
                response = requests.get(f"{self.debug_port_url}/json", timeout=2)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        else:
            raise Exception("Chrome debug port not accessible")
            
        return process
    
    def connect(self):
        """Connect to Chrome DevTools WebSocket"""
        try:
            # Get list of tabs
            response = requests.get(f"{self.debug_port_url}/json")
            tabs = response.json()
            
            if not tabs:
                raise Exception("No Chrome tabs found")
            
            # Use first tab
            tab = tabs[0]
            self.ws_url = tab['webSocketDebuggerUrl']
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to connect to Chrome DevTools: {e}")
    
    async def send_command(self, method, params=None):
        """Send CDP command và đợi response"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        
        self.message_id += 1
        message = {
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("id") == self.message_id:
                if "error" in data:
                    raise Exception(f"CDP Error: {data['error']}")
                return data.get("result", {})
    
    async def get_cookies(self, urls=None):
        """Extract cookies using CDP"""
        try:
            # Connect WebSocket
            async with websockets.connect(self.ws_url) as websocket:
                self.websocket = websocket
                
                # Enable Runtime and Network domains
                await self.send_command("Runtime.enable")
                await self.send_command("Network.enable")
                
                # Get cookies
                params = {}
                if urls:
                    params["urls"] = urls
                
                result = await self.send_command("Network.getCookies", params)
                return result.get("cookies", [])
                
        except Exception as e:
            raise Exception(f"Failed to get cookies via CDP: {e}")
    
    def extract_cookies_sync(self, urls=None):
        """Synchronous wrapper for cookie extraction"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_cookies(urls))
        except Exception as e:
            raise e
        finally:
            loop.close()
    
    def wait_for_login_and_extract(self, target_urls=None, timeout=300):
        """Đợi user login và extract cookies"""
        if not target_urls:
            target_urls = [
                "https://labs.google",
                "https://google.com", 
                "https://accounts.google.com",
                "https://googleapis.com"
            ]
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                cookies = self.extract_cookies_sync(target_urls)
                
                # Check if we have authentication cookies
                auth_cookies = []
                critical_cookies = []
                
                for cookie in cookies:
                    name = cookie.get('name', '')
                    domain = cookie.get('domain', '')
                    
                    # Check for Google auth indicators
                    if any(indicator in name for indicator in [
                        'SAPISID', 'SSID', 'HSID', 'APISID', 'SID',
                        'session-token', 'csrf-token', 'email'
                    ]):
                        auth_cookies.append(cookie)
                    
                    # Check for Veo critical cookies
                    if 'labs.google' in domain and any(indicator in name for indicator in [
                        'session-token', 'csrf-token', 'auth'
                    ]):
                        critical_cookies.append(cookie)
                
                # If we have authentication cookies, return them
                if auth_cookies or critical_cookies:
                    return {
                        'success': True,
                        'total_cookies': len(cookies),
                        'auth_cookies': len(auth_cookies),
                        'critical_cookies': len(critical_cookies),
                        'cookies': cookies,
                        'cookies_json': json.dumps(cookies, indent=2)
                    }
                
                # Wait before next check
                time.sleep(5)
                
            except Exception as e:
                print(f"CDP check error: {e}")
                time.sleep(5)
        
        # Timeout reached
        return {
            'success': False,
            'error': 'Timeout waiting for login cookies',
            'cookies': [],
            'cookies_json': '[]'
        } 