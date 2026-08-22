import urllib.request
import urllib.parse
import json
import time
import sys
import subprocess

client_id = "de82576096a840d47eb3"  # Preconfigured client ID
repo_name = "rooman-ai-resume-screener"
local_repo_dir = r"C:\Users\Dell\.gemini\antigravity\scratch\resume-screener"

def run_cmd(args, cwd=None):
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise Exception(f"Command {' '.join(args)} failed: {res.stderr}")
    return res.stdout.strip()

def main():
    print("Step 1: Requesting device code from GitHub...")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "scope": "repo"
    }).encode("utf-8")
    
    req = urllib.request.Request("https://github.com/login/device/code", data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error requesting device code: {e}")
        return

    device_code = res.get("device_code")
    user_code = res.get("user_code")
    verification_uri = res.get("verification_uri")
    interval = res.get("interval", 5)
    expires_in = res.get("expires_in", 900)

    print("\n" + "="*60)
    print(" ACTION REQUIRED: AUTHENTICATE GITHUB")
    print("="*60)
    print(f"1. Open your browser and go to: {verification_uri}")
    print(f"2. Enter the following code: {user_code}")
    print("="*60)
    print("Polling for authentication status... Please authenticate in your browser.\n")

    # Step 2: Poll for access token
    token = None
    start_time = time.time()
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        poll_data = urllib.parse.urlencode({
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }).encode("utf-8")
        
        poll_req = urllib.request.Request("https://github.com/login/oauth/access_token", data=poll_data, headers=headers)
        try:
            with urllib.request.urlopen(poll_req) as response:
                poll_res = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"Polling error: {e}")
            continue

        if "error" in poll_res:
            err = poll_res["error"]
            if err == "authorization_pending":
                continue
            elif err == "slow_down":
                interval += 5
                continue
            else:
                print(f"Authentication failed: {poll_res.get('error_description', err)}")
                return
        
        token = poll_res.get("access_token")
        if token:
            print("[+] Successfully authenticated with GitHub!")
            break

    if not token:
        print("[!] Authentication timed out.")
        return

    # Step 3: Get User Details
    print("\nStep 2: Fetching user profile info...")
    user_req = urllib.request.Request(
        "https://api.github.com/user", 
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(user_req) as response:
            user_info = json.loads(response.read().decode("utf-8"))
        username = user_info.get("login")
        print(f"[+] Authenticated as GitHub user: {username}")
    except Exception as e:
        print(f"Failed to fetch user details: {e}")
        return

    # Step 4: Create Repository
    print(f"\nStep 3: Creating repository '{repo_name}' on GitHub...")
    create_data = json.dumps({
        "name": repo_name,
        "description": "AI Resume Screening Agent for Rooman selection round",
        "private": False,
        "auto_init": False
    }).encode("utf-8")
    
    create_req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=create_data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(create_req) as response:
            repo_info = json.loads(response.read().decode("utf-8"))
        clone_url = repo_info.get("clone_url")
        html_url = repo_info.get("html_url")
        print(f"[+] Repository created successfully: {html_url}")
    except urllib.error.HTTPError as e:
        # Check if repo already exists (422 status code)
        if e.code == 422:
            print(f"[*] Repository '{repo_name}' already exists. We will push updates directly.")
            html_url = f"https://github.com/{username}/{repo_name}"
        else:
            print(f"Failed to create repository: {e.code} - {e.reason}")
            try:
                print("Details:", e.read().decode('utf-8'))
            except:
                pass
            return
    except Exception as e:
        print(f"Failed to create repository: {e}")
        return

    # Step 5: Push local repo to remote
    print("\nStep 4: Setting remote URL and pushing to GitHub...")
    try:
        # Configure remote origin to use token
        remote_url_with_token = f"https://x-access-token:{token}@github.com/{username}/{repo_name}.git"
        
        # Check if remote origin already exists
        remotes = run_cmd(["git", "remote"], cwd=local_repo_dir)
        if "origin" in remotes.split():
            run_cmd(["git", "remote", "set-url", "origin", remote_url_with_token], cwd=local_repo_dir)
        else:
            run_cmd(["git", "remote", "add", "origin", remote_url_with_token], cwd=local_repo_dir)
            
        print("[*] Pushing 'main' branch to remote origin...")
        run_cmd(["git", "push", "-u", "origin", "main", "--force"], cwd=local_repo_dir)
        print("[+] Code successfully pushed to GitHub!")
        
        # Clean up remote URL to hide token
        clean_remote_url = f"https://github.com/{username}/{repo_name}.git"
        run_cmd(["git", "remote", "set-url", "origin", clean_remote_url], cwd=local_repo_dir)
        
        print("\n" + "="*60)
        print(" SUCCESS: PROJECT IS NOW LIVE ON GITHUB")
        print("="*60)
        print(f"Repository URL: {html_url}")
        print("="*60)
        
    except Exception as e:
        print(f"Error during push process: {e}")

if __name__ == "__main__":
    main()
