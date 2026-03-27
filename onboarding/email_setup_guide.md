# Gmail Setup Guide

## Overview

This guide walks you through connecting the system to a Gmail account so it can create email drafts or send candidate feedback directly from your HR inbox.

---

## Step 1: Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **New Project** and give it a name such as `hr-feedback-automation`
3. Select the project once it is created

---

## Step 2: Enable the Gmail API

1. In the left menu, go to **APIs & Services > Library**
2. Search for **Gmail API**
3. Click **Enable**

---

## Step 3: Create OAuth 2.0 credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. If prompted, configure the OAuth consent screen first:
   - User type: **Internal** (for Google Workspace) or **External**
   - Add your HR email as a test user if using External
4. Application type: **Desktop app**
5. Give it a name and click **Create**
6. Download the credentials JSON file
7. Rename it to `credentials.json` and place it in the root of this project

---

## Step 4: Configure your environment

In your `.env` file, set:

```
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
SENDER_EMAIL=hr@yourcompany.com
MOCK_EMAIL=false
```

---

## Step 5: Authorise the application

On first run, the application will open a browser window asking you to sign in with the Gmail account you want to send from.

1. Start the API server: `uvicorn app.main:app --reload`
2. Make any API call that triggers an email send (or call the `/api/feedback/{id}/approve` endpoint from the dashboard)
3. A browser tab will open — sign in and grant the requested permissions
4. A `token.json` file will be saved automatically for future use

---

## Permissions requested

The system requests the following Gmail scopes:

- `https://www.googleapis.com/auth/gmail.send` — to send emails
- `https://www.googleapis.com/auth/gmail.compose` — to create drafts

No read access to your inbox is requested.

---

## Testing without Gmail

Set `MOCK_EMAIL=true` in your `.env` file to skip Gmail entirely during development. Emails will be printed to the terminal console instead of sent.

---

## Troubleshooting

**`credentials.json not found`**
Make sure you downloaded the credentials file from Google Cloud Console and placed it in the project root directory.

**`Token has been expired or revoked`**
Delete `token.json` and restart the server to re-authorise.

**`Access blocked: this app's request is invalid`**
Make sure the OAuth consent screen is configured and your email is added as a test user if the app is in External mode.
