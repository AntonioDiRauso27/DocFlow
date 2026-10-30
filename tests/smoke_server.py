"""Exercise source server, or the actual Windows portable runtime on Windows."""
import argparse,hashlib,io,json,os,shutil,subprocess,sys,tempfile,time,urllib.error,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def smoke(package=None):
    with tempfile.TemporaryDirectory(prefix='DocFlow Test ') as temp:
        temp=Path(temp)
        if package:
            if os.name!='nt':raise SystemExit('Il test del runtime Windows richiede Windows; nessuna esecuzione su macOS.')
            portable=temp/'Portable DocFlow à';shutil.copytree(package,portable)
            exe=portable/'runtime/python.exe';entry=portable/'app/server.py';examples=portable/'app/examples'
        else:exe=Path(sys.executable);entry=ROOT/'server.py';examples=ROOT/'examples'
        runtime=temp/'runtime';env={**os.environ,'DOCFLOW_DATA':str(runtime),'PYTHONDONTWRITEBYTECODE':'1'}
        options={'stdin':subprocess.DEVNULL}
        if os.name=='nt':options['creationflags']=subprocess.CREATE_NO_WINDOW
        with (temp/'server.log').open('wb') as log:
            child=subprocess.Popen([str(exe),str(entry),'--serve'],env=env,stdout=log,stderr=log,**options)
            base=None
            try:
                for _ in range(400):
                    if child.poll() is not None:raise AssertionError((temp/'server.log').read_text(errors='replace'))
                    try:
                        base=json.loads((runtime/'session.json').read_text())['url']
                        with urllib.request.urlopen(base+'health',timeout=1) as r:
                            if json.load(r)['ok']:break
                    except (OSError,ValueError):base=None
                    time.sleep(.1)
                assert base,'Server non pronto entro 40 secondi'
                with urllib.request.urlopen(base) as r:
                    assert 'L’archivio ZIP' in r.read().decode('utf-8'), 'Interfaccia non letta come UTF-8'
                def post(route,payload):
                    request=urllib.request.Request(base+'api/'+route,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                    with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)
                with urllib.request.urlopen(base+'api/config') as r:registry=json.load(r)['registry']
                data=post('demo',{'registry':registry});assert len(data['rows'])==7
                ready=[r for r in data['rows'] if r['ready']];assert len(ready)==3
                manual=next(r for r in data['rows'] if r['source']=='allegato_005.pdf')
                chosen=ready+[{**manual,'client':'Azienda Delta'}]
                result=post('archive',{'batch':data['batch'],'rows':chosen});assert result['count']==4
                with urllib.request.urlopen(base+result['url']) as r:archive=r.read()
                with zipfile.ZipFile(io.BytesIO(archive)) as z:
                    assert z.testzip() is None
                    assert 'REGISTRO_ARCHIVIAZIONE.csv' in z.namelist()
                    for row,target in zip(chosen,result['paths']):
                        assert z.read(target)==(examples/row['source']).read_bytes()
                        assert hashlib.sha256(z.read(target)).hexdigest()==row['sha256']
                duplicate=next(r for r in data['rows'] if r['source']=='copia_004.pdf')
                result=post('archive',{'batch':data['batch'],'rows':[ready[0],duplicate]})
                assert any('__2.pdf' in p for p in result['paths'])
                try:post('archive',{'batch':'stale','rows':chosen});raise AssertionError('Lotto obsoleto accettato')
                except urllib.error.HTTPError as e:assert e.code==400
                post('shutdown',{});child.wait(timeout=10);assert child.returncode==0
                print('PASS: avvio, 7 PDF, classificazione, correzione manuale, ZIP identico agli originali, duplicati, lotto obsoleto, chiusura.')
            finally:
                if child.poll() is None:
                    if base:
                        try:
                            request=urllib.request.Request(base+'api/shutdown',data=b'{}',headers={'Content-Type':'application/json'})
                            urllib.request.urlopen(request,timeout=2).close();child.wait(timeout=5)
                        except Exception:child.terminate();child.wait(timeout=5)
                    else:child.terminate();child.wait(timeout=5)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path);args=p.parse_args();smoke(args.package.resolve() if args.package else None)
