
import requests
import urllib3
import socket

def test_connection():
    url = 'https://en.wikipedia.org'
    print(f"Testing connection to {url}")
    print("DNS Lookup test...")
    
    try:
        # First test DNS resolution
        ip = socket.gethostbyname('en.wikipedia.org')
        print(f"DNS Resolution successful. IP: {ip}")
        
        # Then test HTTPS connection
        print("\nHTTPS Connection test...")
        response = requests.get(url, verify=True)
        print(f"Connection successful!")
        print(f"Status code: {response.status_code}")
        print(f"Response time: {response.elapsed.total_seconds():.2f} seconds")
        
    except socket.gaierror as e:
        print(f"DNS lookup failed: {e}")
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
    except Exception as e:
        print(f"Other error occurred: {e}")

if __name__ == "__main__":
    test_connection()