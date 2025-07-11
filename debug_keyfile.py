#!/usr/bin/env python3

import subprocess
import sys

def test_keyfile_auth(db_path, key_file_path, password):
    """Test key file authentication manually"""
    
    # Test without key file
    print("=== Testing without key file ===")
    cmd1 = ["keepassxc-cli", "ls", "-q", db_path]
    print(f"Command: {' '.join(cmd1)}")
    
    try:
        proc1 = subprocess.run(
            cmd1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=bytes(password, "utf-8"),
            check=False,
        )
        print(f"Return code: {proc1.returncode}")
        print(f"Stdout: {proc1.stdout.decode('utf-8')}")
        print(f"Stderr: {proc1.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Testing with key file ===")
    cmd2 = ["keepassxc-cli", "ls", "-q", "-k", key_file_path, db_path]
    print(f"Command: {' '.join(cmd2)}")
    
    try:
        proc2 = subprocess.run(
            cmd2,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=bytes(password, "utf-8"),
            check=False,
        )
        print(f"Return code: {proc2.returncode}")
        print(f"Stdout: {proc2.stdout.decode('utf-8')}")
        print(f"Stderr: {proc2.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Testing with key file (no quiet flag) ===")
    cmd3 = ["keepassxc-cli", "ls", "-k", key_file_path, db_path]
    print(f"Command: {' '.join(cmd3)}")
    
    try:
        proc3 = subprocess.run(
            cmd3,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=bytes(password, "utf-8"),
            check=False,
        )
        print(f"Return code: {proc3.returncode}")
        print(f"Stdout: {proc3.stdout.decode('utf-8')}")
        print(f"Stderr: {proc3.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Testing with key file (different order) ===")
    cmd4 = ["keepassxc-cli", "-k", key_file_path, "ls", "-q", db_path]
    print(f"Command: {' '.join(cmd4)}")
    
    try:
        proc4 = subprocess.run(
            cmd4,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=bytes(password, "utf-8"),
            check=False,
        )
        print(f"Return code: {proc4.returncode}")
        print(f"Stdout: {proc4.stdout.decode('utf-8')}")
        print(f"Stderr: {proc4.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python debug_keyfile.py <db_path> <key_file_path> <password>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    key_file_path = sys.argv[2]
    password = sys.argv[3]
    
    test_keyfile_auth(db_path, key_file_path, password) 