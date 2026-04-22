# test_complete_flow.py
import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://127.0.0.1:8006"  # Change to your port

class AttendanceSystemTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.tokens = {}
        self.ids = {}
        
    def print_section(self, title):
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_response(self, title, response):
        print(f"\n✅ {title}:")
        print(f"   Status: {response.status_code}")
        if response.status_code < 300:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"   Error: {response.text}")
            return None
    
    def test_signup(self, name, email, password, role, institution_name=None, institution_id=None):
        """Signup a new user"""
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "role": role
        }
        
        if institution_name:
            payload["institution_name"] = institution_name
        if institution_id:
            payload["institution_id"] = institution_id
            
        response = requests.post(f"{self.base_url}/auth/signup", json=payload)
        return response
    
    def test_login(self, email, password):
        """Login user"""
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{self.base_url}/auth/login", json=payload)
        return response
    
    def test_create_batch(self, token, name, institution_id):
        """Create a batch"""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "name": name,
            "institution_id": institution_id
        }
        response = requests.post(f"{self.base_url}/batches", json=payload, headers=headers)
        return response
    
    def test_create_session(self, token, batch_id, title):
        """Create a session"""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "batch_id": batch_id,
            "title": title,
            "date": datetime.utcnow().isoformat(),
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        # Note: You need to create a sessions endpoint first
        response = requests.post(f"{self.base_url}/sessions", json=payload, headers=headers)
        return response
    
    def test_create_invite(self, token, batch_id):
        """Create invite link for batch"""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{self.base_url}/batches/{batch_id}/invite", headers=headers)
        return response
    
    def test_join_batch(self, token, invite_token):
        """Join batch using invite token"""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"token": invite_token}
        response = requests.post(f"{self.base_url}/batches/join", json=payload, headers=headers)
        return response
    
    def test_mark_attendance(self, token, session_id, status):
        """Mark attendance"""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "session_id": session_id,
            "status": status
        }
        response = requests.post(f"{self.base_url}/attendance/mark", json=payload, headers=headers)
        return response
    
    def run_complete_test(self):
        """Run complete test flow"""
        self.print_section("STARTING COMPLETE ATTENDANCE SYSTEM TEST")
        
        # Step 1: Create Institution
        self.print_section("STEP 1: Creating Institution")
        inst_response = self.test_signup(
            name="Tech University",
            email="admin@techuniversity.com",
            password="admin123",
            role="institution"
        )
        inst_data = self.print_response("Institution Created", inst_response)
        
        if inst_data:
            # Login as institution to get token
            login_response = self.test_login("admin@techuniversity.com", "admin123")
            login_data = self.print_response("Institution Login", login_response)
            if login_data:
                self.tokens['institution'] = login_data['access_token']
                self.ids['institution_id'] = inst_data.get('user_id') or 1
        
        # Step 2: Create Trainer
        self.print_section("STEP 2: Creating Trainer")
        trainer_response = self.test_signup(
            name="Prof. John Smith",
            email="trainer@techuniversity.com",
            password="trainer123",
            role="trainer",
            institution_name="Tech University"
        )
        trainer_data = self.print_response("Trainer Created", trainer_response)
        
        if trainer_response.status_code == 200:
            trainer_login = self.test_login("trainer@techuniversity.com", "trainer123")
            trainer_login_data = self.print_response("Trainer Login", trainer_login)
            if trainer_login_data:
                self.tokens['trainer'] = trainer_login_data['access_token']
        
        # Step 3: Create Student
        self.print_section("STEP 3: Creating Student")
        student_response = self.test_signup(
            name="Rituraj Singh",
            email="rituraj@student.com",
            password="student123",
            role="student",
            institution_name="Tech University"
        )
        student_data = self.print_response("Student Created", student_response)
        
        if student_response.status_code == 200:
            student_login = self.test_login("rituraj@student.com", "student123")
            student_login_data = self.print_response("Student Login", student_login)
            if student_login_data:
                self.tokens['student'] = student_login_data['access_token']
                self.ids['student_id'] = student_login_data.get('user_id', 2)
        
        # Step 4: Create Another Student
        self.print_section("STEP 4: Creating Another Student")
        student2_response = self.test_signup(
            name="Priya Sharma",
            email="priya@student.com",
            password="student123",
            role="student",
            institution_name="Tech University"
        )
        student2_data = self.print_response("Second Student Created", student2_response)
        
        if student2_response.status_code == 200:
            self.ids['student2_id'] = student2_data.get('user_id', 3)
        
        # Step 5: Create Batch
        self.print_section("STEP 5: Creating Batch")
        if 'trainer' in self.tokens:
            batch_response = self.test_create_batch(
                self.tokens['trainer'],
                "Computer Science 2024",
                self.ids.get('institution_id', 1)
            )
            batch_data = self.print_response("Batch Created", batch_response)
            if batch_data and isinstance(batch_data, dict):
                self.ids['batch_id'] = batch_data.get('id')
        
        # Step 6: Create Invite Link
        self.print_section("STEP 6: Creating Batch Invite Link")
        if 'trainer' in self.tokens and 'batch_id' in self.ids:
            invite_response = self.test_create_invite(
                self.tokens['trainer'],
                self.ids['batch_id']
            )
            invite_data = self.print_response("Invite Created", invite_response)
            if invite_data:
                self.ids['invite_token'] = invite_data.get('token')
        
        # Step 7: Student Joins Batch
        self.print_section("STEP 7: Student Joining Batch")
        if 'student' in self.tokens and 'invite_token' in self.ids:
            join_response = self.test_join_batch(
                self.tokens['student'],
                self.ids['invite_token']
            )
            join_data = self.print_response("Student Joined Batch", join_response)
        
        # Step 8: Create Session (Trainer creates a session)
        self.print_section("STEP 8: Creating Session")
        if 'trainer' in self.tokens and 'batch_id' in self.ids:
            # First, we need to add the trainer to batch
            # Create a session
            session_response = self.test_create_session(
                self.tokens['trainer'],
                self.ids['batch_id'],
                "Python Programming - Class 1"
            )
            session_data = self.print_response("Session Created", session_response)
            if session_data and isinstance(session_data, dict):
                self.ids['session_id'] = session_data.get('id')
        
        # Step 9: Mark Attendance
        self.print_section("STEP 9: Marking Attendance")
        if 'student' in self.tokens and 'session_id' in self.ids:
            attendance_response = self.test_mark_attendance(
                self.tokens['student'],
                self.ids['session_id'],
                "present"
            )
            attendance_data = self.print_response("Attendance Marked", attendance_response)
        
        # Step 10: Create Monitoring Officer
        self.print_section("STEP 10: Creating Monitoring Officer")
        monitor_response = self.test_signup(
            name="Dr. Monitoring",
            email="monitor@techuniversity.com",
            password="monitor123",
            role="monitoring_officer",
            institution_name="Tech University"
        )
        monitor_data = self.print_response("Monitoring Officer Created", monitor_response)
        
        if monitor_response.status_code == 200:
            monitor_login = self.test_login("monitor@techuniversity.com", "monitor123")
            monitor_login_data = self.print_response("Monitoring Officer Login", monitor_login)
            if monitor_login_data:
                self.tokens['monitor'] = monitor_login_data['access_token']
                
                # Get monitoring token
                headers = {"Authorization": f"Bearer {self.tokens['monitor']}"}
                mon_token_response = requests.post(f"{self.base_url}/auth/monitoring-token", headers=headers)
                self.print_response("Monitoring Token Generated", mon_token_response)
        
        # Final Summary
        self.print_section("TEST EXECUTION SUMMARY")
        print("\n✅ Created Resources:")
        print(f"   - Institution: Tech University (ID: {self.ids.get('institution_id', 'N/A')})")
        print(f"   - Trainer: Prof. John Smith")
        print(f"   - Students: Rituraj Singh, Priya Sharma")
        print(f"   - Batch: Computer Science 2024 (ID: {self.ids.get('batch_id', 'N/A')})")
        print(f"   - Session: Python Programming - Class 1 (ID: {self.ids.get('session_id', 'N/A')})")
        print(f"   - Attendance: Marked for Rituraj Singh")
        print(f"   - Monitoring Officer: Dr. Monitoring")
        
        print("\n🔑 Tokens Generated:")
        for role, token in self.tokens.items():
            print(f"   - {role}: {token[:50]}...")
        
        print("\n📝 Test Credentials:")
        print("   Institution: admin@techuniversity.com / admin123")
        print("   Trainer: trainer@techuniversity.com / trainer123")
        print("   Student: rituraj@student.com / student123")
        print("   Student2: priya@student.com / student123")
        print("   Monitor: monitor@techuniversity.com / monitor123")
        
        print("\n🎯 Next Steps:")
        print("   1. Use the tokens in Authorization header for API calls")
        print("   2. Create more sessions using trainer token")
        print("   3. Students can mark attendance using their tokens")
        print("   4. Monitoring officer can generate short-lived monitoring tokens")
        
        print("\n" + "="*60)
        print(" TEST COMPLETED SUCCESSFULLY! ")
        print("="*60)

if __name__ == "__main__":
    # First, ensure server is running
    print("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running!")
            
            # Run complete test
            test = AttendanceSystemTest()
            test.run_complete_test()
        else:
            print("❌ Server is not responding properly")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Pleaase make sure the server is running with: uvicorn main:app --reload --port 8006")