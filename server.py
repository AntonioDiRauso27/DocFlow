"""Standard-library local HTTP server and double-click launcher."""
from __future__ import annotations
import argparse, email.policy, json, os, secrets, subprocess, sys, tempfile, threading, time, urllib.request, webbrowser
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from docflow import DEFAULT_CLIENTS, MAX_BYTES, MAX_FILES, analyze_batch, create_archive
BASE=Path(__file__).parent

def data_dir():
    if os.environ.get('DOCFLOW_DATA'):return Path(os.environ['DOCFLOW_DATA'])
    if sys.platform=='darwin':return Path.home()/'Library'/'Application Support'/'DocFlow Demo'
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'DocFlow Demo'

def run_server(port=0):
    directory=data_dir();directory.mkdir(parents=True,exist_ok=True)
    state={'documents':[],'batch':'','archives':{},'registry':DEFAULT_CLIENTS};mutex=threading.RLock();token=secrets.token_urlsafe(24)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def route(self):
            prefix='/'+token+'/'
            if not self.path.startswith(prefix):self.send_error(404);return None
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://127.0.0.1:{self.server.server_port}':self.send_error(403);return None
            return self.path[len(prefix):].split('?')[0]
        def send(self,body,kind='application/json',status=200,attachment=None):
            if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode()
            if isinstance(body,str):body=body.encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8' if kind.startswith(('application/json','text/')) else kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'")
            if attachment:self.send_header('Content-Disposition',f'attachment; filename="{attachment}"')
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            route=self.route()
            if route is None:return
            with mutex:
                if route=='health':return self.send({'ok':True})
                if route=='':return self.send((BASE/'web/index.html').read_text(encoding='utf-8'),'text/html')
                if route=='api/config':return self.send({'registry':state['registry']})
                if route.startswith('pdf/'):
                    ident=route[4:]
                    for row,data in state['documents']:
                        if row['id']==ident:return self.send(data,'application/pdf')
                if route.startswith('archive/'):
                    entry=state['archives'].get(route[8:])
                    if entry:return self.send(entry,'application/zip',attachment='DocFlow_Archivio_Ordinato.zip')
            self.send_error(404)
        def do_POST(self):
            route=self.route()
            if route is None:return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<=0 or length>40*1024*1024:raise ValueError('Richiesta vuota o oltre 40 MB.')
                body=self.rfile.read(length)
                with mutex:
                    if route=='api/shutdown':
                        self.send({'ok':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
                    if route=='api/demo':
                        payload=json.loads(body);registry=payload.get('registry',DEFAULT_CLIENTS)
                        files=[(p.name,p.read_bytes()) for p in sorted((BASE/'examples').glob('*.pdf'),key=lambda p:p.stem.rsplit('_',1)[-1])]
                        return self.analyze(files,registry)
                    if route=='api/analyze':
                        ctype=self.headers.get('Content-Type','')
                        if '\r' in ctype or '\n' in ctype or not ctype.startswith('multipart/form-data;'):raise ValueError('Caricamento non valido.')
                        message=BytesParser(policy=email.policy.default).parsebytes(('Content-Type: '+ctype+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+body)
                        if not message.is_multipart():raise ValueError('Caricamento non valido.')
                        files=[];registry=DEFAULT_CLIENTS
                        for part in message.iter_parts():
                            data=part.get_payload(decode=True) or b''
                            if part.get_filename() is not None:
                                if len(data)>MAX_BYTES:raise ValueError('Ogni PDF deve essere entro 5 MB.')
                                files.append((part.get_filename(),data))
                            elif part.get_param('name',header='content-disposition')=='registry':registry=data.decode('utf-8')
                        return self.analyze(files,registry)
                    if route=='api/archive':
                        payload=json.loads(body)
                        if payload.get('batch')!=state['batch']:raise ValueError('Il lotto è cambiato: ricarica l’anteprima.')
                        data,manifest=create_archive(state['documents'],payload.get('rows'));ident=secrets.token_urlsafe(12);state['archives'][ident]=data
                        while len(state['archives'])>3:del state['archives'][next(iter(state['archives']))]
                        return self.send({'url':'archive/'+ident,'count':len(manifest),'paths':[m['file_archiviato'] for m in manifest]})
                self.send_error(404)
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:self.send({'error':str(e)},status=400)
            except Exception:self.send({'error':'Elaborazione non completata. Verifica i file e riprova.'},status=500)
        def analyze(self,files,registry):
            documents=analyze_batch(files,registry)
            state.update(documents=documents,batch=secrets.token_hex(12),registry=registry)
            self.send({'rows':[r for r,_ in documents],'batch':state['batch']})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
    address=f'http://127.0.0.1:{server.server_port}/{token}/';info={'url':address,'pid':os.getpid()};lock=directory/'session.json';lock.write_text(json.dumps(info))
    print('DocFlow pronto: '+address,flush=True)
    try:server.serve_forever(poll_interval=.25)
    finally:
        server.server_close()
        try:
            if json.loads(lock.read_text()).get('pid')==os.getpid():lock.unlink()
        except (OSError,ValueError):pass

def spawn_server(command,log):
    options={'stdout':log,'stderr':log,'stdin':subprocess.DEVNULL,'close_fds':True}
    if os.name=='nt':
        options['creationflags']=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options['start_new_session']=True
    return subprocess.Popen(command,**options)

def launch():
    directory=data_dir();directory.mkdir(parents=True,exist_ok=True);lock=directory/'session.json'
    def existing():
        try:
            address=json.loads(lock.read_text())['url']
            if not address.startswith('http://127.0.0.1:'):return None
            with urllib.request.urlopen(address+'health',timeout=1) as r:
                if json.load(r).get('ok'):return address
        except Exception:pass
    address=existing()
    if not address:
        command=[sys.executable,'--serve'] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve()),'--serve']
        with (directory/'avvio.log').open('ab') as log:spawn_server(command,log)
        for _ in range(300):
            address=existing()
            if address:break
            time.sleep(.1)
    if not address:raise RuntimeError('DocFlow non è partito. Consulta avvio.log nella cartella dati dell’app.')
    webbrowser.open(address)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--serve',action='store_true');parser.add_argument('--port',type=int,default=0);args=parser.parse_args()
    if args.serve:run_server(args.port)
    else:launch()
