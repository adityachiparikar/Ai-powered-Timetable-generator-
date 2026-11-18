
import os

env_path = 'backend/.env'
new_lines = []

with open(env_path, 'r') as f:
    lines = f.readlines()

uri_set = False

for line in lines:
    line = line.strip()
    if not line:
        continue
        
    if line.startswith('SQLALCHEMY_DATABASE_URI'):
        new_lines.append('SQLALCHEMY_DATABASE_URI=sqlite:///./timetable.db\n')
        uri_set = True
    elif line.startswith('POSTGRES'):
        new_lines.append('# ' + line + '\n')
    elif 'postgresql://' in line:
        # Catch stray appended config
        pass 
    else:
        new_lines.append(line + '\n')

if not uri_set:
    new_lines.append('SQLALCHEMY_DATABASE_URI=sqlite:///./timetable.db\n')

with open(env_path, 'w') as f:
    f.writelines(new_lines)

print("Successfully successfully sanitized .env file.")
