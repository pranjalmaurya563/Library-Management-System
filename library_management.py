"""
============================================================
  LIBRARY MANAGEMENT SYSTEM
  BCA IV Semester - MID-II Assignment
  Language: Python
============================================================
Features:
  - Book issue and return with due date tracking
  - Fine calculation for late returns
  - Search books by title or author
  - Maintain user and book records (CSV files)
  - Display available and issued books
  - Backup and restore data
============================================================
"""

import csv
import os
import shutil
from datetime import datetime, timedelta

# ── File paths ──────────────────────────────────────────────
BOOKS_FILE    = "books.csv"
MEMBERS_FILE  = "members.csv"
ISSUED_FILE   = "issued_books.csv"
BACKUP_DIR    = "library_backup"

# Fine per day (in rupees)
FINE_PER_DAY  = 5
# Default loan period (days)
LOAN_DAYS     = 14

# ── CSV helpers ─────────────────────────────────────────────

def read_csv(filename):
    """Read a CSV file and return list of dicts."""
    if not os.path.exists(filename):
        return []
    with open(filename, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(filename, rows, fieldnames):
    """Write list of dicts to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ── Initialise data files with sample data ──────────────────

def initialise_data():
    """Create sample data files if they don't exist."""
    if not os.path.exists(BOOKS_FILE):
        books = [
            {"book_id": "B001", "title": "Python Programming",
             "author": "Guido van Rossum", "quantity": 3, "available": 3},
            {"book_id": "B002", "title": "Data Structures",
             "author": "Mark Allen Weiss", "quantity": 2, "available": 2},
            {"book_id": "B003", "title": "Database Management",
             "author": "Ramez Elmasri",   "quantity": 4, "available": 4},
            {"book_id": "B004", "title": "Operating Systems",
             "author": "Silberschatz",    "quantity": 2, "available": 2},
            {"book_id": "B005", "title": "Computer Networks",
             "author": "Andrew Tanenbaum","quantity": 3, "available": 3},
        ]
        write_csv(BOOKS_FILE, books,
                  ["book_id","title","author","quantity","available"])
        print("  [+] books.csv created with sample data.")

    if not os.path.exists(MEMBERS_FILE):
        members = [
            {"member_id": "M001", "name": "Rahul Sharma",  "email": "rahul@mail.com",  "phone": "9876543210"},
            {"member_id": "M002", "name": "Priya Verma",   "email": "priya@mail.com",  "phone": "9876543211"},
            {"member_id": "M003", "name": "Amit Patel",    "email": "amit@mail.com",   "phone": "9876543212"},
        ]
        write_csv(MEMBERS_FILE, members,
                  ["member_id","name","email","phone"])
        print("  [+] members.csv created with sample data.")

    if not os.path.exists(ISSUED_FILE):
        write_csv(ISSUED_FILE, [],
                  ["issue_id","book_id","member_id","issue_date","due_date","return_date","fine"])
        print("  [+] issued_books.csv created (empty).")


# ── BOOK functions ───────────────────────────────────────────

def add_book():
    print("\n--- Add New Book ---")
    books = read_csv(BOOKS_FILE)
    book_id = input("Enter Book ID (e.g. B006): ").strip().upper()

    # Check duplicate
    if any(b["book_id"] == book_id for b in books):
        print("  [!] Book ID already exists.")
        return

    title    = input("Title   : ").strip()
    author   = input("Author  : ").strip()
    try:
        qty  = int(input("Quantity: "))
    except ValueError:
        print("  [!] Invalid quantity.")
        return

    books.append({"book_id": book_id, "title": title,
                  "author": author, "quantity": qty, "available": qty})
    write_csv(BOOKS_FILE, books,
              ["book_id","title","author","quantity","available"])
    print(f"  [✓] Book '{title}' added successfully.")


def search_books():
    print("\n--- Search Books ---")
    keyword = input("Enter title or author to search: ").strip().lower()
    books   = read_csv(BOOKS_FILE)
    results = [b for b in books
               if keyword in b["title"].lower() or keyword in b["author"].lower()]

    if not results:
        print("  [!] No books found.")
        return

    print(f"\n{'ID':<8}{'Title':<30}{'Author':<25}{'Qty':<6}{'Available'}")
    print("-" * 75)
    for b in results:
        print(f"{b['book_id']:<8}{b['title']:<30}{b['author']:<25}"
              f"{b['quantity']:<6}{b['available']}")


def display_available_books():
    print("\n--- Available Books ---")
    books   = read_csv(BOOKS_FILE)
    avail   = [b for b in books if int(b["available"]) > 0]

    if not avail:
        print("  [!] No books available.")
        return

    print(f"\n{'ID':<8}{'Title':<30}{'Author':<25}{'Available'}")
    print("-" * 70)
    for b in avail:
        print(f"{b['book_id']:<8}{b['title']:<30}{b['author']:<25}{b['available']}")


def display_issued_books():
    print("\n--- Currently Issued Books ---")
    issued  = [r for r in read_csv(ISSUED_FILE) if not r["return_date"]]
    books   = {b["book_id"]: b["title"]   for b in read_csv(BOOKS_FILE)}
    members = {m["member_id"]: m["name"]  for m in read_csv(MEMBERS_FILE)}

    if not issued:
        print("  [!] No books are currently issued.")
        return

    print(f"\n{'IssueID':<10}{'Book':<28}{'Member':<22}{'Issue Date':<14}{'Due Date'}")
    print("-" * 85)
    for r in issued:
        book_name   = books.get(r["book_id"],   r["book_id"])
        member_name = members.get(r["member_id"], r["member_id"])
        print(f"{r['issue_id']:<10}{book_name:<28}{member_name:<22}"
              f"{r['issue_date']:<14}{r['due_date']}")


# ── ISSUE / RETURN ───────────────────────────────────────────

def _next_issue_id(issued):
    """Generate next issue ID like ISS001, ISS002 …"""
    if not issued:
        return "ISS001"
    nums = [int(r["issue_id"][3:]) for r in issued if r["issue_id"].startswith("ISS")]
    return f"ISS{max(nums) + 1:03d}" if nums else "ISS001"


def issue_book():
    print("\n--- Issue Book ---")
    books   = read_csv(BOOKS_FILE)
    members = read_csv(MEMBERS_FILE)
    issued  = read_csv(ISSUED_FILE)

    # Validate member
    member_id = input("Member ID: ").strip().upper()
    if not any(m["member_id"] == member_id for m in members):
        print("  [!] Member not found.")
        return

    # Validate book
    book_id = input("Book ID  : ").strip().upper()
    book_row = next((b for b in books if b["book_id"] == book_id), None)
    if not book_row:
        print("  [!] Book not found.")
        return
    if int(book_row["available"]) <= 0:
        print("  [!] Book not available right now.")
        return

    # Check if member already has this book
    already = any(r["book_id"] == book_id and r["member_id"] == member_id
                  and not r["return_date"] for r in issued)
    if already:
        print("  [!] Member has already issued this book.")
        return

    today    = datetime.today()
    due_date = today + timedelta(days=LOAN_DAYS)

    issue_record = {
        "issue_id"   : _next_issue_id(issued),
        "book_id"    : book_id,
        "member_id"  : member_id,
        "issue_date" : today.strftime("%Y-%m-%d"),
        "due_date"   : due_date.strftime("%Y-%m-%d"),
        "return_date": "",
        "fine"       : "0",
    }
    issued.append(issue_record)
    write_csv(ISSUED_FILE, issued,
              ["issue_id","book_id","member_id","issue_date","due_date","return_date","fine"])

    # Decrease available count
    for b in books:
        if b["book_id"] == book_id:
            b["available"] = str(int(b["available"]) - 1)
            break
    write_csv(BOOKS_FILE, books,
              ["book_id","title","author","quantity","available"])

    print(f"\n  [✓] Book issued! Issue ID: {issue_record['issue_id']}")
    print(f"      Due date: {due_date.strftime('%d-%m-%Y')}")


def return_book():
    print("\n--- Return Book ---")
    issued = read_csv(ISSUED_FILE)
    books  = read_csv(BOOKS_FILE)

    issue_id = input("Enter Issue ID (e.g. ISS001): ").strip().upper()
    record   = next((r for r in issued
                     if r["issue_id"] == issue_id and not r["return_date"]), None)
    if not record:
        print("  [!] Issue ID not found or book already returned.")
        return

    today      = datetime.today()
    due_date   = datetime.strptime(record["due_date"], "%Y-%m-%d")
    fine       = 0

    if today > due_date:
        overdue_days = (today - due_date).days
        fine         = overdue_days * FINE_PER_DAY
        print(f"  [!] Book is {overdue_days} day(s) overdue.")
        print(f"      Fine: ₹{fine}")
    else:
        print("  [✓] Book returned on time. No fine.")

    # Update record
    record["return_date"] = today.strftime("%Y-%m-%d")
    record["fine"]        = str(fine)
    write_csv(ISSUED_FILE, issued,
              ["issue_id","book_id","member_id","issue_date","due_date","return_date","fine"])

    # Increase available count
    for b in books:
        if b["book_id"] == record["book_id"]:
            b["available"] = str(int(b["available"]) + 1)
            break
    write_csv(BOOKS_FILE, books,
              ["book_id","title","author","quantity","available"])

    print("  [✓] Book returned successfully.")


# ── MEMBER functions ─────────────────────────────────────────

def add_member():
    print("\n--- Add New Member ---")
    members   = read_csv(MEMBERS_FILE)
    member_id = input("Member ID (e.g. M004): ").strip().upper()

    if any(m["member_id"] == member_id for m in members):
        print("  [!] Member ID already exists.")
        return

    name  = input("Name  : ").strip()
    email = input("Email : ").strip()
    phone = input("Phone : ").strip()

    members.append({"member_id": member_id, "name": name,
                    "email": email, "phone": phone})
    write_csv(MEMBERS_FILE, members,
              ["member_id","name","email","phone"])
    print(f"  [✓] Member '{name}' added successfully.")


def display_members():
    print("\n--- All Members ---")
    members = read_csv(MEMBERS_FILE)
    if not members:
        print("  [!] No members found.")
        return
    print(f"\n{'ID':<10}{'Name':<22}{'Email':<28}{'Phone'}")
    print("-" * 72)
    for m in members:
        print(f"{m['member_id']:<10}{m['name']:<22}{m['email']:<28}{m['phone']}")


# ── BACKUP / RESTORE ─────────────────────────────────────────

def backup_data():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backed = []
    for f in [BOOKS_FILE, MEMBERS_FILE, ISSUED_FILE]:
        if os.path.exists(f):
            dest = os.path.join(BACKUP_DIR, f"{timestamp}_{f}")
            shutil.copy2(f, dest)
            backed.append(dest)
    print(f"\n  [✓] Backup created: {', '.join(backed)}")


def restore_data():
    if not os.path.exists(BACKUP_DIR):
        print("  [!] No backup directory found.")
        return

    backups = sorted(os.listdir(BACKUP_DIR))
    if not backups:
        print("  [!] No backup files found.")
        return

    # Get latest timestamp
    timestamps = sorted(set(f[:15] for f in backups if len(f) > 15), reverse=True)
    if not timestamps:
        print("  [!] Could not parse backup timestamps.")
        return

    latest = timestamps[0]
    print(f"\n  Restoring from backup: {latest}")
    confirm = input("  Are you sure? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  [!] Restore cancelled.")
        return

    for f in [BOOKS_FILE, MEMBERS_FILE, ISSUED_FILE]:
        src = os.path.join(BACKUP_DIR, f"{latest}_{f}")
        if os.path.exists(src):
            shutil.copy2(src, f)
            print(f"  [✓] Restored: {f}")

    print("  [✓] Restore complete.")


# ── ADMIN LOGIN ──────────────────────────────────────────────

ADMIN_USER = "admin"
ADMIN_PASS = "library123"

def admin_login():
    print("\n=== Admin Login ===")
    user = input("Username: ").strip()
    pwd  = input("Password: ").strip()
    if user == ADMIN_USER and pwd == ADMIN_PASS:
        print("  [✓] Login successful!\n")
        return True
    else:
        print("  [✗] Invalid credentials.")
        return False


# ── MAIN MENU ────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("      LIBRARY MANAGEMENT SYSTEM")
    print("      BCA IV Semester | Python Project")
    print("=" * 55)

    # Initialise sample data
    initialise_data()

    # Admin login
    if not admin_login():
        return

    while True:
        print("\n╔══════════════════════════════╗")
        print("║         MAIN MENU            ║")
        print("╠══════════════════════════════╣")
        print("║  BOOKS                       ║")
        print("║  1. Add Book                 ║")
        print("║  2. Search Books             ║")
        print("║  3. Display Available Books  ║")
        print("║  4. Display Issued Books     ║")
        print("╠══════════════════════════════╣")
        print("║  ISSUE / RETURN              ║")
        print("║  5. Issue Book               ║")
        print("║  6. Return Book              ║")
        print("╠══════════════════════════════╣")
        print("║  MEMBERS                     ║")
        print("║  7. Add Member               ║")
        print("║  8. Display All Members      ║")
        print("╠══════════════════════════════╣")
        print("║  DATA                        ║")
        print("║  9. Backup Data              ║")
        print("║ 10. Restore Data             ║")
        print("╠══════════════════════════════╣")
        print("║  0. Exit                     ║")
        print("╚══════════════════════════════╝")

        choice = input("\nEnter choice: ").strip()

        try:
            if   choice == "1":  add_book()
            elif choice == "2":  search_books()
            elif choice == "3":  display_available_books()
            elif choice == "4":  display_issued_books()
            elif choice == "5":  issue_book()
            elif choice == "6":  return_book()
            elif choice == "7":  add_member()
            elif choice == "8":  display_members()
            elif choice == "9":  backup_data()
            elif choice == "10": restore_data()
            elif choice == "0":
                print("\n  Goodbye! Thank you for using Library Management System.")
                break
            else:
                print("  [!] Invalid choice. Please enter 0-10.")
        except Exception as e:
            print(f"  [!] Error: {e}")


if __name__ == "__main__":
    main()