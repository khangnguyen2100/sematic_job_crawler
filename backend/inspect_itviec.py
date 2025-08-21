#!/usr/bin/env python3
"""
Script to inspect ITViec page structure after bypassing Cloudflare
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import time

async def bypass_cloudflare_and_inspect():
    """Use cloudscraper-style approach to bypass Cloudflare and inspect page structure"""
    
    print("🔍 Inspecting ITViec page structure with Cloudflare bypass...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        try:
            # Step 1: Get homepage to establish session
            print("📡 Getting homepage to establish session...")
            home_response = await client.get('https://itviec.com', headers=headers)
            print(f"   Homepage status: {home_response.status_code}")
            
            # Add some delay to mimic human behavior
            await asyncio.sleep(2)
            
            # Step 2: Try to get job listing page
            job_url = 'https://itviec.com/it-jobs?q=python&sort=published&page=1'
            print(f"📄 Getting job listing page: {job_url}")
            
            response = await client.get(job_url, headers=headers)
            print(f"   Job page status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                print(f"\n📊 Page Analysis:")
                print(f"   Title: {soup.title.string if soup.title else 'No title'}")
                print(f"   Body text length: {len(soup.body.get_text()) if soup.body else 0} characters")
                
                # Check if it's still a challenge page
                if "Just a moment" in soup.get_text() or "challenge" in soup.get_text().lower():
                    print("   ❌ Still showing Cloudflare challenge page")
                    return
                
                print("   ✅ Got real content!")
                
                # Look for various job-related patterns
                patterns_to_check = [
                    # Modern React/Vue patterns
                    ('div[data-testid*="job"]', 'data-testid job elements'),
                    ('div[id*="job"]', 'id job elements'),
                    ('div[class*="job"]', 'class job elements'),
                    ('[data-cy*="job"]', 'cypress job elements'),
                    
                    # Card patterns
                    ('div[class*="card"]', 'card elements'),
                    ('[class*="item"]', 'item elements'),
                    ('[class*="listing"]', 'listing elements'),
                    
                    # Common structure patterns
                    ('article', 'article elements'),
                    ('[role="listitem"]', 'listitem role elements'),
                    ('li', 'list item elements'),
                    
                    # ITViec specific patterns (guessed)
                    ('[data-job-id]', 'data-job-id elements'),
                    ('.job-post', 'job-post class'),
                    ('.job-card', 'job-card class'),
                    ('.job-item', 'job-item class'),
                ]
                
                print(f"\n🔍 Looking for job elements:")
                found_elements = {}
                
                for selector, description in patterns_to_check:
                    elements = soup.select(selector)
                    count = len(elements)
                    print(f"   {description}: {count} elements")
                    
                    if count > 0:
                        found_elements[selector] = elements
                        
                        # Show sample of first element
                        first_elem = elements[0]
                        print(f"      Sample: {str(first_elem)[:150]}...")
                        
                        # Look for text that suggests job content
                        text = first_elem.get_text()
                        if any(word in text.lower() for word in ['developer', 'engineer', 'software', 'programmer', 'python', 'java', 'javascript']):
                            print(f"      🎯 Contains job-related text!")
                
                # If we found promising elements, analyze further
                if found_elements:
                    print(f"\n🎯 Detailed analysis of most promising elements:")
                    
                    # Pick the most promising selector
                    for selector, elements in found_elements.items():
                        if len(elements) > 5:  # Likely job listings if we have many
                            print(f"\n📋 Analyzing {selector} ({len(elements)} elements):")
                            
                            for i, elem in enumerate(elements[:3]):
                                print(f"   Element {i+1}:")
                                print(f"      Classes: {elem.get('class', [])}")
                                print(f"      Attributes: {dict(elem.attrs)}")
                                
                                # Look for title, company, location patterns
                                title_candidates = elem.select('h1, h2, h3, h4, h5, h6, [class*="title"], [class*="job"], a')
                                if title_candidates:
                                    print(f"      Title candidates: {[t.get_text().strip()[:50] for t in title_candidates[:2]]}")
                                
                                company_candidates = elem.select('[class*="company"], [class*="employer"]')
                                if company_candidates:
                                    print(f"      Company candidates: {[c.get_text().strip()[:50] for c in company_candidates[:2]]}")
                            
                            break
                
                # Save a sample of the HTML for manual inspection
                print(f"\n💾 Saving page sample to /tmp/itviec_sample.html")
                with open('/tmp/itviec_sample.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup.prettify()))
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error during inspection: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(bypass_cloudflare_and_inspect())
