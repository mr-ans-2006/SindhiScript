import http.server
import socketserver
import json
import sys
import os
import io
import threading
import queue
import urllib.parse
import uuid
import builtins

# Import SindhiScript core
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from سنڌي.lexer import tokenize
from سنڌي.parser import Parser
from سنڌي.evaluator import Evaluator
from سنڌي.errors import SindhiError

PORT = 5000

# Global state for runs
active_runs = {}

class CustomOutput(io.StringIO):
    def __init__(self, run_id, key):
        super().__init__()
        self.run_id = run_id
        self.key = key
        
    def write(self, string):
        if self.run_id in active_runs:
            active_runs[self.run_id][self.key] += string
        super().write(string)

def run_code_thread(run_id, source_code):
    run_state = active_runs[run_id]
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = CustomOutput(run_id, 'stdout')
    sys.stderr = CustomOutput(run_id, 'stderr')
    
    old_input = builtins.input
    def custom_input(prompt_text=""):
        # Print prompt to stdout
        if prompt_text:
            print(prompt_text, end='', flush=True)
            
        run_state['input_prompt'] = prompt_text
        run_state['status'] = 'waiting_input'
        
        # Wait for input from frontend
        try:
            user_input = run_state['input_queue'].get(timeout=300) # 5 min timeout
            print(user_input) # Echo input to terminal
            return user_input
        except queue.Empty:
            raise KeyboardInterrupt("Input timeout")
            
    builtins.input = custom_input
    
    try:
        tokens = tokenize(source_code, "web.سن")
        parser = Parser(tokens, "web.سن")
        ast = parser.parse()
        evaluator = Evaluator()
        evaluator.interpret(ast)
    except SindhiError as e:
        print(e, file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[روڪيو ويو - Interrupted]", file=sys.stderr)
    except Exception as e:
        print(f"اندروني غلطي: {e}", file=sys.stderr)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        builtins.input = old_input
        run_state['status'] = 'finished'

class WebIDEHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('web_ide.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path.startswith('/poll'):
            parsed_path = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed_path.query)
            run_id = query.get('run_id', [''])[0]
            
            if run_id in active_runs:
                state = active_runs[run_id]
                response = {
                    "status": state['status'],
                    "stdout": state['stdout'],
                    "stderr": state['stderr'],
                    "input_prompt": state['input_prompt']
                }
                # Clear read output so we only send deltas
                state['stdout'] = ''
                state['stderr'] = ''
                
                # Cleanup finished runs
                if state['status'] == 'finished':
                    del active_runs[run_id]
            else:
                response = {"status": "not_found"}
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/run':
            content_length = int(self.headers['Content-Length'])
            source_code = self.rfile.read(content_length).decode('utf-8')
            
            run_id = str(uuid.uuid4())
            active_runs[run_id] = {
                'status': 'running',
                'stdout': '',
                'stderr': '',
                'input_prompt': None,
                'input_queue': queue.Queue()
            }
            
            t = threading.Thread(target=run_code_thread, args=(run_id, source_code), daemon=True)
            t.start()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"run_id": run_id}).encode('utf-8'))
            
        elif self.path == '/input':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            run_id = data.get('run_id')
            user_input = data.get('input', '')
            
            if run_id in active_runs:
                active_runs[run_id]['status'] = 'running'
                active_runs[run_id]['input_prompt'] = None
                active_runs[run_id]['input_queue'].put(user_input)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Disable default HTTP logging to keep terminal clean
        pass

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), WebIDEHandler) as httpd:
        print(f"Web IDE Server running on http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
