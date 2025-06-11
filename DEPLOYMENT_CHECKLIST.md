# The5HC Deployment Checklist

## Pre-Deployment ✅
- [x] Procfile updated for root directory
- [x] runtime.txt set to python-3.12.1
- [x] requirements.txt complete with all dependencies
- [x] Production settings configured
- [x] .env.example created for reference
- [x] Aptfile created for WeasyPrint dependencies
- [x] Deployment script created
- [x] CORS settings configured
- [x] Logging configured for Heroku

## Deployment Steps 📋
1. [ ] Run deployment script: `./scripts/deploy_to_heroku.sh`
2. [ ] Verify environment variables are set
3. [ ] Push code to Heroku
4. [ ] Wait for build to complete
5. [ ] Check deployment logs

## Post-Deployment ⚡
- [ ] Create superuser account
- [ ] Test login functionality
- [ ] Test client CRUD operations
- [ ] Test assessment creation
- [ ] Test PDF report generation
- [ ] Test API endpoints
- [ ] Verify Korean language display
- [ ] Check static files loading
- [ ] Monitor error logs

## Troubleshooting 🔧
If issues arise:
1. Check logs: `heroku logs --tail`
2. Verify DATABASE_URL is set
3. Check static files with `heroku run python manage.py collectstatic`
4. Verify migrations: `heroku run python manage.py showmigrations`
5. Test locally with production settings: `DEBUG=False python manage.py runserver`

## Rollback if Needed 🔄
```bash
heroku releases
heroku rollback v[previous]
```