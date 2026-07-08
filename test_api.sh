#!/bin/bash

# =============================================================================
# AUTOMATED API TESTING SCRIPT
# =============================================================================

API_BASE_URL="http://127.0.0.1:8000/api"
USER_ID="test_user_$(date +%s)"
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

echo "🚀 Starting API Tests..."
echo "📊 User ID: $USER_ID"
echo "⏰ Timestamp: $TIMESTAMP"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: $2"
  else
    echo -e "${RED}❌ FAIL${NC}: $2"
  fi
}

PASSED=0
FAILED=0

# =============================================================================
# TEST 1: Health Check
# =============================================================================
echo -e "\n${YELLOW}TEST 1: Health Check${NC}"
RESPONSE=$(curl -s -X GET "$API_BASE_URL/health")
if echo "$RESPONSE" | grep -q "healthy"; then
  test_result 0 "Health check passed"
  ((PASSED++))
else
  test_result 1 "Health check failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 2: Create Goal
# =============================================================================
echo -e "\n${YELLOW}TEST 2: Create Goal${NC}"
GOAL_RESPONSE=$(curl -s -X POST "$API_BASE_URL/goals" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"goal_name\": \"Test Emergency Fund\",
    \"goal_type\": \"long_term\",
    \"target_amount\": 50000,
    \"deadline\": \"2027-12-31T00:00:00\",
    \"priority\": \"high\",
    \"description\": \"Test goal\"
  }")

