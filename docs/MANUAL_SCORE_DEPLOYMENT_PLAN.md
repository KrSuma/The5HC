# Manual Score Override Feature - Deployment Plan

**Date**: 2025-06-25
**Feature**: Manual Score Override for Physical Assessments
**Risk Level**: Medium (UI changes, scoring logic updates)

## Overview

This deployment plan covers the rollout of the manual score override feature, which includes Alpine.js integration updates, visual feedback elements, and backend scoring normalization changes.

## Pre-Deployment Checklist

### Code Review
- [ ] All Phase 1-6 changes reviewed
- [ ] No console errors in development
- [ ] ESLint/code quality checks pass
- [ ] Django template syntax validated

### Testing Complete
- [ ] Automated tests pass (pytest)
- [ ] Manual testing checklist completed
- [ ] Cross-browser testing verified
- [ ] Performance benchmarks acceptable

### Documentation
- [ ] User guide created (MANUAL_SCORE_OVERRIDE_USER_GUIDE.md)
- [ ] Technical documentation updated
- [ ] Change logs complete

## Deployment Steps

### 1. Staging Deployment (Day 1)

#### Morning (9:00 AM KST)
1. **Create deployment branch**
   ```bash
   git checkout -b deploy/manual-score-override
   git merge feature/manual-score-fixes
   ```

2. **Deploy to staging**
   ```bash
   git push staging deploy/manual-score-override:main
   ```

3. **Run migrations** (if any)
   ```bash
   heroku run python manage.py migrate --app=the5hc-staging
   ```

4. **Clear cache**
   ```bash
   heroku run python manage.py clear_cache --app=the5hc-staging
   ```

#### Afternoon (2:00 PM KST)
5. **Staging verification**
   - [ ] Create new assessment with manual scores
   - [ ] Edit existing assessment
   - [ ] Verify visual indicators work
   - [ ] Test reset functionality
   - [ ] Check score calculations
   - [ ] Verify PDF reports include manual scores

6. **Performance monitoring**
   - [ ] Check page load times
   - [ ] Monitor JavaScript errors
   - [ ] Verify no memory leaks

### 2. Production Deployment (Day 2)

#### Pre-deployment (8:00 AM KST)
1. **Backup database**
   ```bash
   heroku pg:backups:capture --app=the5hc
   ```

2. **Notify users** (via email/in-app notification)
   - Scheduled maintenance window
   - New feature announcement
   - Expected downtime: < 5 minutes

#### Deployment (10:00 AM KST)
3. **Deploy to production**
   ```bash
   git push production deploy/manual-score-override:main
   ```

4. **Run any migrations**
   ```bash
   heroku run python manage.py migrate --app=the5hc
   ```

5. **Clear production cache**
   ```bash
   heroku run python manage.py clear_cache --app=the5hc
   ```

6. **Static file collection** (if needed)
   ```bash
   heroku run python manage.py collectstatic --noinput --app=the5hc
   ```

### 3. Post-Deployment Verification

#### Immediate (10:15 AM KST)
- [ ] Site accessible
- [ ] Login working
- [ ] Create test assessment
- [ ] Verify manual score features
- [ ] Check existing assessments display correctly
- [ ] Monitor error logs

#### First Hour (11:00 AM KST)
- [ ] Review application metrics
- [ ] Check for JavaScript errors in Sentry/logs
- [ ] Monitor server performance
- [ ] Verify database query performance
- [ ] Test API endpoints

## Rollback Plan

If critical issues are discovered:

1. **Immediate rollback** (< 5 minutes)
   ```bash
   heroku releases:rollback --app=the5hc
   ```

2. **Restore database** (if needed)
   ```bash
   heroku pg:backups:restore --app=the5hc
   ```

3. **Clear cache**
   ```bash
   heroku run python manage.py clear_cache --app=the5hc
   ```

4. **Notify team**
   - Document issue
   - Plan fix
   - Reschedule deployment

## Monitoring Plan

### Day 1 Post-Deployment
- Monitor error rates hourly
- Check user feedback channels
- Review performance metrics
- Verify data integrity

### Week 1 Post-Deployment
- Daily error log review
- User adoption metrics
- Performance trends
- Feedback collection

### Success Criteria
- Error rate < 0.1%
- No performance degradation
- Positive user feedback
- All automated tests passing

## Communication Plan

### Internal Team
- [ ] Development team briefed
- [ ] Support team trained on new feature
- [ ] Documentation shared

### Users
- [ ] Feature announcement email sent
- [ ] In-app notification configured
- [ ] User guide accessible
- [ ] Support FAQ updated

## Feature Flags (Optional)

Consider implementing feature flag for gradual rollout:

```python
# settings.py
FEATURE_FLAGS = {
    'MANUAL_SCORE_OVERRIDE': {
        'enabled': True,
        'rollout_percentage': 100,  # Start with 10%, increase gradually
        'allowed_users': [],  # Specific user IDs for testing
    }
}
```

## Browser Cache Considerations

Due to JavaScript/CSS changes:

1. **Cache busting**
   - Update static file versions
   - Consider adding timestamp to static URLs

2. **User communication**
   - Include cache clearing instructions in announcement
   - Provide troubleshooting guide

## Risk Mitigation

### Identified Risks
1. **Browser caching issues**
   - Mitigation: Clear communication, cache busting
   
2. **Alpine.js compatibility**
   - Mitigation: Tested across browsers, fallback behavior

3. **Score calculation changes**
   - Mitigation: Comprehensive testing, data validation

4. **User confusion**
   - Mitigation: Clear documentation, training materials

## Post-Deployment Tasks

### Day 3
- [ ] Remove feature flag (if used)
- [ ] Archive deployment branch
- [ ] Update project documentation
- [ ] Schedule retrospective

### Week 2
- [ ] User training sessions
- [ ] Gather feedback
- [ ] Plan improvements
- [ ] Performance optimization

## Emergency Contacts

- **Lead Developer**: [Contact Info]
- **DevOps**: [Contact Info]
- **Product Owner**: [Contact Info]
- **Support Team**: [Contact Info]

## Deployment Log

| Timestamp | Action | Status | Notes |
|-----------|--------|--------|-------|
| YYYY-MM-DD HH:MM | Staging deployment started | ⏳ | |
| YYYY-MM-DD HH:MM | Staging verification complete | ✅ | |
| YYYY-MM-DD HH:MM | Production deployment started | ⏳ | |
| YYYY-MM-DD HH:MM | Production verification complete | ✅ | |

---

**Remember**: Take time, verify each step, and maintain clear communication throughout the deployment process.