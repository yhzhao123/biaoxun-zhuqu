# Task 047: Notification Service - Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 047 |
| Task Name | Notification Service Implementation |
| Task Type | impl |
| Dependencies | 046 (Notification Service Test Implementation) |
| Status | pending |

## Description
Implement the notification service for the bidding system including email notifications, in-app notifications, and Celery task processing. This service delivers bidding opportunity alerts to users through their preferred channels based on matching subscription keywords. Supports template-based emails, rate limiting, retry logic, and digest mode.

## Files to Create/Modify

### Create Files
1. `models/notification.py` - Notification and preference models
2. `services/notification_service.py` - Core notification service
3. `services/email_service.py` - Email delivery service
4. `tasks/notification_tasks.py` - Celery tasks for notifications
5. `templates/emails/` - Email template directory
   - `bid_alert.html` - Bidding opportunity alert template
   - `daily_digest.html` - Daily summary template
   - `welcome.html` - Welcome email template
6. `core/notification_config.py` - Notification configuration
7. `migrations/versions/004_add_notification_tables.py` - Database migration

### Modify Files
1. `models/__init__.py` - Export notification models
2. `services/__init__.py` - Export notification services
3. `tasks/__init__.py` - Register notification tasks
4. `core/config.py` - Add notification settings
5. `services/matching_service.py` - Integrate notification trigger

## Implementation Steps

### Step 1: Database Models
1. Create `Notification` model:
   - id (UUID, primary key)
   - user_id (UUID, foreign key)
   - subscription_id (UUID, foreign key, optional)
   - opportunity_id (UUID, foreign key)
   - type (enum: email, in_app, sms, push)
   - status (enum: pending, sent, delivered, read, failed)
   - subject (str, for email)
   - content (text)
   - metadata (JSON: match score, matched keywords)
   - sent_at, delivered_at, read_at (timestamps)
   - created_at, updated_at (timestamps)
   - retry_count (int, default 0)
   - error_message (text, optional)

2. Create `UserNotificationPreference` model:
   - user_id (UUID, primary key, foreign key)
   - email_enabled (boolean, default True)
   - in_app_enabled (boolean, default True)
   - sms_enabled (boolean, default False)
   - push_enabled (boolean, default False)
   - digest_mode (enum: realtime, hourly, daily)
   - digest_time (time, for daily digests)
   - quiet_hours_start, quiet_hours_end (time, optional)

3. Create `NotificationTemplate` model (optional, for dynamic templates):
   - id (UUID, primary key)
   - name (str, unique)
   - type (enum: email, sms, push)
   - subject_template (str)
   - body_template (str)
   - html_template (str)
   - is_active (boolean)

### Step 2: Email Service
1. Create `EmailService` class:
   - `send_email(to, subject, body, html=None, cc=None, bcc=None, attachments=None)`
   - `send_template_email(to, template_name, context, **kwargs)`
   - `render_template(template_name, context)` - Jinja2 templating

2. Implement email backends:
   - SMTP backend for development/testing
   - SendGrid backend for production
   - AWS SES backend (optional)
   - Console backend for debugging

3. Implement template system:
   - Jinja2 template engine
   - HTML email templates with CSS
   - Plain text fallback generation
   - Template inheritance
   - Custom filters (date formatting, currency)

4. Add email validation:
   - Recipient email format validation
   - Domain validation
   - Bounce handling

### Step 3: Notification Service
1. Create `NotificationService` class:
   - `create_notification(user_id, opportunity_id, subscription_id, match_result)`
   - `send_notification(notification_id)` - Send via preferred channels
   - `send_batch_notifications(notification_ids)` - Batch processing
   - `mark_as_read(notification_id)` - Update status
   - `mark_all_as_read(user_id)` - Bulk update
   - `get_user_notifications(user_id, filters, pagination)` - List with filters
   - `get_unread_count(user_id)` - Unread notification count

2. Implement channel selection:
   - Check user preferences
   - Skip quiet hours
   - Respect digest mode settings
   - Channel fallback logic

3. Implement rate limiting:
   - Per-user notification limits
   - Per-subscription limits
   - Global rate limiting
   - Rate limit storage (Redis/cache)

4. Implement retry logic:
   - Exponential backoff (2^n seconds)
   - Max retry attempts (default: 3)
   - Dead letter queue for permanent failures
   - Retry status tracking

5. Implement notification aggregation:
   - Group similar notifications
   - Digest generation for daily summaries
   - Real-time vs batched queue selection

### Step 4: Celery Tasks
1. Create `tasks/notification_tasks.py`:
   - `send_notification_task(notification_id)` - Send single notification
   - `process_match_results_task(match_results)` - Create notifications from matches
   - `send_digest_emails_task()` - Scheduled daily digest
   - `cleanup_old_notifications_task()` - Archive old notifications

