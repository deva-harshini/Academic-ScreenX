import httpx
import time

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

print("1. Testing Health & Login page...")
r = client.get("/login")
assert r.status_code == 200, f"Failed /login: {r.status_code}"
print("   -> /login returned HTTP 200 OK")

print("2. Testing Login Auth...")
r = client.post("/api/auth/login", json={"email": "faculty@university.edu", "password": "ASX_Faculty#2026!Pass"})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   -> Authenticated successfully! Token: {token[:20]}...")

print("3. Testing Demo 3 Sample Papers Trigger...")
r = client.post("/demo/load-samples", headers=headers)
assert r.status_code == 200, f"Load samples failed: {r.text}"
print("   -> Queued samples:", r.json())

print("4. Waiting 3.5 seconds for background multi-agent evaluations to finish...")
time.sleep(3.5)

print("5. Querying Submissions List...")
r = client.get("/api/submissions/list", headers=headers)
assert r.status_code == 200
items = r.json()
print(f"   -> Fetched {len(items)} processed submissions:")
for item in items:
    status_str = item['status'].upper()
    title_str = item['title'][:45]
    student_str = item['student_name']
    score_str = str(item['overall_score'])
    print(f"      • [{status_str:<10}] Score: {score_str}/10 | Title: {title_str}... | Student: {student_str}")

print("6. Querying Stats...")
r = client.get("/api/submissions/stats", headers=headers)
assert r.status_code == 200
stats = r.json()
print("   -> Dashboard Stats:", stats)

print("7. Querying Detailed Report for Top Submission...")
if items:
    sub_id = items[0]["id"]
    r = client.get(f"/api/submissions/{sub_id}/report", headers=headers)
    assert r.status_code == 200
    report = r.json()
    print("   -> Report Summary Review (3-sentence):", report.get("summary"))
    print("   -> Stage 1 Word Count & Sections:", report.get("word_count"), report.get("detected_sections"))
    print("   -> Stage 2 Verdict:", report.get("novelty_verdict"))
    print("   -> Stage 3 Dataset Feasibility:", report.get("dataset_feasibility"))

print("\n✓ ALL END-TO-END SERVER VERIFICATIONS PASSED PERFECTLY!")
