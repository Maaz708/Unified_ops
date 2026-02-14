# Deployment Guide

## Option 1: Render (Recommended)

### Prerequisites
- GitHub account with your code pushed
- Render account (free tier available)
- Gemini API key
- Resend API key (for emails)

### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

3. **Deploy Backend**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select root directory
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables:
     - `DATABASE_URL`: (will be auto-created)
     - `JWT_SECRET_KEY`: Generate random string
     - `GEMINI_API_KEY`: Your Gemini API key
     - `RESEND_API_KEY`: Your Resend API key

4. **Create Database**
   - Click "New" → "PostgreSQL"
   - Name: `hackathon-db`
   - Plan: Free
   - Connect to your backend service

5. **Deploy Frontend**
   - Click "New" → "Static Site"
   - Connect your GitHub repository
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/out`
   - Add environment variable:
     - `NEXT_PUBLIC_API_URL`: `https://your-backend-name.onrender.com/api/v1`

6. **Update CORS Settings**
   - In backend environment variables, add:
     - `ALLOWED_ORIGINS`: `https://your-frontend-name.onrender.com`

### Alternative: Railway

Similar setup to Render:
1. Create Railway account
2. Import from GitHub
3. Set up PostgreSQL database
4. Deploy backend and frontend separately

### Alternative: Vercel + Railway/PlanetScale

- Frontend: Vercel (excellent for Next.js)
- Backend: Railway or PlanetScale for database
- API: Railway for Python backend

## Environment Variables Needed

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Random secret for JWT tokens
- `GEMINI_API_KEY`: Your Gemini API key
- `RESEND_API_KEY`: Your Resend API key
- `ALLOWED_ORIGINS`: Your frontend URL(s)

### Frontend
- `NEXT_PUBLIC_API_URL`: Your backend API URL

## Post-Deployment Checklist

1. **Test API Health**
   - Visit `https://your-backend-name.onrender.com/api/v1/health`
   - Should return `{"status": "ok"}`

2. **Test Frontend**
   - Visit `https://your-frontend-name.onrender.com`
   - Should load your application

3. **Test Workspace Creation**
   - Try creating a new workspace
   - Check if emails are sent (if Resend is configured)

4. **Test Booking Flow**
   - Create availability slots
   - Test customer booking page

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Make sure `ALLOWED_ORIGINS` includes your frontend URL
   - Check for trailing slashes in URLs

2. **Database Connection**
   - Verify DATABASE_URL is correct
   - Check if database is running

3. **Build Failures**
   - Check build logs
   - Make sure all dependencies are in requirements.txt

4. **Environment Variables**
   - Double-check all required variables are set
   - Make sure API keys are correct

### Performance Tips

1. **Free Tier Limitations**
   - Render free tier spins down after 15 minutes
   - First request may be slow (cold start)
   - Consider upgrading for production

2. **Database Optimization**
   - Add indexes for frequently queried fields
   - Monitor database performance

3. **Frontend Optimization**
   - Enable caching headers
   - Optimize images and assets

## Custom Domain (Optional)

1. **Render**
   - Go to service settings
   - Add custom domain
   - Update DNS records

2. **Frontend**
   - Update `NEXT_PUBLIC_API_URL` if needed
   - Update `ALLOWED_ORIGINS` in backend

## Monitoring

- Render provides basic monitoring
- Check logs regularly
- Set up alerts for errors
- Monitor database usage
