import uvicorn
from silero_api_server.server import app
import argparse

parser = argparse.ArgumentParser(
    prog='silero_api_server',
    description='Run Silero within a FastAPI application'
)

parser.add_argument('-o', '--host', action='store', dest='host', default='0.0.0.0')
parser.add_argument('-p', '--port', action='store', dest='port', type=int, default=8001)
parser.add_argument('-s', '--session_path', action='store', dest='session_path', type=str, default="sessions")
parser.add_argument('-r', '--reload', action='store_true', dest='reload', help='Enable automatic reloading on file change')

args = parser.parse_args()

if help not in args:
    uvicorn.run("silero_api_server.server:app", host=args.host, port=args.port, reload=args.reload)