# Task 042: Subscription Management - Test Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 042 |
| Task Name | Subscription Management Test Implementation |
| Task Type | test |
| Dependencies | None (or existing user/auth module) |
| Status | pending |

## Description
Implement comprehensive test suite for the subscription management module. This includes unit tests for subscription CRUD operations, keyword management, validation rules, and API endpoint integration tests. Tests cover subscription creation with keyword limits, update workflows, activation/deactivation logic, and user authorization checks.

## Files to Create/Modify

### Create Files
1. `tests/unit/models/test_subscription.py` - Unit tests for subscription model
2. `tests/unit/models/test_keyword.py` - Unit tests for keyword model
3. `tests/unit/services/test_subscription_service.py` - Unit tests for subscription service
4. `tests/integration/test_subscription_crud.py` - Integration tests for subscription CRUD
5. `tests/api/test_subscription_endpoints.py` - API endpoint tests
6. `tests/fixtures/subscription_fixtures.py` - Test fixtures for subscriptions

### Modify Files
1. `tests/conftest.py` - Add subscription test fixtures
2. `pytest.ini` - Add custom markers if needed

## Implementation Steps

### Step 1: Create Test Fixtures
1. Create user fixtures:
   - Regular user fixture
   - Premium user fixture (higher subscription limits)
   - Admin user fixture

2. Create subscription fixtures:
   - Active subscription with keywords
   - Inactive subscription
   - Subscription at keyword limit
   - Subscription with various notification channels

3. Create keyword fixtures:
   - Exact match keywords
   - Contains match keywords
   - Regex pattern keywords
   - Keywords with weights

4. Create test data generators:
   - Subscription factory function
   - Keyword factory function
   - Bulk subscription generator

### Step 2: Implement Model Unit Tests
1. Test `Subscription` model:
   - Create subscription with valid data
   - Validate required fields (name, user_id)
   - Test unique constraints
   - Test soft delete behavior
   - Test relationship to keywords (cascade)
   - Test relationship to user

2. Test `Keyword` model:
   - Create keyword with valid data
   - Validate match_type enum values
   - Test regex pattern validation
   - Test case_sensitive flag

3. Test `SubscriptionKeyword` association:
   - Create association with weight
   - Test required flag
   - Test cascade delete behavior

### Step 3: Implement Service Unit Tests
1. Test `SubscriptionService.create_subscription()`:
   - Create with valid data returns subscription
   - Create without name raises ValidationError
   - Create exceeds limit raises LimitExceededError
   - Create with initial keywords

2. Test `SubscriptionService.get_subscription()`:
   - Get existing subscription by ID
   - Get non-existing raises NotFoundError
   - Get with wrong user_id raises UnauthorizedError

3. Test `SubscriptionService.list_user_subscriptions()`:
   - List returns user's subscriptions
   - Pagination works correctly
   - Filter by status (active/inactive)
   - Filter by notification channel
   - Sort by created_at

4. Test `SubscriptionService.update_subscription()`:
   - Update name succeeds
   - Update description succeeds
   - Update notification channels succeeds
   - Cannot update non-owned subscription
   - Soft deleted subscription cannot be updated

5. Test `SubscriptionService.delete_subscription()`:
   - Delete performs soft delete
   - Delete removes associated keywords
   - Cannot delete non-owned subscription

6. Test `SubscriptionService.activate/deactivate_subscription()`:
   - Activate sets is_active=True
   - Deactivate sets is_active=False
   - Toggle twice returns to original state

7. Test keyword management methods:
   - `add_keywords()` adds keywords to subscription
   - `add_keywords()` enforces keyword limit
   - `remove_keywords()` removes keywords
   - `update_keyword()` updates keyword attributes
   - Duplicate keywords prevented

8. Test validation methods:
   - Subscription limit enforced per user
   - Keyword limit enforced per subscription
   - Invalid regex patterns rejected
   - Keyword length limits enforced

### Step 4: Implement Integration Tests
1. Test subscription CRUD flow:
   - Create -> Read -> Update -> Delete cycle
   - Verify database state at each step
   - Verify cascade operations

2. Test keyword management flow:
   - Create subscription without keywords
   - Add keywords via service
   - Verify association table entries
   - Remove keywords and verify cleanup

3. Test user isolation:
   - User A cannot access User B's subscriptions
   - Cross-user access returns 403
   - Admin can access all (if applicable)

4. Test concurrent operations:
   - Simultaneous creation under limit
   - Race condition handling for limits

### Step 5: Implement API Endpoint Tests
1. Test `POST /api/v1/subscriptions`:
   - Create with valid data returns 201
   - Create without auth returns 401
   - Create with invalid data returns 422
   - Create exceeding limit returns 403

2. Test `GET /api/v1/subscriptions`:
   - List returns 200 with pagination
   - List without auth returns 401
   - Pagination parameters work
   - Filter parameters work

3. Test `GET /api/v1/subscriptions/{id}`:
   - Get existing returns 200
   - Get non-existing returns 404
   - Get other's subscription returns 403

4. Test `PUT /api/v1/subscriptions/{id}`:
   - Update returns 200
   - Partial update works
   - Update other's returns 403
   - Update deleted returns 404

5. Test `DELETE /api/v1/subscriptions/{id}`:
   - Delete returns 204
   - Delete already deleted returns 404
   - Delete other's returns 403

6. Test `POST /api/v1/subscriptions/{id}/activate|deactivate`:
   - Activate/deactivate returns 200
   - Toggle twice restores original state

7. Test keyword endpoints:
   - POST /keywords returns 201
   - GET /keywords returns list
   - PUT /keywords/{id} updates
   - DELETE /keywords/{id} removes
   - Bulk operations work

8. Test error responses:
   - Proper error codes
   - Informative error messages
   - Validation error details

## Verification Steps

### Step 1: Run Unit Tests
```bash
pytest tests/unit/models/test_subscription.py -v --cov=models.subscription
pytest tests/unit/models/test_keyword.py -v --cov=models.keyword
pytest tests/unit/services/test_subscription_service.py -v --cov=services.subscription
```
- All unit tests should pass
- Coverage should be >= 85%

### Step 2: Run Integration Tests
```bash
pytest tests/integration/test_subscription_crud.py -v
```
- All integration tests should pass
- Database state verified

### Step 3: Run API Tests
```bash
pytest tests/api/test_subscription_endpoints.py -v
```
- All API tests should pass
- HTTP status codes correct

### Step 4: Coverage Report
```bash
pytest --cov=models.subscription --cov=services.subscription --cov=api.v1.endpoints.subscriptions --cov-report=html
```
- Overall coverage >= 85%
- All CRUD operations covered
- Edge cases covered

### Step 5: Test Limit Enforcement
```bash
# Create maximum allowed subscriptions
python -c "
from tests.fixtures.subscription_fixtures import create_max_subscriptions
create_max_subscriptions(user_id='test-user')
"
# Verify limit is enforced
```

## Git Commit Message
```
test: add subscription management test suite

- Add Subscription, Keyword, and SubscriptionKeyword model tests
- Add SubscriptionService tests for CRUD and keyword management
- Add API endpoint tests for all subscription routes
- Add integration tests for subscription CRUD workflows
- Test limit enforcement (subscriptions per user, keywords per subscription)
- Test user authorization and data isolation
- Test validation rules including regex pattern validation
- Achieve 87% code coverage

Refs: task-042
```
