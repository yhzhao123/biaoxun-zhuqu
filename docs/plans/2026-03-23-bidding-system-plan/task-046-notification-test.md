# Task 046: Notification Service - Test Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 046 |
| Task Name | Notification Service Test Implementation |
| Task Type | test |
| Dependencies | 045 (Keyword Matching Algorithm Implementation) |
| Status | pending |

## Description
Implement comprehensive test suite for the notification service including email notifications, in-app notifications, and Celery task processing. Tests cover notification template rendering, multi-channel delivery, rate limiting, retry logic, and Celery task queue management.

## Files to Create/Modify

### Create Files
1. `tests/unit/services/test_notification_service.py` - Unit tests for notification service
2. `tests/unit/services/test_email_service.py` - Unit tests for email service
3. `tests/unit/tasks/test_notification_tasks.py` - Unit tests for Celery notification tasks
4. `tests/unit/models/test_notification.py` - Unit tests for notification model
5. `tests/integration/test_notification_flow.py` - Integration tests for notification delivery
6. `tests/integration/test_celery_tasks.py` - Integration tests for Celery task processing
7. `tests/fixtures/notification_fixtures.py` - Test fixtures for notifications

### Modify Files
1. `tests/conftest.py` - Add notification fixtures
2. `pytest.ini` - Add Celery test configuration
3. `tests/__init__.py` - Configure Celery test app

## Implementation Steps

### Step 1: Create Test Fixtures
1. Create notification fixtures:
   - Pending notification objects
   - Sent notification objects
   - Failed notification objects
   - Different notification types (email, in_app, sms)

2. Create user preference fixtures:
   - Users with email enabled
   - Users with in-app only
   - Users with all channels disabled

3. Create bidding opportunity fixtures:
   - Matched opportunities with notification triggers
   - Opportunities with various match scores

4. Create email template fixtures:
   - Template with variables
   - Template with conditionals
   - Template with loops

### Step 2: Implement Notification Model Tests
1. Test `Notification` model:
   - Create notification with valid data
   - Validate required fields
   - Test status transitions (pending -> sent -> read)
   - Test soft delete behavior
   - Test notification type validation

2. Test `UserNotificationPreference` model:
   - Default preferences on user creation
   - Update preferences
   - Validate channel combinations

3. Test relationships:
   - Notification to user relationship
   - Notification to opportunity relationship
   - Notification to subscription relationship

### Step 3: Implement Email Service Tests
1. Test `EmailService` class:
   - `send_email()` with valid recipients
   - `send_template_email()` with template rendering
   - HTML and text email generation
   - Attachment handling
   - CC and BCC recipients

2. Test template rendering:
   - Variable substitution
   - Conditional blocks
   - Loop iteration
   - HTML escaping for security
   - Custom filters

3. Test email validation:
   - Valid email addresses accepted
   - Invalid email addresses rejected
   - Empty recipient list handling

4. Test email provider integration:
   - SMTP backend
   - SendGrid backend
   - AWS SES backend
   - Provider failover

### Step 4: Implement Notification Service Tests
1. Test `NotificationService` class:
   - `create_notification()` for matched opportunity
   - `send_notification()` delivery orchestration
   - `batch_send()` for multiple notifications
   - `mark_as_read()` status update
   - `get_user_notifications()` with pagination

2. Test channel selection logic:
   - Respect user preferences
   - Fallback channels
   - Skip disabled channels

3. Test rate limiting:
   - Per-user rate limits
   - Global rate limits
   - Rate limit reset

4. Test retry logic:
   - Retry on transient failures
   - Exponential backoff
   - Max retry limit
   - Dead letter queue on permanent failure

5. Test notification aggregation:
   - Batch similar notifications
   - Digest mode for daily summaries
   - Real-time vs batched delivery

### Step 5: Implement Celery Task Tests
1. Test `send_notification_task`:
   - Task execution with valid notification ID
   - Task failure handling
   - Retry on failure
   - Success callback

2. Test `process_match_results_task`:
   - Create notifications from match results
   - Group by user
   - Respect user preferences
   - Queue notification tasks

3. Test `send_digest_emails_task`:
   - Aggregate daily notifications
   - Generate digest content
   - Send to subscribed users

4. Test task chaining:
   - Match -> Create Notification -> Send flow
   - Error propagation in chain

5. Test Celery configuration:
   - Queue routing
   - Priority levels
   - Task timeouts

### Step 6: Implement Integration Tests
1. Test end-to-end notification flow:
   - Bidding opportunity created
   - Matching algorithm runs
   - Notifications created and queued
   - Celery task processes queue
   - Email sent via provider
   - In-app notification created

2. Test failure scenarios:
   - Email provider unavailable
   - Database connection lost
   - Celery worker down
   - Recovery and retry

3. Test with multiple users:
   - Concurrent notification processing
   - No cross-user data leakage
   - Rate limiting per user

## Verification Steps

### Step 1: Run Unit Tests
```bash
pytest tests/unit/models/test_notification.py -v --cov=models.notification
pytest tests/unit/services/test_email_service.py -v --cov=services.email
pytest tests/unit/services/test_notification_service.py -v --cov=services.notification
pytest tests/unit/tasks/test_notification_tasks.py -v --cov=tasks.notification
```
- All unit tests should pass
- Coverage should be >= 80%

### Step 2: Run Integration Tests
```bash
pytest tests/integration/test_notification_flow.py -v
pytest tests/integration/test_celery_tasks.py -v
```
- All integration tests should pass
- End-to-end flow verified

### Step 3: Run with Celery Worker
```bash
# Start test Celery worker
celery -A tasks.worker worker --loglevel=info --queues=notifications

# Run tests
pytest tests/integration/test_celery_tasks.py -v
```

### Step 4: Coverage Report
```bash
pytest --cov=services.notification --cov=services.email --cov=tasks.notification --cov-report=html
```
- Overall coverage >= 80%
- All notification channels covered
- Celery task paths covered

### Step 5: Email Template Testing
```bash
# Test template rendering
python -c "from services.email import EmailService; s = EmailService(); s.test_templates()"
```
- All templates render without errors
- Variables substituted correctly
- HTML output is valid

## Git Commit Message
```
test: add notification service test suite

- Add Notification and UserNotificationPreference model tests
- Add EmailService tests for template rendering and delivery
- Add NotificationService tests for multi-channel delivery
- Add Celery task tests for async processing
- Add integration tests for end-to-end notification flow
- Test rate limiting, retry logic, and failure handling
- Test email template security (XSS prevention)
- Achieve 82% code coverage

Refs: task-046
```