2. Implement task configuration:
   - Queue routing (notifications queue)
   - Task priorities (high for real-time, low for digest)
   - Task timeouts and retry policies
   - Error callbacks

3. Implement task chaining:
   - Match -> Create Notification -> Send
   - Batch processing chains

4. Implement scheduled tasks:
   - Daily digest at configured time
   - Weekly cleanup job
   - Retry failed notifications

### Step 5: Email Templates
1. Create `templates/emails/base.html`:
   - Base layout with header/footer
   - Responsive CSS styling
   - Company branding

2. Create `templates/emails/bid_alert.html`:
   - Bidding opportunity details
   - Match score display
   - Matched keywords highlight
   - CTA button to view details
   - Unsubscribe link

3. Create `templates/emails/bid_alert.txt`:
   - Plain text version
   - Same content as HTML

4. Create `templates/emails/daily_digest.html`:
   - Summary of multiple opportunities
   - Grouped by subscription
   - Statistics (total matches, new since last)

5. Create `templates/emails/welcome.html`:
   - Welcome message for new users
   - Quick start guide
   - Subscription setup CTA

### Step 6: Integration with Matching Service
1. Modify `MatchingService` to trigger notifications:
   - After matching completes successfully
   - Create notifications for high-scoring matches
   - Queue notification tasks

2. Implement webhook support (optional):
   - External notification endpoints
   - Custom payload formatting

### Step 7: Database Migration
1. Create migration for notification tables
2. Add indexes:
   - notifications.user_id
   - notifications.status
   - notifications.created_at
   - notifications.opportunity_id
3. Add foreign key constraints
4. Set up cascade deletes

### Step 8: Configuration
1. Add to `core/config.py`:
   - `NOTIFICATION_EMAIL_BACKEND` (smtp, sendgrid, ses)
   - `NOTIFICATION_RATE_LIMIT_PER_USER` (default: 100/hour)
   - `NOTIFICATION_MAX_RETRIES` (default: 3)
   - `NOTIFICATION_RETRY_BACKOFF` (default: 2)
   - `NOTIFICATION_DIGEST_TIME` (default: "09:00")
   - `NOTIFICATION_RETENTION_DAYS` (default: 90)
   - SendGrid/AWS credentials
   - SMTP settings

## Verification Steps

### Step 1: Run Tests
```bash
pytest tests/unit/models/test_notification.py -v
pytest tests/unit/services/test_email_service.py -v
pytest tests/unit/services/test_notification_service.py -v
pytest tests/unit/tasks/test_notification_tasks.py -v
pytest tests/integration/test_notification_flow.py -v
```
- All tests should pass

### Step 2: Manual Email Testing
```bash
# Test email template rendering
python -c "
from services.email_service import EmailService
es = EmailService()
html = es.render_template('bid_alert', {
    'user_name': 'Test User',
    'opportunity_title': 'Construction Project',
    'match_score': 0.95,
    'matched_keywords': ['construction', 'building']
})
print(html)
"

# Test email sending (if SMTP configured)
python -c "
from services.email_service import EmailService
es = EmailService()
es.send_email(
    to=['test@example.com'],
    subject='Test Notification',
    body='This is a test.',
    html='<h1>Test</h1>'
)
"
```

### Step 3: Celery Task Testing
```bash
# Start Celery worker
celery -A tasks.worker worker --loglevel=info --queues=notifications

# Trigger test task
python -c "
from tasks.notification_tasks import send_notification_task
send_notification_task.delay('test-notification-id')
"
```

### Step 4: Database Verification
```sql
-- Verify tables created
SELECT * FROM notifications LIMIT 1;
SELECT * FROM user_notification_preferences LIMIT 1;

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename IN ('notifications');
```

### Step 5: API Endpoints Testing
```bash
# Get user notifications
curl http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer $TOKEN"

# Mark as read
curl -X POST http://localhost:8000/api/v1/notifications/{id}/read \
  -H "Authorization: Bearer $TOKEN"

# Update preferences
curl -X PUT http://localhost:8000/api/v1/users/me/notification-preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email_enabled": true, "digest_mode": "daily"}'
```

### Step 6: Code Quality
```bash
mypy services/notification_service.py services/email_service.py tasks/notification_tasks.py
pylint services/notification_service.py services/email_service.py
black --check services/notification_service.py services/email_service.py tasks/
```
- No type errors
- No linting errors
- Code formatted

## Git Commit Message
```
feat: implement notification service with multi-channel support

- Add Notification and UserNotificationPreference models
- Implement EmailService with SMTP/SendGrid backends
- Create NotificationService with rate limiting and retry logic
- Add Celery tasks for async notification processing
- Create HTML/text email templates for bid alerts and digests
- Support email, in-app, SMS, and push notification channels
- Implement digest mode and quiet hours
- Add scheduled tasks for daily digests and cleanup
- Integrate notification trigger with matching service

Refs: task-047
```
