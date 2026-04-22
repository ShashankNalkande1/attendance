# test_all_endpoints.py
import requests
import json
from datetime import datetime
import time

BASE_URL = "https://attendance-pkjm.onrender.com"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add(self, name, status, message=""):
        if status:
            self.passed += 1
            self.results.append(f"✅ PASS: {name} - {message}")
        else:
            self.failed += 1
            self.results.append(f"❌ FAIL: {name} - {message}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        for result in self.results:
            print(result)
        print("="*60)
        print(f"TOTAL: {self.passed + self.failed} | ✅ PASSED: {self.passed} | ❌ FAILED: {self.failed}")
        print("="*60)
        return self.failed == 0

results = TestResults()

def test_endpoint(method, endpoint, data=None, token=None, expected_status=200):
    """Test an endpoint and return response"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
        
        status_match = response.status_code == expected_status
        return status_match, response
    except Exception as e:
        return False, str(e)

print("="*60)
print("ATTENDANCE SYSTEM - COMPLETE TEST SUITE")
print("="*60)

# Step 1: Health Check
print("\n📡 TESTING API CONNECTION...")
status, response = test_endpoint("GET", "/health")
results.add("API Health Check", status, "Server is running" if status else "Server not responding")

if not status:
    print("\n❌ Server is not running! Please start the server first:")
    print("   uvicorn main:app --reload --port 8006")
    exit(1)

# Step 2: Create Institution
print("\n🏛️ TESTING INSTITUTION CREATION...")
inst_data = {
    "name": "Tech University",
    "email": "admin@techuniversity.com",
    "password": "admin123",
    "role": "institution"
}
status, response = test_endpoint("POST", "/auth/signup", inst_data)
results.add("Create Institution", status, "Institution created successfully" if status else f"Error: {response}")

if status:
    inst_token = response.json().get("access_token")
    inst_id = response.json().get("user_id", 1)
    results.add("Institution Token Generated", bool(inst_token), f"Token: {inst_token[:30]}...")
else:
    inst_token = None
    inst_id = 1

# Step 3: Login as Institution
print("\n🔐 TESTING INSTITUTION LOGIN...")
login_data = {"email": "admin@techuniversity.com", "password": "admin123"}
status, response = test_endpoint("POST", "/auth/login", login_data)
results.add("Institution Login", status, "Login successful" if status else "Login failed")

if status:
    inst_login_token = response.json().get("access_token")
else:
    inst_login_token = None

# Step 4: Create Trainer
print("\n👨‍🏫 TESTING TRAINER CREATION...")
trainer_data = {
    "name": "Prof. John Smith",
    "email": "trainer@techuniversity.com",
    "password": "trainer123",
    "role": "trainer",
    "institution_name": "Tech University"
}
status, response = test_endpoint("POST", "/auth/signup", trainer_data)
results.add("Create Trainer", status, "Trainer created successfully" if status else f"Error: {response}")

if status:
    trainer_token = response.json().get("access_token")
    trainer_id = response.json().get("user_id", 2)
else:
    trainer_token = None
    trainer_id = 2

# Step 5: Login as Trainer
print("\n🔐 TESTING TRAINER LOGIN...")
login_data = {"email": "trainer@techuniversity.com", "password": "trainer123"}
status, response = test_endpoint("POST", "/auth/login", login_data)
results.add("Trainer Login", status, "Login successful" if status else "Login failed")

if status:
    trainer_login_token = response.json().get("access_token")
else:
    trainer_login_token = trainer_token

# Step 6: Create Student
print("\n🎓 TESTING STUDENT CREATION...")
student_data = {
    "name": "Rituraj Singh",
    "email": "rituraj@student.com",
    "password": "student123",
    "role": "student",
    "institution_name": "Tech University"
}
status, response = test_endpoint("POST", "/auth/signup", student_data)
results.add("Create Student", status, "Student created successfully" if status else f"Error: {response}")

if status:
    student_token = response.json().get("access_token")
    student_id = response.json().get("user_id", 3)
else:
    student_token = None
    student_id = 3

# Step 7: Login as Student
print("\n🔐 TESTING STUDENT LOGIN...")
login_data = {"email": "rituraj@student.com", "password": "student123"}
status, response = test_endpoint("POST", "/auth/login", login_data)
results.add("Student Login", status, "Login successful" if status else "Login failed")

if status:
    student_login_token = response.json().get("access_token")
else:
    student_login_token = student_token

# Step 8: Get All Users (requires trainer token)
print("\n👥 TESTING GET USERS...")
if trainer_login_token:
    status, response = test_endpoint("GET", "/users/", token=trainer_login_token)
    results.add("Get All Users", status, f"Retrieved {len(response.json()) if status else 0} users" if status else "Failed")
    
    if status:
        users = response.json()
        print(f"   Users found: {len(users)}")
        for user in users[:3]:
            print(f"   - {user['name']} ({user['role']})")
else:
    results.add("Get All Users", False, "No trainer token available")

# Step 9: Get Institutions
print("\n🏛️ TESTING GET INSTITUTIONS...")
status, response = test_endpoint("GET", "/users/institutions")
results.add("Get Institutions", status, f"Found {len(response.json()) if status else 0} institutions" if status else "Failed")

if status:
    institutions = response.json()
    for inst in institutions:
        print(f"   - {inst['name']} (ID: {inst['id']})")

# Step 10: Create Batch
print("\n📦 TESTING BATCH CREATION...")
if trainer_login_token:
    batch_data = {
        "name": "Computer Science 2024",
        "institution_id": inst_id
    }
    status, response = test_endpoint("POST", "/batches", batch_data, trainer_login_token)
    results.add("Create Batch", status, "Batch created successfully" if status else f"Error: {response}")
    
    if status:
        batch_id = response.json().get("id")
        results.add("Batch ID Generated", bool(batch_id), f"Batch ID: {batch_id}")
    else:
        batch_id = 1
else:
    results.add("Create Batch", False, "No trainer token available")
    batch_id = 1

# Step 11: Create Invite
print("\n🔗 TESTING INVITE CREATION...")
if trainer_login_token and batch_id:
    status, response = test_endpoint("POST", f"/batches/{batch_id}/invite", token=trainer_login_token)
    results.add("Create Invite", status, "Invite created successfully" if status else f"Error: {response}")
    
    if status:
        invite_token = response.json().get("token")
        results.add("Invite Token Generated", bool(invite_token), f"Token: {invite_token[:30]}...")
    else:
        invite_token = None
else:
    results.add("Create Invite", False, "Missing trainer token or batch ID")
    invite_token = None

# Step 12: Join Batch
print("\n🔗 TESTING JOIN BATCH...")
if student_login_token and invite_token:
    join_data = {"token": invite_token}
    status, response = test_endpoint("POST", "/batches/join", join_data, student_login_token)
    results.add("Join Batch", status, "Student joined batch successfully" if status else f"Error: {response}")
else:
    results.add("Join Batch", False, "Missing student token or invite token")

# Step 13: Create Monitoring Officer
print("\n👁️ TESTING MONITORING OFFICER CREATION...")
monitor_data = {
    "name": "Dr. Monitoring",
    "email": "monitor@techuniversity.com",
    "password": "monitor123",
    "role": "monitoring_officer",
    "institution_name": "Tech University"
}
status, response = test_endpoint("POST", "/auth/signup", monitor_data)
results.add("Create Monitoring Officer", status, "Monitoring officer created" if status else f"Error: {response}")

if status:
    monitor_token = response.json().get("access_token")
    results.add("Monitor Token Generated", bool(monitor_token), f"Token: {monitor_token[:30]}...")
else:
    monitor_token = None

# Step 14: Login as Monitoring Officer
print("\n🔐 TESTING MONITORING OFFICER LOGIN...")
login_data = {"email": "monitor@techuniversity.com", "password": "monitor123"}
status, response = test_endpoint("POST", "/auth/login", login_data)
results.add("Monitoring Officer Login", status, "Login successful" if status else "Login failed")

if status:
    monitor_login_token = response.json().get("access_token")
else:
    monitor_login_token = monitor_token

# Step 15: Generate Monitoring Token
print("\n🎫 TESTING MONITORING TOKEN GENERATION...")
if monitor_login_token:
    status, response = test_endpoint("POST", "/auth/monitoring-token", token=monitor_login_token)
    results.add("Generate Monitoring Token", status, "Short-lived token generated" if status else f"Error: {response}")
else:
    results.add("Generate Monitoring Token", False, "No monitoring officer token available")

# Step 16: Get Current User Info
print("\n👤 TESTING GET CURRENT USER...")
if student_login_token:
    status, response = test_endpoint("GET", "/auth/me", token=student_login_token)
    results.add("Get Current User", status, f"User: {response.json().get('email') if status else 'Unknown'}" if status else "Failed")
else:
    results.add("Get Current User", False, "No student token available")

# Print final summary
success = results.print_summary()

# Print credentials for manual testing
print("\n" + "="*60)
print("📝 TEST CREDENTIALS (Save these for manual testing)")
print("="*60)
print("\n🔑 LOGIN CREDENTIALS:")
print("   Institution: admin@techuniversity.com / admin123")
print("   Trainer: trainer@techuniversity.com / trainer123")
print("   Student: rituraj@student.com / student123")
print("   Monitor: monitor@techuniversity.com / monitor123")

print("\n🔐 AUTH TOKENS (Copy these):")
if 'trainer_login_token' in locals() and trainer_login_token:
    print(f"   Trainer Token: {trainer_login_token[:50]}...")
if 'student_login_token' in locals() and student_login_token:
    print(f"   Student Token: {student_login_token[:50]}...")
if 'monitor_login_token' in locals() and monitor_login_token:
    print(f"   Monitor Token: {monitor_login_token[:50]}...")

print("\n🌐 API ENDPOINTS:")
print("   Swagger UI: http://127.0.0.1:8006/docs")
print("   ReDoc: http://127.0.0.1:8006/redoc")
print("   Health: http://127.0.0.1:8006/health")

print("\n💡 Quick Test Commands:")
print('   curl -X POST http://127.0.0.1:8006/auth/login -H "Content-Type: application/json" -d "{\\"email\\":\\"student@test.com\\",\\"password\\":\\"test123\\"}"')
print('   curl -X GET http://127.0.0.1:8006/auth/me -H "Authorization: Bearer YOUR_TOKEN"')
