import os
import re

FRONTEND_DIR = 'frontend'

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

student_dash = read_file(os.path.join(FRONTEND_DIR, 'student', 'dashboard.html'))
management_dash = read_file(os.path.join(FRONTEND_DIR, 'management', 'dashboard.html'))

# Extract student navbar (everything between <nav> and </nav>)
match_nav = re.search(r'(<nav.*?</nav>)', student_dash, re.DOTALL)
if match_nav:
    nav_html = match_nav.group(1)
    write_file(os.path.join(FRONTEND_DIR, 'components', 'layout', 'student-navbar.html'), nav_html)
    print("Created student-navbar.html")

# Extract management sidebar (everything between <aside> and </aside>)
match_aside = re.search(r'(<aside.*?</aside>)', management_dash, re.DOTALL)
if match_aside:
    aside_html = match_aside.group(1)
    write_file(os.path.join(FRONTEND_DIR, 'components', 'layout', 'management-sidebar.html'), aside_html)
    print("Created management-sidebar.html")

# Extract management header (everything between <header> and </header>)
match_header = re.search(r'(<header.*?</header>)', management_dash, re.DOTALL)
if match_header:
    header_html = match_header.group(1)
    write_file(os.path.join(FRONTEND_DIR, 'components', 'layout', 'management-navbar.html'), header_html)
    print("Created management-navbar.html")

