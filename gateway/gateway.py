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
  if self.path=='/v1/chat/completions':
   c=self.cred()
   if not c or c.get('status')!='active': return self.send(401,{'error':'invalid_token'})
   if c.get('expires_at') and str(c['expires_at']) < str(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())): c['status']='expired'; save(state); return self.send(401,{'error':'expired'})
   q=self.body(); model=q.get('model'); allowed=c.get('models') or []
   if allowed and model not in allowed:return self.send(403,{'error':'model_not_allowed','allowed_models':allowed})
   usage=state['usage'].setdefault(c['hash'],{'requests':0,'total_tokens':0}); lim=c.get('limits',{})
   if lim.get('rpm') and usage.get('minute',0)>=lim['rpm']:return self.send(429,{'error':'rpm_limit'})
   if lim.get('token_budget') and usage['total_tokens']>=lim['token_budget']:return self.send(429,{'error':'token_budget_exhausted'})
   req=urllib.request.Request(UP+'/chat/completions',data=json.dumps(q).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+ROOT})
   try:
    with urllib.request.urlopen(req,timeout=120) as r: out=json.loads(r.read())
   except Exception as e:return self.send(502,{'error':'upstream_error','detail':str(e)})
   u=out.get('usage',{}); n=int(u.get('total_tokens',0)); usage['requests']+=1;usage['total_tokens']+=n;usage['minute']=usage.get('minute',0)+1;save(state);return self.send(200,out)
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
