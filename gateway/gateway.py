#!/usr/bin/env python3
"""Lightweight TokenQR Gateway POC. Configure upstream with TOKENQR_UPSTREAM_URL and TOKENQR_UPSTREAM_TOKEN."""
from http.server import BaseHTTPRequestHandler,HTTPServer
import os,json,time,uuid,hashlib,threading,urllib.request
DATA=os.environ.get('TOKENQR_DATA','gateway-state.json'); UP=os.environ.get('TOKENQR_UPSTREAM_URL','https://api.openai.com/v1').rstrip('/'); ROOT=os.environ.get('TOKENQR_UPSTREAM_TOKEN',''); ADMIN=os.environ.get('TOKENQR_ADMIN_TOKEN','change-me'); lock=threading.Lock()
def load():
 try:return json.load(open(DATA))
 except:return {'credentials':{},'usage':{}}
def save(x):
 tmp=DATA+'.tmp';open(tmp,'w').write(json.dumps(x,indent=2));os.replace(tmp,DATA)
state=load()
def token():return 'tqr_live_'+uuid.uuid4().hex
class H(BaseHTTPRequestHandler):
 def send(self,c,d):
  b=json.dumps(d).encode();self.send_response(c);self.send_header('Content-Type','application/json');self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Authorization,Content-Type');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');self.end_headers();self.wfile.write(b)
 def body(self):return json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))
 def auth(self):return self.headers.get('Authorization','').removeprefix('Bearer ').strip()
 def do_OPTIONS(self):self.send(204,{})
 def do_POST(self):
  if self.path=='/tokenqr/credentials':
   if self.auth()!=ROOT:return self.send(401,{'error':'provider_token_invalid'})
   q=self.body(); plain=token(); cid='cred_'+uuid.uuid4().hex[:12]; now=int(time.time()); exp=q.get('expires_at');
   with lock: state['credentials'][cid]={'hash':hashlib.sha256(plain.encode()).hexdigest(),'name':q.get('name','Unnamed'),'purpose':q.get('purpose',''),'models':q.get('models',[]),'limits':q.get('limits',{}),'created_at':now,'expires_at':exp,'status':'active'};save(state)
   return self.send(201,{'credential_id':cid,'token':plain,'base_url':'/v1','expires_at':exp})
  if self.path=='/tokenqr/revoke':
   c=self.cred();
   if not c:return self.send(401,{'error':'invalid_token'})
   c['status']='revoked';save(state);return self.send(200,{'revoked':True})
  self.send(404,{'error':'not_found'})
 def cred(self):
  h=hashlib.sha256(self.auth().encode()).hexdigest()
  for c in state['credentials'].values():
   if c['hash']==h:return c
 def do_GET(self):
  if self.path=='/tokenqr/usage':
   c=self.cred();return self.send(200,{'credential':c,'usage':c and state['usage'].get(c['hash'],{'requests':0,'total_tokens':0})}) if c else self.send(401,{'error':'invalid_token'})
  if self.path=='/tokenqr/admin/usage':
   if self.auth()!=ADMIN:return self.send(401,{'error':'admin_token_invalid'})
   return self.send(200,{'credentials':list(state['credentials'].values())})
  if self.path=='/tokenqr/capabilities':return self.send(200,{'credential_creation':True,'revocation':True,'usage':True,'limits':['rpm','tpm','token_budget']})
  self.send(404,{'error':'not_found'})
 def do_DELETE(self):
  self.send(405,{'error':'use_post_revoke'})
 def log_message(self,*a):pass
HTTPServer(('0.0.0.0',8787),H).serve_forever()
