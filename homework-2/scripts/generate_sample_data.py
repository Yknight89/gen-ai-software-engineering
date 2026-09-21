"""Generate realistic sample ticket data in CSV, JSON and XML, plus invalid files."""
import csv, json, os, random
import xml.etree.ElementTree as ET
from xml.dom import minidom

random.seed(42)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(HERE, "demo")
os.makedirs(DEMO, exist_ok=True)

FIRST = ["Jane", "Bob", "Ann", "Carl", "Dana", "Ed", "Fay", "Gil", "Hana", "Ivan",
         "Jo", "Kim", "Leo", "Mona", "Ned", "Ola", "Pia", "Ravi", "Sam", "Tara"]
LAST = ["Doe", "Lee", "Ng", "Park", "Rao", "Sun", "Vega", "Wong", "Ali", "Cruz"]

TEMPLATES = [
    ("account_access", ["Cannot log in to my account", "Password reset not working", "Locked out after 2FA"],
     "I cannot access my account after a password reset and I am locked out, this is blocking me."),
    ("billing_question", ["Refund for double charge", "Invoice question", "Overcharged this month"],
     "I was charged twice on my latest invoice and would like a refund for the extra payment."),
    ("technical_issue", ["App crashes on startup", "500 error on dashboard", "Page is very slow"],
     "The application crashes with a 500 error and the dashboard is extremely slow to load."),
    ("feature_request", ["Please add dark mode", "Export to PDF idea", "Suggestion for filters"],
     "It would be a nice enhancement if you could please add this feature to improve the product."),
    ("bug_report", ["Bug: totals are wrong", "Defect in report export", "Steps to reproduce a crash"],
     "Here are the steps to reproduce a clear defect: the totals are wrong, this looks like a bug."),
    ("other", ["General question", "Feedback for the team", "Just saying hello"],
     "I just had a general question about the product roadmap and wanted to share some feedback."),
]
PRIORITIES = ["urgent", "high", "medium", "low"]
STATUSES = ["new", "in_progress", "waiting_customer", "resolved", "closed"]
SOURCES = ["web_form", "email", "api", "chat", "phone"]
DEVICES = ["desktop", "mobile", "tablet"]


def make(i):
    cat, subjects, desc = random.choice(TEMPLATES)
    fn, ln = random.choice(FIRST), random.choice(LAST)
    return {
        "customer_id": f"CUST-{1000+i}",
        "customer_email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
        "customer_name": f"{fn} {ln}",
        "subject": random.choice(subjects),
        "description": desc,
        "category": cat,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "tags": random.sample(["ui", "backend", "urgent", "vip", "mobile", "refund"], k=random.randint(0, 2)),
        "source": random.choice(SOURCES),
        "device_type": random.choice(DEVICES),
    }


# CSV — 50 tickets
with open(os.path.join(DEMO, "sample_tickets.csv"), "w", newline="") as f:
    cols = ["customer_id", "customer_email", "customer_name", "subject", "description",
            "category", "priority", "status", "tags", "source", "device_type"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for i in range(50):
        r = make(i)
        r["tags"] = ";".join(r["tags"])
        w.writerow(r)

# JSON — 20 tickets (nested metadata)
tickets = []
for i in range(100, 120):
    r = make(i)
    tickets.append({
        "customer_id": r["customer_id"], "customer_email": r["customer_email"],
        "customer_name": r["customer_name"], "subject": r["subject"],
        "description": r["description"], "category": r["category"],
        "priority": r["priority"], "status": r["status"], "tags": r["tags"],
        "metadata": {"source": r["source"], "device_type": r["device_type"]},
    })
with open(os.path.join(DEMO, "sample_tickets.json"), "w") as f:
    json.dump(tickets, f, indent=2)

# XML — 30 tickets
root = ET.Element("tickets")
for i in range(200, 230):
    r = make(i)
    t = ET.SubElement(root, "ticket")
    for k in ("customer_id", "customer_email", "customer_name", "subject", "description",
              "category", "priority", "status"):
        ET.SubElement(t, k).text = str(r[k])
    tags = ET.SubElement(t, "tags")
    for tag in r["tags"]:
        ET.SubElement(tags, "tag").text = tag
    md = ET.SubElement(t, "metadata")
    ET.SubElement(md, "source").text = r["source"]
    ET.SubElement(md, "device_type").text = r["device_type"]
xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
with open(os.path.join(DEMO, "sample_tickets.xml"), "w") as f:
    f.write(xml_str)

# Invalid files for negative tests
with open(os.path.join(DEMO, "invalid_tickets.csv"), "w") as f:
    f.write("customer_id,customer_email,customer_name,subject,description,category,priority\n")
    f.write("CUST-X,bademail,No Email,Bad row,short,other,low\n")          # bad email + short desc
    f.write("CUST-Y,y@example.com,Enum Bad,Valid subject here,This description is definitely long enough to pass.,nonsense,huge\n")  # bad enums
with open(os.path.join(DEMO, "invalid_tickets.json"), "w") as f:
    f.write('{"tickets": [ {"customer_id": "Z", "broken": ')  # malformed JSON

print("Sample data written to demo/:")
for name in ["sample_tickets.csv", "sample_tickets.json", "sample_tickets.xml",
             "invalid_tickets.csv", "invalid_tickets.json"]:
    p = os.path.join(DEMO, name)
    print(f"  {name}: {os.path.getsize(p)} bytes")
