import os
import subprocess
import requests
import time
from pathlib import Path
import shutil

# ============================================
# STEP 1: CONFIGURE YOUR SETTINGS (EDIT THESE)
# ============================================

# Your GitHub username
GITHUB_USERNAME = "mohas2p2"
#GITHUB_USERNAME = "yukayare36-arch"  # CHANGE THIS

# Your GitHub Personal Access Token (create one at https://github.com/settings/tokens)
# Give it "repo" permissions
#GITHUB_TOKEN = "" #YUKAYARE36
#GITHUB_TOKEN = "" wiilkawiilasha7
GITHUB_TOKEN = ""

# The folder where your Python files are located
FILES_FOLDER = r"C:\Users\mss happy\Downloads\run1"  # CHANGE THIS

# Your Git user info (MUST FILL THIS IN)
GIT_USER_NAME = "mohas2p2"  # Your GitHub username
GIT_USER_EMAIL = "suphonestex+kgujq@gmail.com"  # Your GitHub email - CHANGE THIS!

# What number to start from (since you have up to run61)
START_FROM = 388  # This will create run67, run68, run69, etc.

# How many repositories to create
HOW_MANY = 1500  # CHANGE THIS - how many repos you want

# Clean up local folders after successful push (True = delete, False = keep)
CLEANUP_LOCAL = True  # CHANGE THIS - set to False if you want to keep local folders

# ============================================
# STEP 2: THE SCRIPT (DON'T CHANGE ANYTHING BELOW)
# ============================================

def print_step(step_number, message):
    """Helper function to show progress nicely"""
    print("=" * 60)
    print(f"✅ STEP {step_number}: {message}")
    print("=" * 60)

def setup_git_config():
    """Setup Git user configuration"""
    try:
        # Set global git config for this session
        subprocess.run(["git", "config", "--global", "user.name", GIT_USER_NAME], check=True, capture_output=True)
        subprocess.run(["git", "config", "--global", "user.email", GIT_USER_EMAIL], check=True, capture_output=True)
        print("   ✅ Git configured with your username and email")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not set git config: {e}")
        return False

