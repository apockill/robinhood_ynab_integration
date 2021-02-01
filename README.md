# Robinhood ➡️ Ynab

Import stocks and cash management information to your You Need A Budget (YNAB)
account!

If you're an avid user of YNAB you probably already realized that there is
currently no way to automatically import Robinhood information. This script +
Google Cloud Functions is the way that I've gotten around this.

# How It Works

Basically, you create two "Unlinked" accounts on your YNAB.

- Account 1 (Checking): A "Checking" type account. Call it "Checking @
  Robinhood" or whatever you like to name your accounts.
- Account 2 (Stocks): A "Tracking" type account. Call it "Stocks @ Robinhood"
  or whatever you like to name your equity accounts.

The "Checking" account will reflect purchases, sales, dividends, and transfers
in and out of your robinhood.

The "Stocks" account will be automatically updated to reflect the current value
of your Robinhood equity.

# Instructions

## Setup

### For YNAB

1) First, get your YNAB api key
   using [these instructions](https://api.youneedabudget.com/). Take note of
   the API key.
2) Create two "unlinked" accounts on YNAB. Account 1 will be a "Checking" type
   account, Account 2 will be a "Tracking" type account, for the current value
   of any stocks. Take note of your chosen names for the accounts on YNAB.

### For Robinhood

1) Turn on 2FA on robinhood. To do this: go to settings, select turn on 2FA,
   select "Authentication App", click "Can't Scan It?", and take note of the
   16-character QR code.

### For running the script

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
poetry install
```

## Running the Script

With all of the previous setup complete, simply running the script should do
all the necessary operations. You can then check your YNAB to see the updated
transactional information and equity value.

```python
python3 sync_rh_to_ynab.py
```

# Instructions for Google Cloud Functions setup

(These instructions need fleshing out)

1. Zip up the source using the following command on the root of the repository
    ```commandline
    poetry export --without-hashes > requirements.txt
    zip source.zip * -r
    ```
    The `--without-hashes` flag prevents a bug with pip when pip installs from 
    a git repo that has hashes.
2. Upload the zip to a google cloud function
3. Use Google Cloud Scheduler to run the script once every day.
