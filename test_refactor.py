import os
import re

def refactor_file(filepath, layout_type):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract Title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else "HostelOS"
    
    # Extract Main Content
    if layout_type == 'student':
        # Everything inside <main ...> and </main>
        main_match = re.search(r'<main[^>]*>(.*?)</main>', content, re.DOTALL)
    elif layout_type == 'management':
        # Inside <div class="... custom-scrollbar"> where the content lives
        # A bit trickier. Let's look for the main content area.
        # It's usually after <header> and inside a <div class="flex-1 overflow-auto ...">
        main_match = re.search(r'<header.*?</header>.*?<div[^>]*custom-scrollbar[^>]*>(.*?)</div>\s*</main>', content, re.DOTALL)
        if not main_match:
            main_match = re.search(r'<main[^>]*>.*?<header.*?</header>.*?<div[^>]*>(.*?)</div>\s*</main>', content, re.DOTALL)
    else:
        # auth pages etc
        main_match = None

    if not main_match:
        return False
        
    main_html = main_match.group(1).strip()
    
    # Remove wrappers inside student main if they exist (like max-w-5xl mx-auto)
    # Actually, layout.js already adds max-w-5xl mx-auto space-y-8 for student.
    # Let's not double wrap if we can help it, but it's safer to just take whatever is in main.
    
    # Extract Scripts at the bottom
    # We want to extract <script> blocks that do NOT src theme.js, auth.js, utils.js, tailwind, etc.
    script_blocks = re.findall(r'(<script[^>]*>.*?</script>)', content, re.DOTALL)
    
    kept_scripts = []
    for s in script_blocks:
        if 'src=' in s and ('tailwindcss' in s or 'lucide' in s or 'theme.js' in s or 'auth.js' in s or 'utils.js' in s or 'components.js' in s or 'layout.js' in s or 'app.js' in s or 'api.js' in s):
            continue
        kept_scripts.append(s)
        
    scripts_html = '\n    '.join(kept_scripts)
    
    # Check if this is root
    is_root = 'frontend/login.html' in filepath.replace('\\\\', '/') or 'frontend/index.html' in filepath.replace('\\\\', '/')
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

refactor_file('frontend/student/dashboard.html', 'student')
