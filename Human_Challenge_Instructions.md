# Human-in-the-Loop TopCV Crawler - Instructions

## 🚀 How It Works

The TopCV crawler now supports **human-in-the-loop challenge solving** to bypass Cloudflare protection:

### 1. **Automatic Browser Opening**
- A visible Chrome browser window will open automatically
- The crawler navigates to TopCV pages
- When it encounters a Cloudflare challenge, it pauses and waits for you

### 2. **Manual Challenge Solving**
When you see a Cloudflare challenge page:
- ✅ **Click any verification checkboxes**
- ✅ **Solve any CAPTCHAs presented**
- ✅ **Wait for the "Verify you are human" process to complete**
- ✅ **The page should redirect to actual TopCV content**

### 3. **Automatic Continuation**
- The crawler detects when the challenge is solved
- It automatically continues crawling job listings
- You can watch the automated process in action

## 🎯 Using the Web Interface

### Option A: Through Admin Dashboard
1. Go to `http://localhost:3030/admin/data-sources`
2. Find the TopCV data source
3. Click the "Sync" button
4. Select "TopCV" from the dropdown
5. A browser window will open - solve any challenges that appear
6. Watch the progress in the sync modal

### Option B: Direct Test Script
Run the test script we just created:
```bash
cd backend
poetry run python test_human_challenge.py
```

## 🔧 Configuration

The crawler is now configured with:
- **Visible browser** (headless = false)
- **2 minute timeout** for challenge solving
- **Slower automation** to appear more human-like
- **Browser stays open** for inspection after crawling

## 📝 What to Expect

### Success Case:
1. Browser opens to TopCV homepage ✅
2. Navigates to job search page
3. **Challenge appears** → Solve it manually
4. **Jobs are found and extracted** ✅
5. Progress shown in web interface

### Blocked Case:
1. Browser opens ✅  
2. Challenge appears but can't be solved
3. Helpful error message explaining the situation
4. Browser stays open for manual inspection

## 💡 Tips

- **Keep the browser window visible** during crawling
- **Don't close the browser manually** until crawling is complete
- **The crawler waits up to 2 minutes** for you to solve challenges
- **Multiple challenges may appear** for different pages

This approach gives you the best chance of successfully crawling TopCV while respecting their anti-bot measures.
