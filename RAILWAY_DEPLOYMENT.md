# 🚀 Deploy Online in 3 Minutes

Your DOCUGRAPH CNN-Only website is ready to go online **WITHOUT manually opening the backend**.

---

## **Step 1: Deploy Backend to Railway (FREE)**

### 1.1 Go to Railway
- Visit https://railway.app
- Click **"Start Project"**
- Sign in with **GitHub**

### 1.2 Deploy from Repository
- Click **"Deploy from GitHub repo"**
- Select: `lenjimagsino/docugraph_cnn`
- Click **"Deploy"**

✅ Railway automatically:
- Detects `requirements.txt` and installs dependencies
- Finds `Procfile` and starts the Flask server
- Gives you a public URL (wait 2-3 minutes)

---

## **Step 2: Get Your Backend URL**

1. Open your Railway dashboard
2. Click on your project
3. Go to **"Settings"**
4. Copy the **Public URL** (looks like: `https://docugraph-cnn-xxxxx.up.railway.app`)

---

## **Step 3: Update Backend URL in Code**

Edit `assets/config.js`:

```javascript
// Line 6 - Replace with your Railway URL
BACKEND_URL_PRODUCTION: 'https://your-railway-url.up.railway.app',
```

Example:
```javascript
BACKEND_URL_PRODUCTION: 'https://docugraph-cnn-prod-xyz.up.railway.app',
```

**Push to GitHub:**
```bash
git add assets/config.js
git commit -m "Update production backend URL"
git push
```

✅ GitHub Pages automatically updates!

---

## **Step 4: Test Your Website**

1. Go to: https://lenjimagsino.github.io/docugraph_cnn/
2. Click **"Start Analysis"**
3. Upload a document image
4. Click **"Analyze Layout"**
5. View results! 🎉

---

## **Complete Flow (After Setup)**

```
User visits GitHub Pages
           ↓
Frontend loads from: https://lenjimagsino.github.io/docugraph_cnn/
           ↓
Frontend calls backend: https://your-railway-url.up.railway.app/api/analyze
           ↓
Backend (Flask) running 24/7 on Railway
           ↓
Results sent back to frontend
           ↓
Display analysis with bounding boxes ✨
```

---

## **Cost Breakdown**

| Service | Cost | Why |
|---------|------|-----|
| **GitHub Pages** | FREE | Frontend static hosting |
| **Railway** | FREE* | Backend server ($5/month free credit) |
| **Total** | FREE | Everything you need |

*Railway free tier: $5/month credit covers this project easily

---

## **Troubleshooting**

| Problem | Solution |
|---------|----------|
| "Cannot connect to backend" | Wait 2-3 min for Railway to deploy |
| "Backend Offline" error | Check Railway dashboard for errors |
| "404 Error" on GitHub Pages | Wait 30 sec for GitHub to refresh |
| "CORS error" | Already configured - refresh browser |

---

## **Environment Variables (Optional)**

If needed in Railway dashboard → Settings → Variables:
```
FLASK_ENV=production
FLASK_DEBUG=0
WORKERS=2
```

---

## **Next Steps**

✅ Deploy to Railway (5 min)
✅ Update `assets/config.js` with your URL
✅ Push to GitHub
✅ Visit your live website
✅ Upload documents and analyze!

**Your website is now ONLINE and fully functional!** 🎊

Questions? Check `CNN_ONLY_ANALYSIS.md` or `IMPLEMENTATION_SUMMARY.md`