def create_github_repo_with_retry(repo_name, username, token, max_retries=5):
    """Create a repository on GitHub using the API with retry logic"""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "private": False,  # Change to True if you want private repos
        "auto_init": False
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   📝 Creating repository: {repo_name}... (Attempt {attempt}/{max_retries})")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                print(f"   ✅ Repository {repo_name} created successfully!")
                return True, None
            elif response.status_code == 422:
                print(f"   ⚠️  Repository {repo_name} already exists, skipping...")
                return True, None  # Return True so we can still push to existing repo
            elif response.status_code == 403:
                # Rate limit hit
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(reset_time - time.time(), 30)
                print(f"   ⚠️  Rate limit hit. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                continue
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                print(f"   ❌ Error creating {repo_name}: {error_msg}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt * 5  # Exponential backoff
                    print(f"   🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return False, error_msg
                    
        except requests.exceptions.ConnectionError as e:
            print(f"   ⚠️  Connection error (attempt {attempt}/{max_retries}): {str(e)[:100]}")
            if attempt < max_retries:
                wait_time = 2 ** attempt * 10  # Exponential backoff
                print(f"   🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return False, f"Connection error: {str(e)[:100]}"
                
        except requests.exceptions.Timeout as e:
            print(f"   ⚠️  Timeout error (attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                wait_time = 2 ** attempt * 5
                print(f"   🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return False, f"Timeout error: {str(e)[:100]}"
                
        except Exception as e:
            print(f"   ❌ Unexpected error (attempt {attempt}/{max_retries}): {str(e)[:100]}")
            if attempt < max_retries:
                wait_time = 2 ** attempt * 5
                print(f"   🔄 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return False, f"Unexpected error: {str(e)[:100]}"
    
    return False, "Max retries exceeded"

def push_files_to_repo_with_retry(repo_name, file_path, username, token, max_retries=3):
    """Initialize git, add files, and push to GitHub with retry logic"""
    
    # Create a temporary folder for this repo
    repo_folder = os.path.join(os.getcwd(), repo_name)
    os.makedirs(repo_folder, exist_ok=True)
    
    # Change to the repo folder
    original_dir = os.getcwd()
    os.chdir(repo_folder)
    
    try:
        # Copy the Python file to the repo folder
        if os.path.exists(file_path):
            dest_file = os.path.join(repo_folder, f"{repo_name}.py")
            
            # Copy the file
            shutil.copy2(file_path, dest_file)
            print(f"   📄 Copied {os.path.basename(file_path)} as {repo_name}.py")
        else:
            print(f"   ❌ File not found: {file_path}")
            os.chdir(original_dir)
            return False, "Source file not found"
        
        # Initialize git
        print("   🔧 Initializing git...")
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Create a .gitignore file
        with open(".gitignore", "w") as f:
            f.write("__pycache__/\n*.pyc\n.DS_Store\n")
        
        # Create a simple README
        with open("README.md", "w") as f:
            f.write(f"# {repo_name}\n\nThis repository contains {repo_name}.py\n")
        
        # Add all files
        print("   📦 Adding files...")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # Commit - using the user info we set globally
        print("   💾 Committing...")
        subprocess.run(
            ["git", "commit", "-m", f"Initial commit for {repo_name}"],
            check=True,
            capture_output=True
        )
        
        # Set the branch to main
        subprocess.run(["git", "branch", "-M", "main"], check=True, capture_output=True)
        
        # Add remote
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            check=True,
            capture_output=True
        )
        
        # Push to GitHub with retry
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   🚀 Pushing to GitHub... (Attempt {attempt}/{max_retries})")
                result = subprocess.run(
                    ["git", "push", "-u", "origin", "main"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Successfully pushed {repo_name} to GitHub!")
                    return True, None
                else:
                    error_msg = result.stderr[:200]
                    print(f"   ❌ Push failed (attempt {attempt}): {error_msg}")
                    if attempt < max_retries:
                        wait_time = 2 ** attempt * 5
                        print(f"   🔄 Retrying push in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return False, error_msg
                        
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Push timeout (attempt {attempt})")
                if attempt < max_retries:
                    wait_time = 2 ** attempt * 5
                    print(f"   🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return False, "Push timeout"
        
        return False, "Max retries exceeded for push"
            
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        print(f"   ❌ Git error: {error_msg[:200]}")
        return False, error_msg
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return False, str(e)
    finally:
        # Go back to original directory
        os.chdir(original_dir)
        # Clean up the repo folder if it exists
        # try:
        #     shutil.rmtree(repo_folder)
        # except:
        #     pass

def cleanup_local_folder(repo_name, repo_folder):
    """Clean up the local repository folder after successful push"""
    try:
        if os.path.exists(repo_folder):
            print(f"   🧹 Cleaning up local folder: {repo_name}...")
            shutil.rmtree(repo_folder)
            print(f"   ✅ Successfully removed local folder for {repo_name}")
            return True
        else:
            print(f"   ⚠️  Local folder for {repo_name} not found, nothing to clean")
            return False
    except Exception as e:
        print(f"   ❌ Failed to clean up {repo_name}: {str(e)[:200]}")
        return False

def main():
    """Main function to run everything"""
    
    print("\n" + "=" * 60)
    print("🚀 GITHUB REPO CREATOR & UPLOADER (WITH RETRY LOGIC)")
    print("=" * 60)
    print("\n📋 Your settings:")
    print(f"   • GitHub Username: {GITHUB_USERNAME}")
    print(f"   • Git Email: {GIT_USER_EMAIL}")
    print(f"   • Starting from: run{START_FROM}")
    print(f"   • Number of repos: {HOW_MANY}")
    print(f"   • Files folder: {FILES_FOLDER}")
    print(f"   • Cleanup local folders: {CLEANUP_LOCAL}")
    print("\n" + "=" * 60)
    
    # Setup Git configuration
    print("\n🔧 Setting up Git configuration...")
    if not setup_git_config():
        print("⚠️  Continuing anyway...")
    
    # Check if the files folder exists
    if not os.path.exists(FILES_FOLDER):
        print(f"\n❌ ERROR: Folder not found: {FILES_FOLDER}")
        print("Please fix the FILES_FOLDER path in the script")
        return
    
    # Check if we have a file to copy (run1.py as base)
    source_file = os.path.join(FILES_FOLDER, "run1.py")
    if not os.path.exists(source_file):
        print(f"\n❌ ERROR: run1.py not found in {FILES_FOLDER}")
        print("Please make sure run1.py exists in your files folder")
        return
    
    # Create a list of repo names
    repo_names = [f"run{i}" for i in range(START_FROM, START_FROM + HOW_MANY)]
    
    print(f"\n📝 Will create these repositories: {repo_names[0]} to {repo_names[-1]}")
    print("\n⏳ Starting process...\n")
    
    success_count = 0
    fail_count = 0
    failed_repos = []
    cleaned_count = 0
    
    for i, repo_name in enumerate(repo_names, 1):
        print(f"\n🔹 [{i}/{len(repo_names)}] Processing {repo_name}")
        print("-" * 40)
        
        # Step 1: Create repo on GitHub with retry
        repo_created, error_msg = create_github_repo_with_retry(repo_name, GITHUB_USERNAME, GITHUB_TOKEN)
        
        if repo_created:
            # Step 2: Push files with retry
            push_success, push_error = push_files_to_repo_with_retry(repo_name, source_file, GITHUB_USERNAME, GITHUB_TOKEN)
            if push_success:
                success_count += 1
                
                # Clean up local folder if enabled
                if CLEANUP_LOCAL:
                    repo_folder = os.path.join(os.getcwd(), repo_name)
                    if cleanup_local_folder(repo_name, repo_folder):
                        cleaned_count += 1
            else:
                fail_count += 1
                failed_repos.append((repo_name, f"Push failed: {push_error}"))
                print(f"   ❌ Failed to push {repo_name} - continuing with next repo")
        else:
            fail_count += 1
            failed_repos.append((repo_name, f"Repo creation failed: {error_msg}"))
            print(f"   ❌ Failed to create {repo_name} - continuing with next repo")
        
        # Wait a bit to avoid rate limiting
        if i < len(repo_names):
            # Increase wait time if there were failures to avoid rate limits
            wait_time = 45  # Increased from 40 to be safer
            print(f"   ⏳ Waiting {wait_time} seconds before next repo...")
            time.sleep(wait_time)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully created: {success_count} repositories")
    print(f"🧹 Local folders cleaned: {cleaned_count}")
    print(f"❌ Failed: {fail_count} repositories")
    print(f"📁 Total processed: {len(repo_names)} repositories")
    
    if failed_repos:
        print("\n⚠️  Failed repositories:")
        for repo_name, error in failed_repos[:10]:  # Show first 10 failures
            print(f"   • {repo_name}: {error[:150]}")
        if len(failed_repos) > 10:
            print(f"   ... and {len(failed_repos) - 10} more failures")
    
    if success_count > 0:
        print("\n🎉 All done! Check your GitHub: https://github.com/" + GITHUB_USERNAME)
    
    # Save failed repos to a file for later retry
    if failed_repos:
        with open("failed_repos.txt", "w") as f:
            f.write(f"Failed repositories from run {START_FROM} to {START_FROM + HOW_MANY - 1}\n")
            f.write("=" * 60 + "\n")
            for repo_name, error in failed_repos:
                f.write(f"{repo_name}\t{error}\n")
        print(f"\n📄 Failed repositories saved to 'failed_repos.txt'")
    
    print("=" * 60)

if __name__ == "__main__":
    main()