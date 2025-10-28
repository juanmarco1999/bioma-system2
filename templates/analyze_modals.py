import re

# Read the HTML file
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by lines
lines = content.split('\n')

# Find all Swal.fire and SafeSwal.fire calls with their line numbers
results = {
    'excellent': [],
    'good': [],
    'basic': [],
    'poor': [],
    'special': []
}

# Pattern to find Swal.fire calls
swal_pattern = r'(Swal|SafeSwal)\.fire\s*\('

current_modal = None
modal_start_line = 0
modal_content = []
in_modal = False

for idx, line in enumerate(lines, 1):
    if re.search(swal_pattern, line):
        if in_modal and modal_content:
            # Process previous modal
            process_modal(modal_start_line, ''.join(modal_content))
            modal_content = []
        
        modal_start_line = idx
        in_modal = True
        modal_content.append(line)
    elif in_modal:
        modal_content.append(line)
        # Check if modal ends (looking for closing parenthesis at root level)
        if ')' in line and not any(c in line for c in ['({', '(',]):
            in_modal = False

print("Total lines analyzed:", len(lines))
