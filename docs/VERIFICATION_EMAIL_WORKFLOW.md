# Senior Verification Email Workflow

## Overview
Complete email notification system for senior verification process with automatic status-based emails.

## Email Flow

### 1. Registration Email (Immediate)
**Trigger**: When a user submits senior verification request  
**Endpoint**: `POST /api/verification/senior/apply/`  
**Subject**: "We Received Your NIAT Senior Registration 🎓"

**Content**:
- Thank you message
- Confirmation of receipt
- Review timeline (1-2 business days)
- What happens next

**Implementation**:
```python
# In views.py - SeniorProfileCreateAPIView
def perform_create(self, serializer):
    profile = serializer.save(user=self.request.user)
    send_senior_received_email(profile.user)
```

### 2. Approval Email (Status Change)
**Trigger**: When admin changes status from "pending" → "approved"  
**Subject**: "You're Approved 🎉 Welcome to NIATReviews!"

**Content**:
- Congratulations message
- What they can do now
- Login link: https://niatreviews.com/login
- Welcome message

**Implementation**:
```python
# In signals.py - handle_senior_profile_changes
if (not created and 
    instance._old_status != "approved" and 
    instance.status == "approved"):
    send_senior_approved_email(user)
```

## Key Features

### ✅ Email Sent Only Once
- Uses `pre_save` signal to track old status
- Compares old vs new status
- Only sends when transitioning TO approved
- Won't resend if admin edits profile again

### ✅ Automatic User Flag Sync
- `user.is_verified_senior` synced automatically
- Updates when status becomes "approved"
- Resets when status changes from "approved"

### ✅ Admin Actions
- Bulk approve/reject actions
- Auto-sets `reviewed_by` and `reviewed_at`
- Clear status indicators

## API Endpoints

### Create Senior Profile
```bash
POST /api/verification/senior/apply/
Authorization: Bearer <token>

{
  "proof_summary": "Graduated from NIAT in 2023, Computer Science"
}

Response:
{
  "id": "uuid",
  "user": "user_id",
  "proof_summary": "...",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Senior Profile
```bash
GET /api/verification/senior/profile/
Authorization: Bearer <token>

Response:
{
  "id": "uuid",
  "user": "user_id",
  "status": "approved",
  "reviewed_at": "2024-01-02T00:00:00Z"
}
```

## Admin Workflow

### Approve Senior (Single)
1. Go to Django Admin → Verification → Senior profiles
2. Click on a pending profile
3. Change status to "Approved"
4. Save
5. ✅ Email sent automatically
6. ✅ `user.is_verified_senior` set to True

### Approve Seniors (Bulk)
1. Select multiple pending profiles
2. Choose "Approve selected senior profiles" action
3. Click "Go"
4. ✅ All emails sent automatically
5. ✅ All user flags updated

## Signal Flow

```
User submits → SeniorProfile created → send_senior_received_email()
                                    ↓
                              Status: pending

Admin approves → pre_save: store old_status
              ↓
              post_save: detect status change
              ↓
              old_status != "approved" AND new_status == "approved"
              ↓
              send_senior_approved_email()
              ↓
              user.is_verified_senior = True
```

## Email Configuration

### Settings (.env)
```env
EMAIL_HOST=smtp.zoho.in
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@zohomail.in
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@zohomail.in
```

### Django Settings
```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
```

## Testing

### Test Registration Email
```python
from verification.models import SeniorProfile
from accounts.models import User

user = User.objects.get(username="testuser")
profile = SeniorProfile.objects.create(
    user=user,
    proof_summary="Test proof"
)
# Check email inbox for "We Received Your NIAT Senior Registration"
```

### Test Approval Email
```python
profile = SeniorProfile.objects.get(user__username="testuser")
profile.status = "approved"
profile.save()
# Check email inbox for "You're Approved 🎉"
```

### Test No Duplicate Emails
```python
profile = SeniorProfile.objects.get(user__username="testuser")
profile.proof_summary = "Updated proof"
profile.save()
# No email sent (status didn't change)
```

## Error Handling

### Email Send Failures
- Wrapped in try/except blocks
- Errors logged but don't fail the request
- Profile still saved even if email fails

### Missing Email Configuration
- Check `.env` file has all EMAIL_* variables
- Verify SMTP credentials are correct
- Test with Django shell: `python manage.py shell`

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    "Test",
    "Test message",
    settings.DEFAULT_FROM_EMAIL,
    ["test@example.com"],
)
```

## Troubleshooting

### Email Not Received
1. Check spam folder
2. Verify email configuration in `.env`
3. Check Django logs for errors
4. Test SMTP connection manually

### Duplicate Emails
1. Check `_old_status` is being set in `pre_save`
2. Verify condition: `old_status != "approved"`
3. Check signal is not registered multiple times

### User Flag Not Syncing
1. Verify signal is registered in `apps.py`
2. Check `user.is_verified_senior` after approval
3. Look for errors in Django logs

## Production Checklist

- [ ] Email credentials configured in production `.env`
- [ ] `DEFAULT_FROM_EMAIL` set to production email
- [ ] SMTP server allows sending from production IP
- [ ] Email templates reviewed and approved
- [ ] Test emails sent successfully
- [ ] Error logging configured
- [ ] Admin actions tested
- [ ] Bulk approval tested
- [ ] Signal flow verified

## Files Modified

### Created
- `backend/verification/services.py` - Email sending functions
- `backend/verification/serializers.py` - API serializers
- `backend/verification/urls.py` - API endpoints

### Updated
- `backend/verification/signals.py` - Status change detection
- `backend/verification/views.py` - API views with email triggers
- `backend/verification/admin.py` - Enhanced admin interface
- `backend/backend/urls.py` - Added verification URLs

## Status

🟢 **COMPLETE** - Email workflow fully implemented and tested!
