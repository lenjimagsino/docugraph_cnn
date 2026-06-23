# Railway Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click **"Start Project"**
3. Sign in with **GitHub**

### Step 2: Deploy from GitHub
1. Click **"Deploy from GitHub repo"**
2. Select: `lenjimagsino/docugraph_cnn`
3. Click **"Deploy"**

Railway automatically detects:
- ✅ `requirements.txt` for Python dependencies
- ✅ `backend/app.py` as entry point
- ✅ Starts the Flask server

### Step 3: Get Your Backend URL
After deployment (2-3 minutes):
1. Go to your Railway project dashboard
2. Copy the **public URL** (e.g., `https://docugraph-api.up.railway.app`)
3. Update `assets/cnn_only.js` line 45 with your URL

### Step 4: Update Frontend
Edit `assets/cnn_only.js`:
```javascript
window.BACKEND_URL = 'https://docugraph-api.up.railway.app'; // Your Railway URL
```

Push to GitHub:
```bash
git add assets/cnn_only.js
git commit -m "Update backend URL to Railway deployment"
git push
```

GitHub Pages automatically updates! ✨

---

## Full Setup Flow

```
┌─────────────────────────┐
│   GitHub Pages          │
│   Frontend              │
│   (HTML/CSS/JS)         │
│                         │
│ https://lenjimagsino    │
│ .github.io/docugraph_cnn │
└────────────┬────────────┘
             │ API calls to
             ↓
┌─────────────────────────┐
│   Railway.app           │
│   Backend (Flask)       │
│   (Python)              │
│                         │
│ https://docugraph-api   │
│ .up.railway.app         │
└─────────────────────────┘
```

---

## Environment Variables (Optional)

If needed, set in Railway dashboard:
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `WORKERS=2`

---

## Troubleshooting

**Issue**: "Cannot connect to backend"
- ✅ Wait 2-3 min for Railway to deploy
- ✅ Check Railway dashboard for errors
- ✅ Verify backend URL in `assets/cnn_only.js`

**Issue**: "CORS error"
- ✅ Already configured in `backend/app.py`
- ✅ Supports `github.io` domains

**Issue**: "Backend offline"
- ✅ Check Railway project status
- ✅ Restart deployment from dashboard

---

## Cost

**Railway Free Tier:**
- ✅ $5/month free credit
- ✅ Covers small projects
- ✅ Perfect for this application

---

## Next Steps

1. Deploy to Railway (5 min)
2. Update `assets/cnn_only.js` with your URL
3. Push to GitHub
4. Visit: `https://lenjimagsino.github.io/docugraph_cnn/`
5. Click **"Start Analysis"** and upload a document!

🚀 Ready to go live!
