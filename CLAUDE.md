# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon product availability monitor that uses Playwright for web scraping and provides notifications when products become available for purchase. The application continuously monitors Amazon product pages and alerts users via desktop notifications and email when a monitored product is back in stock.

## Setup and Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # or use alias: pyva

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for scraping)
playwright install chromium
```

### Configuration
Create `.env` file based on the following structure for email notifications:
```
FROM_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TO_EMAIL=destination@gmail.com
```

### Running the Application
```bash
# Activate virtual environment and run
pyva && python main.py
```

The application will:
1. Load product data from `product.json` if it exists
2. Start monitoring the configured Amazon product URL
3. Check availability every 5 minutes (configurable)
4. Send notifications when product becomes available
5. Automatically stop when product is found

## Architecture

### Core Components

**AmazonMonitor Class**: Main orchestrator that handles:
- Product URL monitoring with configurable check intervals
- Playwright-based web scraping with bot detection evasion
- Data persistence to JSON file
- Multi-channel notification system (desktop + email)

**Web Scraping Strategy**: Uses Playwright instead of requests/BeautifulSoup because:
- Bypasses Amazon's bot detection mechanisms
- Handles dynamic content loading
- Automatically deals with verification pages
- Provides more reliable product data extraction

**Availability Detection Logic**: Multi-layered approach:
1. Checks for visual availability indicators (CSS selectors)
2. Looks for "Em estoque" text in availability container
3. Verifies active "Add to Cart" buttons
4. Uses fallback text-based detection

### Data Flow

1. **First Run**: Extracts complete product information (title, price, availability, rating) and saves to `product.json`
2. **Subsequent Runs**: Loads existing product data and focuses on availability monitoring
3. **Detection**: When "Em estoque" is found, sends notifications and terminates
4. **Persistence**: Screenshots are saved to `screenshots/` directory for debugging

### File Structure

- `main.py`: Single-file application containing all functionality
- `product.json`: Persistent storage for product data (auto-generated)
- `screenshots/`: Debug screenshots with timestamp naming
- `.env`: Email configuration (not tracked in git)
- `requirements.txt`: Python dependencies including Playwright, colorlog, python-dotenv

### Key Configuration Points

- **PRODUCT_URL**: Main product to monitor (line ~335 in main.py)
- **CHECK_INTERVAL**: Time between checks in seconds (default: 300)
- **Email settings**: SMTP configuration for Gmail in main.py
- **Screenshot debugging**: Automatically enabled, saves full-page screenshots

### Notification System

The application uses a fallback notification approach:
1. Native desktop notifications via plyer
2. System notify-send command
3. Console output as final fallback

Email notifications require proper .env configuration with Gmail app passwords.

### Bot Detection Evasion

The scraper handles Amazon's verification pages by:
- Using realistic browser headers and viewport
- Detecting "Continuar comprando" buttons and clicking them automatically  
- Implementing proper wait times for page loading
- Using Playwright's network idle detection

### Logging

Colorized logging with emojis for better UX:
- 🔍 for availability checks
- ✅ for successful operations  
- ❌ for failures/unavailability
- 📧 for email operations
- 🔔 for notifications