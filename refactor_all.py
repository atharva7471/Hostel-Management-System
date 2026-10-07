import os
import re

FRONTEND_DIR = 'frontend'

def refactor_file(filepath, layout_type):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if '<body data-layout="' in content:
        return # already refactored
        
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else "HostelOS"
    
    if layout_type == 'student':
        main_match = re.search(r'<main[^>]*>(.*?)</main>', content, re.DOTALL)
        if main_match:
            # Strip the max-w-5xl wrapper if it exists because layout.js adds it
            inner = main_match.group(1).strip()
            # Let's remove the wrapper if it matches
            wrapper_match = re.match(r'<div class="max-w-5xl mx-auto[^>]*>(.*?)</div>\s*$', inner, re.DOTALL)
            if wrapper_match:
                # Need to be careful, this is a greedy regex that might strip too much or too little if there are nested divs.
                # Actually, layout.js wraps in <div class="max-w-5xl mx-auto space-y-8">.
                # If we don't strip it, they just have nested max-w-5xl, which is fine and safe.
                pass
            main_html = inner
        else:
            return False
            
    elif layout_type == 'management':
        main_match = re.search(r'<header.*?</header>.*?<div[^>]*custom-scrollbar[^>]*>(.*?)</div>\s*</main>', content, re.DOTALL)
        if not main_match:
            main_match = re.search(r'<main[^>]*>.*?<header.*?</header>.*?<div[^>]*>(.*?)</div>\s*</main>', content, re.DOTALL)
        if main_match:
            # We want the content inside the custom-scrollbar div
            inner = main_match.group(1).strip()
            # Often there's a <div class="max-w-7xl mx-auto space-y-6"> that we might want to keep.
            main_html = inner
        else:
            return False
    else:
        # For login, register, etc.
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
        if not body_match:
            return False
        inner = body_match.group(1).strip()
        # Remove scripts from inner
        inner = re.sub(r'<script.*?</script>', '', inner, flags=re.DOTALL).strip()
        main_html = inner

    script_blocks = re.findall(r'(<script[^>]*>.*?</script>)', content, re.DOTALL)
    
    kept_scripts = []
    for s in script_blocks:
        if 'src=' in s and ('tailwindcss' in s or 'lucide' in s or 'theme.js' in s or 'auth.js' in s or 'utils.js' in s or 'components.js' in s or 'layout.js' in s or 'app.js' in s or 'api.js' in s):
            continue
        
        # We need to change DOMContentLoaded to LayoutLoaded to ensure scripts run after layout is injected
        s = s.replace("document.addEventListener('DOMContentLoaded'", "document.addEventListener('LayoutLoaded'")
        kept_scripts.append(s)
        
    scripts_html = '\n    '.join(kept_scripts)
    
    filepath_unix = filepath.replace('\\\\', '/')
    is_root = 'frontend/login.html' in filepath_unix or 'frontend/register.html' in filepath_unix or 'frontend/index.html' in filepath_unix
    prefix = '' if is_root else '../'
    
    new_html = f'''<!DOCTYPE html>
<html lang="en" class="light">
<head>
    <script src="{prefix}js/core.js"></script>
</head>
<body data-layout="{layout_type}" data-page-title="{title}">
{main_html}
{scripts_html}
</body>
</html>'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return True

for root, _, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.html') and 'components' not in root:
            fp = os.path.join(root, f)
            if 'student' in root:
                layout = 'student'
            elif 'management' in root:
                layout = 'management'
            else:
                layout = 'auth'
            
            print(f"Refactoring {fp} with layout {layout}...")
            refactor_file(fp, layout)

