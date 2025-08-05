# Debug Directory

This directory contains debugging files and temporary artifacts from development.

## Current Files

- `inspect_topcv.py` - Script to inspect TopCV page structure using Playwright
- `topcv_page.html` - Captured HTML content from TopCV page
- `topcv_page.png` - Screenshot of TopCV page for visual inspection

## Purpose

These files were used for:

- 🔍 Understanding TopCV website structure
- 🎯 Developing crawler selectors
- 📸 Visual debugging of page layouts
- 🧪 Testing scraping strategies

## Recommendation

- ✅ **Keep `inspect_topcv.py`** - Useful for debugging crawler issues
- 🤔 **Archive HTML/PNG files** - These are snapshots from specific time and may become outdated
- 📝 **Consider adding .gitignore** for future debug artifacts

## Usage

```bash
# Run TopCV inspection
python debug/inspect_topcv.py
```

The script will generate new HTML and PNG files for current page state.
