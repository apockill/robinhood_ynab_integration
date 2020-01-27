# Robinhood ➡️ Ynab
Import stocks and cash management information to your You Need A Budget (YNAB) account!

If you're an avid user of YNAB you probably already realized that there is currently no way to automatically import Robinhood information. This script + Google Cloud Functions is the way that I've gotten around this. 

# How It Works
Basically, you create two "Unlinked" accounts on your YNAB. 

- Account 1 (Checking): A "Checking" type account. Call it "Checking @ Robinhood" or whatever you like to name your accounts.
- Account 2 (Stocks): A "Tracking" type account. Call it "Stocks @ Robinhood" or whatever you like to name your equity accounts.

The "Checking" account will reflect purchases, sales, dividends, and transfers in and out of your robinhood. 

The "Stocks" account will be automatically updated to reflect the current value of your Robinhood account. 

# Instructions
## Running the Script
### Initial Setup
To enter account information, run this block in a terminal as one line.
```commandline
read -p "Robinhood Username: " RH_USERNAME && \
read -p "Robinhood Password: " -s RH_PASS && \
read -p "Robinhood 2FA QR Code: " RH_QR_CODE && \
read -p "Name of your YNAB account for Robinhood 'Checking': " RH_CHECKING_ACC && \
read -p "Name of the YNAB account for Robinhood 'Stocks': " RH_ASSETS_ACC && \
read -p "YNAB API Key: " -s YNAB_API_KEY
```
Install Dependencies:
```commandline
pip install -r requirements.txt
```
