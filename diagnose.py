#!/usr/bin/env python3
"""
Diagnostic script to check FIDEAS API server status
"""
import socket
import os
from dotenv import load_dotenv

load_dotenv()

def check_port(host, port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def main():
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print("=== FIDEAS API Diagnostics ===")
    print(f"Configured Host: {host}")
    print(f"Configured Port: {port}")
    print()
    
    # Check if port is open
    print("1. Checking if port is open...")
    if check_port("localhost", port):
        print(f"[OK] Port {port} is open on localhost")
    else:
        print(f"[FAIL] Port {port} is NOT open on localhost")
    
    if check_port("127.0.0.1", port):
        print(f"[OK] Port {port} is open on 127.0.0.1")
    else:
        print(f"[FAIL] Port {port} is NOT open on 127.0.0.1")
    
    print()
    
    # Check common ports
    print("2. Checking common ports...")
    common_ports = [8000, 8080, 3000, 5000]
    for test_port in common_ports:
        if check_port("localhost", test_port):
            print(f"[OK] Port {test_port} is open")
        else:
            print(f"[CLOSED] Port {test_port} is closed")
    
    print()
    print("3. Recommendations:")
    if not check_port("localhost", port):
        print(f"- The API server doesn't appear to be running on port {port}")
        print(f"- Try starting the server with: python main.py")
        print(f"- Check if another process is using port {port}")
        print(f"- Try accessing: http://localhost:{port} or http://127.0.0.1:{port}")
    else:
        print(f"- Server appears to be running on port {port}")
        print(f"- Try accessing: http://localhost:{port}")
        print(f"- API docs should be at: http://localhost:{port}/docs")

if __name__ == "__main__":
    main()