# Facebook Graph API Integration Guide

This guide explains how to set up Facebook integration using the official Graph API.

## Overview

The AI Employee uses Facebook Graph API for:
- Monitoring page notifications (likes, comments, shares)
- Reading page messages
- Posting updates to your page
- Getting page insights

**Note:** This uses the official API, not browser automation.

## Prerequisites

- Facebook Business Account
- Facebook Page (you must be an admin)
- Facebook Developer Account

## Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Select **"Business"** as the app type
4. Fill in app details:
   - App Name: `AI Employee`
   - App Contact Email: your email
5. Click **"Create App"**

## Step 2: Add Facebook Login Product

1. In your app dashboard, click **"Add Product"**
2. Find **"Facebook Login"** → Click **"Set Up"**
3. Select **"Page Access"** as the use case
4. Configure settings:
   - Valid OAuth Redirect URIs: `https://localhost`
   - Save changes

## Step 3: Generate Access Token

1. Go to **Tools** → **Graph API Explorer**
2. Select your app from the dropdown
3. Click **"Generate New Token"** → **"Get Page Access Token"**
4. Select your Facebook Page
5. Add these permissions:
   - `pages_read_engagement` - Read page posts and engagement
   - `pages_manage_posts` - Create posts on page
   - `pages_read_user_content` - Read page messages and comments
   - `pages_manage_metadata` - Manage page settings
6. Click **"Generate Token"**
7. **Copy the access token** - you'll need this for `.env`

## Step 4: Get Long-Lived Token (Recommended)

Short-lived tokens expire in 1 hour. For production use:

1. Go to [Access Token Debugger](https://developers.facebook.com/tools/debug/access_token/)
2. Paste your token → Click **"Debug"**
3. Click **"Extend Access Token"**
4. Copy the new long-lived token (expires in 60 days)

## Step 5: Find Your Page ID

1. Go to your Facebook Page
2. Click **"About"**
3. Find **"Facebook Page ID"**
4. Or use: https://findmyfbid.com/

## Step 6: Configure Environment Variables

Edit your `.env` file:

```bash
# Facebook Graph API Configuration
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abc123def456ghi789jkl012mno345pq
FACEBOOK_ACCESS_TOKEN=EAAB... (your long token)
FACEBOOK_PAGE_ID=987654321098765
FACEBOOK_API_VERSION=v19.0
FACEBOOK_CHECK_INTERVAL=300
```

## Step 7: Test the Integration

```bash
# Test Facebook Graph API Watcher
cd scripts
python facebook_graph_watcher.py

# Test Facebook MCP Server
python facebook_mcp_server.py
```

## Available Features

### Facebook Graph Watcher

Monitors for:
- New likes on posts
- New comments on posts
- New page messages
- User notifications

Creates action files in `Needs_Action/`:
```
FACEBOOK_comment_20260306_170000.md
FACEBOOK_message_20260306_171500.md
FACEBOOK_like_20260306_173000.md
```

### Facebook MCP Server

Available tools for Qwen Code:

#### Post Update
```python
facebook_post_update(
    content="Exciting news about our product!",
    link="https://example.com"
)
```

#### Post Photo
```python
facebook_post_photo(
    content="Check out our new office!",
    photo_url="https://example.com/image.jpg"
)
```

#### Get Insights
```python
facebook_get_insights(metric="page_impressions_unique")
```

#### Get Recent Posts
```python
facebook_get_posts(limit=10)
```

#### Reply to Comment
```python
facebook_reply_to_comment(
    comment_id="123456_789012",
    message="Thanks for your feedback!"
)
```

#### Get Conversations
```python
facebook_get_conversations(limit=10)
```

## Troubleshooting

### Token Expired

```bash
# Generate new token from Graph API Explorer
# Update FACEBOOK_ACCESS_TOKEN in .env
```

### Permissions Error

Make sure your token has these permissions:
- `pages_read_engagement`
- `pages_manage_posts`
- `pages_read_user_content`

### Page Not Found

Verify your Page ID:
```bash
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN"
```

### API Version Deprecated

Check current version:
https://developers.facebook.com/docs/graph-api/guides/versioning

Update `FACEBOOK_API_VERSION` in `.env`

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| Page Posts | 200 posts/hour |
| Page Insights | 200 requests/hour |
| Messages | 100 requests/hour |

## Security Best Practices

1. **Never commit tokens** - `.env` is gitignored
2. **Use long-lived tokens** - Extend before expiration
3. **Limit permissions** - Only request what you need
4. **Rotate tokens** - Generate new tokens every 60 days
5. **Monitor usage** - Check Graph API Explorer for unusual activity

## Resources

- [Graph API Reference](https://developers.facebook.com/docs/graph-api)
- [Page API](https://developers.facebook.com/docs/pages/api)
- [Access Tokens](https://developers.facebook.com/docs/facebook-login/access-tokens)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer)
