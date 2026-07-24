import os
import sys
import yaml
import json
from datetime import datetime
import subprocess

def run_cmd(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()

def get_pr_files():
    cmd = f"gh pr view {os.environ['PR_NUMBER']} --json files"
    stdout, _ = run_cmd(cmd)
    return json.loads(stdout)['files']

def validate_yaml_file(file_path):
    errors = []
    
    # Check filename
    if file_path.endswith('my-site.yml'):
        errors.append("❌ Cannot use default filename 'my-site.yml'")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        # Check required fields
        required_fields = ['title', 'url', 'tags', 'created_at']
        for field in required_fields:
            if field not in data:
                errors.append(f"❌ Missing required field: {field}")
        
        # Check title is not default
        if 'title' in data and data['title'] in ["Site Name", "Your Site Name"]:
            errors.append("❌ Cannot use default title 'Site Name' or 'Your Site Name'")
        
        # Check URL format
        if 'url' in data and not data['url'].startswith(('http://', 'https://')):
            errors.append("❌ URL must start with http:// or https://")
        
        # Check tags
        if 'tags' in data:
            if not isinstance(data['tags'], list):
                errors.append("❌ Tags must be a list")
            elif len(data['tags']) == 0:
                errors.append("❌ Tags cannot be empty")
        
        # Check creation date
        if 'created_at' in data:
            try:
                datetime.strptime(str(data['created_at']), '%Y-%m-%d')
            except ValueError:
                errors.append("❌ created_at must use YYYY-MM-DD format")
                
    except yaml.YAMLError as e:
        errors.append(f"❌ YAML format error: {str(e)}")
    except Exception as e:
        errors.append(f"❌ Validation error: {str(e)}")
    
    return errors

def main():
    pr_files = get_pr_files()
    all_valid = True
    comment_body = []
    
    for file in pr_files:
        if not file['path'].startswith('sites/'):
            continue
            
        errors = validate_yaml_file(file['path'])
        
        if errors:
            all_valid = False
            comment_body.extend([
                f"### Validation Results for {file['path']}:",
                *errors,
                ""
            ])
    
    if comment_body:
        comment = "\n".join(comment_body)
        cmd = f'gh pr comment {os.environ["PR_NUMBER"]} --body "{comment}"'
        run_cmd(cmd)
    
    # Set output variable for GitHub Actions using GITHUB_OUTPUT
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"is_valid={str(all_valid).lower()}\n")
    
    if not all_valid:
        sys.exit(1)

if __name__ == '__main__':
    main()
