from http.server import BaseHTTPRequestHandler, HTTPServer
import json, re, time, uuid
messages={}
class H(BaseHTTPRequestHandler):
 def send(self,code=200,data=None):
  raw=json.dumps(data or {}).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,DELETE,OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers(); self.wfile.write(raw)
 def do_OPTIONS(self): self.send(204)
 def do_POST(self):
  m=re.match(r'/relay/([\w-]+)$',self.path)
  if not m:return self.send(404)
  n=int(self.headers.get('Content-Length',0)); messages[m.group(1)]={'body':self.rfile.read(n).decode(),'at':time.time()}; self.send(201,{'ok':True})
 def do_GET(self):
  m=re.match(r'/relay/([\w-]+)$',self.path)
  if not m:return self.send(404)
  x=messages.pop(m.group(1),None); self.send(200,x or {})
 def do_DELETE(self):
  m=re.match(r'/relay/([\w-]+)$',self.path)
  if m: messages.pop(m.group(1),None)
  self.send(200,{'ok':True})
HTTPServer(('0.0.0.0',8765),H).serve_forever()