GOAL_ID=$(echo "$GOAL_RESPONSE" | grep -o '"goal_id":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$GOAL_ID" ]; then
  test_result 0 "Goal created: $GOAL_ID"
  ((PASSED++))
else
  test_result 1 "Failed to create goal"
  echo "Response: $GOAL_RESPONSE"
  ((FAILED++))
  GOAL_ID="error"
fi

# =============================================================================
# TEST 3: Get All Goals
# =============================================================================
echo -e "\n${YELLOW}TEST 3: Get All Goals${NC}"
GOALS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/goals/$USER_ID")
if echo "$GOALS_RESPONSE" | grep -q "total_goals"; then
  test_result 0 "Get all goals passed"
  ((PASSED++))
else
  test_result 1 "Get all goals failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 4: Add Progress to Goal
# =============================================================================
if [ "$GOAL_ID" != "error" ]; then
  echo -e "\n${YELLOW}TEST 4: Add Progress to Goal${NC}"
  PROGRESS_RESPONSE=$(curl -s -X POST "$API_BASE_URL/goals/$GOAL_ID/add-progress" \
    -H "Content-Type: application/json" \
    -d '{"amount": 10000}')
  
  if echo "$PROGRESS_RESPONSE" | grep -q "success"; then
    test_result 0 "Progress added to goal"
    ((PASSED++))
  else
    test_result 1 "Failed to add progress"
    ((FAILED++))
  fi
fi

# =============================================================================
# TEST 5: Create Budget
# =============================================================================
echo -e "\n${YELLOW}TEST 5: Create Budget${NC}"
BUDGET_RESPONSE=$(curl -s -X POST "$API_BASE_URL/budgets" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"category\": \"Food\",
    \"monthly_limit\": 15000,
    \"month\": \"2026-07\"
  }")

BUDGET_ID=$(echo "$BUDGET_RESPONSE" | grep -o '"budget_id":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$BUDGET_ID" ]; then
  test_result 0 "Budget created: $BUDGET_ID"
  ((PASSED++))
else
  test_result 1 "Failed to create budget"
  ((FAILED++))
  BUDGET_ID="error"
fi

# =============================================================================
# TEST 6: Get Budgets for Month
# =============================================================================
echo -e "\n${YELLOW}TEST 6: Get Budgets for Month${NC}"
BUDGETS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/budgets/$USER_ID/2026-07")
if echo "$BUDGETS_RESPONSE" | grep -q "total_limit"; then
  test_result 0 "Get budgets passed"
  ((PASSED++))
else
  test_result 1 "Get budgets failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 7: Add Spending to Budget
# =============================================================================
if [ "$BUDGET_ID" != "error" ]; then
  echo -e "\n${YELLOW}TEST 7: Add Spending to Budget${NC}"
  SPENDING_RESPONSE=$(curl -s -X POST "$API_BASE_URL/budgets/$BUDGET_ID/add-spending" \
    -H "Content-Type: application/json" \
    -d '{"amount": 5000}')
  
  if echo "$SPENDING_RESPONSE" | grep -q "success"; then
    test_result 0 "Spending added to budget"
    ((PASSED++))
  else
    test_result 1 "Failed to add spending"
    ((FAILED++))
  fi
fi

# =============================================================================
# TEST 8: Check Budget Alerts
# =============================================================================
echo -e "\n${YELLOW}TEST 8: Check Budget Alerts${NC}"
ALERTS_RESPONSE=$(curl -s -X POST "$API_BASE_URL/budgets/check-alerts" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"month\": \"2026-07\"}")

if echo "$ALERTS_RESPONSE" | grep -q "warnings\|critical"; then
  test_result 0 "Check alerts passed"
  ((PASSED++))
else
  test_result 1 "Check alerts failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 9: GoalPlanner Agent Analysis
# =============================================================================
echo -e "\n${YELLOW}TEST 9: GoalPlanner Agent Analysis${NC}"
ANALYSIS_RESPONSE=$(curl -s -X POST "$API_BASE_URL/goals/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"monthly_income\": 100000}")

if echo "$ANALYSIS_RESPONSE" | grep -q "analyzed"; then
  test_result 0 "GoalPlanner agent analysis passed"
  ((PASSED++))
else
  test_result 1 "GoalPlanner agent analysis failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 10: BudgetMonitor Agent Monitoring
# =============================================================================
echo -e "\n${YELLOW}TEST 10: BudgetMonitor Agent Monitoring${NC}"
MONITOR_RESPONSE=$(curl -s -X POST "$API_BASE_URL/budgets/monitor" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"month\": \"2026-07\"}")

if echo "$MONITOR_RESPONSE" | grep -q "monitored"; then
  test_result 0 "BudgetMonitor agent monitoring passed"
  ((PASSED++))
else
  test_result 1 "BudgetMonitor agent monitoring failed"
  ((FAILED++))
fi

# =============================================================================
# TEST 11: Update Goal
# =============================================================================
if [ "$GOAL_ID" != "error" ]; then
  echo -e "\n${YELLOW}TEST 11: Update Goal${NC}"
  UPDATE_RESPONSE=$(curl -s -X PUT "$API_BASE_URL/goals/$GOAL_ID" \
    -H "Content-Type: application/json" \
    -d '{"priority": "medium"}')
  
  if echo "$UPDATE_RESPONSE" | grep -q "priority"; then
    test_result 0 "Goal updated"
    ((PASSED++))
  else
    test_result 1 "Failed to update goal"
    ((FAILED++))
  fi
fi

# =============================================================================
# TEST 12: Delete Budget
# =============================================================================
if [ "$BUDGET_ID" != "error" ]; then
  echo -e "\n${YELLOW}TEST 12: Delete Budget${NC}"
  DELETE_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/budgets/$BUDGET_ID")
  
  if echo "$DELETE_RESPONSE" | grep -q "deleted"; then
    test_result 0 "Budget deleted"
    ((PASSED++))
  else
    test_result 1 "Failed to delete budget"
    ((FAILED++))
  fi
fi

# =============================================================================
# TEST 13: Delete Goal
# =============================================================================
if [ "$GOAL_ID" != "error" ]; then
  echo -e "\n${YELLOW}TEST 13: Delete Goal${NC}"
  DELETE_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/goals/$GOAL_ID")
  
  if echo "$DELETE_RESPONSE" | grep -q "deleted"; then
    test_result 0 "Goal deleted"
    ((PASSED++))
  else
    test_result 1 "Failed to delete goal"
    ((FAILED++))
  fi
fi

# =============================================================================
# FINAL RESULTS
# =============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ PASSED: $PASSED${NC}"
echo -e "${RED}❌ FAILED: $FAILED${NC}"
TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))
echo "📊 Total: $TOTAL tests"
echo "📈 Success Rate: $PERCENTAGE%"
echo "═══════════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
  exit 0
else
  echo -e "${RED}⚠️  SOME TESTS FAILED!${NC}"
  exit 1
fi
