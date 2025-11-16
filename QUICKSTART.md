# 🚀 Quick Start Guide

## Get Running in 5 Minutes!

### Step 1: Setup Environment (2 min)

```bash
# Make sure you're in the project directory
conda activate jobbot
pip install -r requirements.txt
```

### Step 2: Configure API Keys (1 min)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Get your FREE API keys:
   - **Adzuna**: https://developer.adzuna.com/signup (instant approval)
   - **RapidAPI**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch (free tier: 2500 requests/month)

3. Edit `.env` and paste your keys:
```
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

### Step 3: Start the Backend (1 min)

```bash
python app.py
```

You should see:
```
INFO - Starting server on 0.0.0.0:5000
INFO - All modules initialized successfully
```

### Step 4: Start the Frontend (1 min)

Open a **new terminal**:

```bash
cd frontend
python -m http.server 8000
```

### Step 5: Use the Bot! 🎉

1. Open your browser: **http://localhost:8000**
2. Type: "I know Python, JavaScript, and React"
3. Answer: "3 years experience"
4. See your personalized job recommendations!

## 🎯 Demo Mode (No API Keys Needed)

Want to try it without API keys? The frontend works in demo mode!

Just open `frontend/index.html` directly in your browser. It will show skill extraction but won't fetch real jobs.

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "Port 5000 already in use"
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9
```

### "No jobs found"
- Check your API keys in `.env`
- Try different skills (e.g., "Software Engineer Python")
- Check `logs/bot.log` for errors

### Frontend shows "Backend not connected"
- Make sure `python app.py` is running
- Check that it's on port 5000
- Try refreshing the page

## 📊 Test It Works

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```

Should return: `{"status": "healthy"}`

### Test 2: Skill Extraction
```bash
python test_skill_analyzer.py
```

Should show extracted skills from test text.

### Test 3: Full Flow
1. Open frontend
2. Type skills
3. See recommendations
4. Click "Apply"
5. Check `data/applications.xlsx`

## 🎓 Next Steps

- Add more skills to your profile
- Try different job searches
- Check your application history
- Explore skill gap analysis
- Set up email notifications (optional)

## 💡 Pro Tips

1. **Better Recommendations**: Be specific with skills (e.g., "React.js" not just "React")
2. **More Jobs**: Try broader searches (e.g., "Developer" vs "Senior React Developer")
3. **Cache**: Jobs are cached for 6 hours - delete `data/cache/` to refresh
4. **Logs**: Check `logs/bot.log` for debugging

## 🆘 Need Help?

- Check the main [README.md](README.md) for detailed docs
- Review [config.yaml](config.yaml) for settings
- Look at example API calls in the README
- Check the browser console for frontend errors

---

Happy job hunting! 🎯
