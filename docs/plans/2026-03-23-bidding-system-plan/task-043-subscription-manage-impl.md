# Task 043: Subscription Management - Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 043 |
| Task Name | Subscription Management Implementation |
| Task Type | impl |
| Dependencies | 042 (Subscription Management Test Implementation) |
| Status | pending |

## Description
Implement the subscription management module including user subscription CRUD operations and keyword management. This module allows users to create subscription rules with associated keywords for bidding opportunity notifications. Each user can manage multiple subscriptions with configurable parameters including notification channels, frequency, and keyword matching rules.

## Files to Create/Modify

### Create Files
1. `models/subscription.py` - Subscription model with SQLAlchemy
2. `models/keyword.py` - Keyword model with match type support
3. `models/subscription_keyword.py` - Association table model
4. `services/subscription_service.py` - Business logic for subscription operations
5. `schemas/subscription.py` - Pydantic schemas for validation/serialization
6. `schemas/keyword.py` - Pydantic schemas for keyword operations
7. `api/v1/endpoints/subscriptions.py` - REST API endpoints
8. `migrations/versions/003_add_subscription_tables.py` - Database migration

### Modify Files
1. `models/__init__.py` - Export new models
2. `services/__init__.py` - Export subscription service
3. `schemas/__init__.py` - Export new schemas
4. `api/v1/router.py` - Register subscription endpoints
5. `core/config.py` - Add subscription limits config

## Implementation Steps

### Step 1: Database Models
1. Create `Subscription` model with fields:
   - id (UUID, primary key)
   - user_id (UUID, foreign key)
   - name (str, max 100 chars)
   - description (text, optional)
   - notification_channels (JSON: email, sms, in_app)
   - frequency (enum: realtime, hourly, daily)
   - is_active (boolean)
   - max_keywords (int, default 50)
   - created_at, updated_at, deleted_at (timestamps)

2. Create `Keyword` model with fields:
   - id (UUID, primary key)
   - value (str, max 200 chars, indexed)
   - match_type (enum: exact, contains, starts_with, ends_with, regex)
   - case_sensitive (boolean, default False)
   - created_at, updated_at (timestamps)

3. Create `SubscriptionKeyword` association table:
   - subscription_id (UUID, foreign key)
   - keyword_id (UUID, foreign key)
   - is_required (boolean, default False)
   - weight (float, default 1.0)
   - Composite primary key on (subscription_id, keyword_id)

### Step 2: Service Layer
1. Implement `SubscriptionService` class with methods:
   - `create_subscription(user_id, subscription_data)` - Create new subscription
   - `get_subscription(subscription_id, user_id)` - Get single subscription
   - `list_user_subscriptions(user_id, filters, pagination)` - List with filtering
   - `update_subscription(subscription_id, user_id, update_data)` - Update
   - `delete_subscription(subscription_id, user_id)` - Soft delete
   - `activate_subscription(subscription_id, user_id)` - Activate
   - `deactivate_subscription(subscription_id, user_id)` - Deactivate

2. Implement keyword management methods:
   - `add_keywords(subscription_id, user_id, keywords_data)` - Bulk add
   - `remove_keywords(subscription_id, user_id, keyword_ids)` - Bulk remove
   - `update_keyword(subscription_id, user_id, keyword_id, update_data)` - Update
   - `get_subscription_keywords(subscription_id, user_id)` - List keywords

3. Implement validation logic:
   - Check subscription limit per user (configurable)
   - Validate keyword count per subscription
   - Validate regex patterns for keyword match_type
   - Prevent duplicate keywords per subscription

### Step 3: Pydantic Schemas
1. Create request/response schemas:
   - `SubscriptionCreate` - Create request validation
   - `SubscriptionUpdate` - Update request validation
   - `SubscriptionResponse` - Response serialization
   - `SubscriptionListResponse` - Paginated list response
   - `KeywordCreate` - Keyword creation schema
   - `KeywordUpdate` - Keyword update schema
   - `KeywordResponse` - Keyword response schema
   - `BulkKeywordRequest` - Bulk operations schema

2. Add validation rules:
   - Name length: 1-100 characters
   - Description max: 1000 characters
   - Keywords per subscription: max 50
   - Keyword value length: 1-200 characters

### Step 4: API Endpoints
1. Implement endpoints in `subscriptions.py`:
   - `POST /api/v1/subscriptions` - Create subscription
   - `GET /api/v1/subscriptions` - List subscriptions
   - `GET /api/v1/subscriptions/{subscription_id}` - Get details
   - `PUT /api/v1/subscriptions/{subscription_id}` - Update
   - `DELETE /api/v1/subscriptions/{subscription_id}` - Delete
   - `POST /api/v1/subscriptions/{subscription_id}/activate` - Activate
   - `POST /api/v1/subscriptions/{subscription_id}/deactivate` - Deactivate
   - `POST /api/v1/subscriptions/{subscription_id}/keywords` - Add keywords
   - `GET /api/v1/subscriptions/{subscription_id}/keywords` - List keywords
   - `PUT /api/v1/subscriptions/{subscription_id}/keywords/{keyword_id}` - Update keyword
   - `DELETE /api/v1/subscriptions/{subscription_id}/keywords/{keyword_id}` - Remove keyword

2. Add authentication middleware to all endpoints
3. Add authorization checks (user owns subscription)
4. Implement proper HTTP status codes and error responses

### Step 5: Database Migration
1. Create migration script for new tables
2. Add indexes on frequently queried columns:
   - subscriptions.user_id
   - subscriptions.is_active
   - keywords.value
   - subscription_keywords.subscription_id
3. Test migration rollback

### Step 6: Configuration
1. Add to `core/config.py`:
   - `SUBSCRIPTION_MAX_PER_USER` (default: 10)
   - `SUBSCRIPTION_MAX_KEYWORDS` (default: 50)
   - `SUBSCRIPTION_KEYWORD_MAX_LENGTH` (default: 200)

## Verification Steps

### Step 1: Run Tests
```bash
pytest tests/unit/models/test_subscription.py -v
pytest tests/unit/services/test_subscription_service.py -v
pytest tests/integration/test_subscription_crud.py -v
pytest tests/api/test_subscription_endpoints.py -v
```
- All tests should pass

### Step 2: Manual API Testing
```bash
# Create subscription
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Construction Bids", "notification_channels": {"email": true}}'

# Add keywords
curl -X POST http://localhost:8000/api/v1/subscriptions/{id}/keywords \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keywords": [{"value": "construction", "match_type": "contains"}]}'

# List subscriptions
curl http://localhost:8000/api/v1/subscriptions \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Database Verification
```sql
-- Verify tables created
SELECT * FROM subscriptions LIMIT 1;
SELECT * FROM keywords LIMIT 1;
SELECT * FROM subscription_keywords LIMIT 1;

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename IN ('subscriptions', 'keywords');
```

### Step 4: Code Quality
```bash
mypy services/subscription_service.py
mypy api/v1/endpoints/subscriptions.py
pylint services/subscription_service.py
black --check models/subscription.py services/subscription_service.py
```
- No type errors
- No linting errors
- Code formatted with black

### Step 5: Documentation
- Update API documentation (OpenAPI/Swagger)
- Verify all endpoints documented
- Include example requests/responses

## Git Commit Message
```
feat: implement subscription management module

- Add Subscription, Keyword, and SubscriptionKeyword models
- Implement subscription CRUD service with validation
- Add keyword management (add/remove/update/bulk operations)
- Create REST API endpoints with auth and authz
- Add database migration with indexes
- Enforce subscription and keyword limits
- Support multiple notification channels and match types

Refs: task-043
```
