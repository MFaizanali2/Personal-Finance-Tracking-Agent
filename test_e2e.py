import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed):
    status = f"{Colors.GREEN}[PASS]{Colors.END}" if passed else f"{Colors.RED}[FAIL]{Colors.END}"
    print(f"{status}: {name}")

def print_section(name):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}{name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

class E2ETests:
    def __init__(self):
        self.user_id = f"test_user_{datetime.now().timestamp()}"
        self.passed = 0
        self.failed = 0
        self.goal_id = None
        self.budget_id = None

    def run_all(self):
        print(f"\n{Colors.BLUE}==> Starting E2E Tests{Colors.END}")
        print(f"==> User ID: {self.user_id}")
        
        self.test_health_check()
        self.test_goal_workflow()
        self.test_budget_workflow()
        self.test_agent_integration()
        self.test_error_handling()
        self.test_cleanup()
        
        self.print_summary()

    def test_health_check(self):
        print_section("TEST 1: Health Check")
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            passed = response.status_code == 200 and "healthy" in response.text
            print_test("API Health Check", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("API Health Check", False)
            print(f"  Error: {str(e)}")
            self.failed += 1

    def test_goal_workflow(self):
        print_section("TEST 2: Goal Workflow (Create / Read / Update / Delete)")
        
        goal_data = {
            "user_id": self.user_id,
            "goal_name": "Test Emergency Fund",
            "goal_type": "long_term",
            "target_amount": 50000,
            "deadline": (datetime.now() + timedelta(days=365)).isoformat(),
            "priority": "high",
            "description": "E2E Test Goal"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/goals", json=goal_data)
            if response.status_code == 201:
                self.goal_id = response.json().get("goal_id")
                print_test("Create Goal", True)
                self.passed += 1
            else:
                print_test("Create Goal", False)
                self.failed += 1
                return
        except Exception as e:
            print_test("Create Goal", False)
            print(f"  Error: {str(e)}")
            self.failed += 1
            return

        try:
            response = requests.get(f"{API_BASE_URL}/goals/{self.user_id}")
            passed = response.status_code == 200 and "goals" in response.text
            print_test("Get All Goals", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Get All Goals", False)
            self.failed += 1

        try:
            response = requests.post(
                f"{API_BASE_URL}/goals/{self.goal_id}/add-progress",
                json={"amount": 10000}
            )
            passed = response.status_code == 200 and "success" in response.text
            print_test("Add Progress to Goal", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Add Progress to Goal", False)
            self.failed += 1

        try:
            response = requests.put(
                f"{API_BASE_URL}/goals/{self.goal_id}",
                json={"priority": "medium"}
            )
            passed = response.status_code == 200
            print_test("Update Goal", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Update Goal", False)
            self.failed += 1

    def test_budget_workflow(self):
        print_section("TEST 3: Budget Workflow (Create / Read / Update / Delete)")
        
        budget_data = {
            "user_id": self.user_id,
            "category": "Food",
            "monthly_limit": 15000,
            "month": datetime.now().strftime("%Y-%m")
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/budgets", json=budget_data)
            if response.status_code == 201:
                self.budget_id = response.json().get("budget_id")
                print_test("Create Budget", True)
                self.passed += 1
            else:
                print_test("Create Budget", False)
                self.failed += 1
                return
        except Exception as e:
            print_test("Create Budget", False)
            print(f"  Error: {str(e)}")
            self.failed += 1
            return

        try:
            response = requests.get(
                f"{API_BASE_URL}/budgets/{self.user_id}/{datetime.now().strftime('%Y-%m')}"
            )
            passed = response.status_code == 200 and "budgets" in response.text
            print_test("Get Budgets by Month", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Get Budgets by Month", False)
            self.failed += 1

        try:
            response = requests.post(
                f"{API_BASE_URL}/budgets/{self.budget_id}/add-spending",
                json={"amount": 5000}
            )
            passed = response.status_code == 200 and "success" in response.text
            print_test("Add Spending to Budget", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Add Spending to Budget", False)
            self.failed += 1

        try:
            response = requests.post(
                f"{API_BASE_URL}/budgets/check-alerts",
                json={"user_id": self.user_id, "month": datetime.now().strftime("%Y-%m")}
            )
            passed = response.status_code == 200
            print_test("Check Budget Alerts", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("Check Budget Alerts", False)
            self.failed += 1

    def test_agent_integration(self):
        print_section("TEST 4: Agent Integration")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/goals/analyze",
                json={"user_id": self.user_id, "monthly_income": 100000}
            )
            passed = response.status_code == 200 and "analyzed" in response.text
            print_test("GoalPlanner Agent Analysis", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("GoalPlanner Agent Analysis", False)
            print(f"  Error: {str(e)}")
            self.failed += 1

        try:
            response = requests.post(
                f"{API_BASE_URL}/budgets/monitor",
                json={"user_id": self.user_id, "month": datetime.now().strftime("%Y-%m")}
            )
            passed = response.status_code == 200 and "monitored" in response.text
            print_test("BudgetMonitor Agent Monitoring", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("BudgetMonitor Agent Monitoring", False)
            self.failed += 1

    def test_error_handling(self):
        print_section("TEST 5: Error Handling")
        
        try:
            response = requests.get(f"{API_BASE_URL}/goals/detail/invalid-id")
            passed = response.status_code == 404
            print_test("404 Error Handling (Invalid Goal)", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("404 Error Handling (Invalid Goal)", False)
            self.failed += 1

        try:
            response = requests.post(
                f"{API_BASE_URL}/goals",
                json={"invalid": "data"}
            )
            passed = response.status_code >= 400
            print_test("400 Error Handling (Invalid Data)", passed)
            self.passed += 1 if passed else 0
            self.failed += 0 if passed else 1
        except Exception as e:
            print_test("400 Error Handling (Invalid Data)", False)
            self.failed += 1

    def test_cleanup(self):
        print_section("TEST 6: Cleanup (Delete Created Resources)")
        
        if self.goal_id:
            try:
                response = requests.delete(f"{API_BASE_URL}/goals/{self.goal_id}")
                passed = response.status_code == 200
                print_test("Delete Goal", passed)
                self.passed += 1 if passed else 0
                self.failed += 0 if passed else 1
            except Exception as e:
                print_test("Delete Goal", False)
                self.failed += 1

        if self.budget_id:
            try:
                response = requests.delete(f"{API_BASE_URL}/budgets/{self.budget_id}")
                passed = response.status_code == 200
                print_test("Delete Budget", passed)
                self.passed += 1 if passed else 0
                self.failed += 0 if passed else 1
            except Exception as e:
                print_test("Delete Budget", False)
                self.failed += 1

    def print_summary(self):
        total = self.passed + self.failed
        percentage = (self.passed * 100 // total) if total > 0 else 0
        
        print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}PASSED: {self.passed}{Colors.END}")
        print(f"{Colors.RED}FAILED: {self.failed}{Colors.END}")
        print(f"Total: {total} tests")
        print(f"Success Rate: {percentage}%")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}ALL TESTS PASSED!{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}SOME TESTS FAILED!{Colors.END}\n")

if __name__ == "__main__":
    tester = E2ETests()
    tester.run_all()
