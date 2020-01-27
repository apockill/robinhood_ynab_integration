# Robinhood ➡️ Ynab
Import stocks and cash management information to your You Need A Budget (YNAB) account!

If you're an avid user of YNAB you probably already realized that there is currently no way to automatically import Robinhood information. This script + Google Cloud Functions is the way that I've gotten around this. 

# Quick 'how it works'
Basically, you create two "Unlinked" accounts on your YNAB. 

- Account 1 (Checking): A "Checking" type account. Call it "Checking @ Robinhood" or whatever you like to name your accounts.
- Account 2 (Stocks): A "Tracking" type account. Call it "Stocks @ Robinhood" or whatever you like to name your equity accounts.

The "Checking" account will reflect purchases, sales, dividends, and transfers in and out of your robinhood. 

The "Stocks" account will be automatically updated to reflect the current value of your Robinhood account. 
