# Gmail App Password Setup Guide

## Problem
The SMTP authentication failed with error: "Username and Password not accepted"

## Solution

### Step 1: Generate a new Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Sign in with your Google account (estradingmachine@gmail.com)
3. Select "Mail" as the app
4. Select your device (or "Other" and type "ESMH.TRADE")
5. Click "Generate"
6. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### Step 2: Update .env file

Replace the SMTP_PASSWORD in `.env` with the new password:

```env
SMTP_USER=estradingmachine@gmail.com
SMTP_PASSWORD=your_new_16_char_password
```

### Step 3: Test again

```powershell
python test_email.py
```

## Important Notes

- The password you provided (`gkph ihad cnog zyoc`) appears to be scrambled or incorrect
- Gmail App Passwords are 16 characters, usually shown as 4 groups of 4 letters
- Make sure 2-Step Verification is enabled on your Google account
- If you can't generate an App Password, check:
  - 2-Step Verification is ON (https://myaccount.google.com/security)
  - No security alerts on your account
  - "Less secure app access" is not blocked

## Alternative: Use SendGrid or Mailgun

If Gmail doesn't work, consider using a transactional email service:

### SendGrid (Free tier: 100 emails/day)
```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

### Mailgun (Free tier: 5,000 emails/month)
```env
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your_domain
SMTP_PASSWORD=your_mailgun_password
```
