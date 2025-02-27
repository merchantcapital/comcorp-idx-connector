import sys
import os
import traceback

# Print debug information
print("Starting wsgi.py", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
print(f"Files in current directory: {os.listdir('.')}", file=sys.stderr)
print(f"Files in app directory: {os.listdir('app')}", file=sys.stderr)
print(f"Files in config directory: {os.listdir('config')}", file=sys.stderr)
print(f"Files in certs directory: {os.listdir('certs')}", file=sys.stderr)
print(f"Files in wsdl directory: {os.listdir('wsdl')}", file=sys.stderr)
print(f"Environment variables: {dict(os.environ)}", file=sys.stderr)

try:
    print("Importing app...", file=sys.stderr)
    from app import app
    print("App imported successfully!", file=sys.stderr)
except Exception as e:
    print(f"Error importing app: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise

if __name__ == "__main__":
    app.run()