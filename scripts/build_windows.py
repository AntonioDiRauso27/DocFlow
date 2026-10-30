"""Build a portable Windows x64 archive from the official embeddable Python."""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='3.14.10'
URL='https://www.python.org/ftp/python/3.14.10/python-3.14.10-embed-amd64.zip'
SHA256='90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159'

def extract_verified(archive,target):
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=SHA256:raise ValueError('Hash runtime diverso da quello pubblicato da Python.org: build interrotta.')
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            path=Path(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:raise ValueError('Percorso runtime non valido.')
        z.extractall(target)

def build(output,cache):
    cache.mkdir(parents=True,exist_ok=True);archive=cache/f'python-{VERSION}-embed-amd64.zip'
    if not archive.exists():
        tmp=archive.with_suffix('.part')
        try:
            with urllib.request.urlopen(URL,timeout=90) as source,tmp.open('wb') as sink:shutil.copyfileobj(source,sink)
            tmp.replace(archive)
        finally:tmp.unlink(missing_ok=True)
    output.mkdir(parents=True,exist_ok=True);folder=output/'DocFlow Windows'
    if folder.exists():raise ValueError('Cartella di destinazione già presente. Scegli una cartella vuota.')
    runtime=folder/'runtime';runtime.mkdir(parents=True)
    try:
        extract_verified(archive,runtime)
        app=folder/'app';app.mkdir()
        for name in ('server.py','docflow.py'):shutil.copy2(ROOT/name,app/name)
        for name in ('web','examples','vendor'):shutil.copytree(ROOT/name,app/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        (runtime/'python314._pth').write_text('python314.zip\n.\n../app\n../app/vendor\nimport site\n',encoding='ascii')
        command='''@echo off
setlocal
if not exist "%~dp0runtime\\pythonw.exe" goto incomplete
if not exist "%~dp0app\\server.py" goto incomplete
start "" "%~dp0runtime\\pythonw.exe" "%~dp0app\\server.py"
exit /b 0
:incomplete
echo Pacchetto incompleto. Estrai tutto lo ZIP prima di aprire DocFlow.
pause
exit /b 1
'''
        (folder/'APRI DOCFLOW.cmd').write_bytes(command.replace('\n','\r\n').encode('ascii'))
        (folder/'LEGGIMI.txt').write_text('DOCFLOW - DEMO WINDOWS x64\n\n1. Estrai TUTTO lo ZIP in una cartella.\n2. Apri APRI DOCFLOW.cmd con doppio clic.\n3. Nel browser premi "Prova con 7 PDF fittizi".\n4. Approva le copie e scarica l’archivio ordinato.\n5. Per terminare premi "Chiudi DocFlow" nell’interfaccia.\n\nWindows 10/11 x64 Intel/AMD. Python e pypdf sono inclusi: nessuna installazione richiesta.\nNon separare APRI DOCFLOW.cmd dalle cartelle app e runtime.\n\nGli originali non vengono spostati o modificati. OCR non incluso.\nSessione e log di avvio: %LOCALAPPDATA%\\DocFlow Demo\nNon usare documenti reali per la demo. Esporta il risultato prima di chiudere.\n\nQuesto pacchetto è assemblato su macOS. La prova esecutiva su Windows deve essere completata separatamente.\n',encoding='utf-8-sig')
        (folder/'RUNTIME_ORIGIN.json').write_text(json.dumps({'python':VERSION,'architecture':'win_amd64','source':URL,'sha256':SHA256},indent=2)+'\n')
        result=Path(shutil.make_archive(str(output/'DocFlow_WINDOWS_x64'),'zip',output,folder.name))
    except Exception:
        shutil.rmtree(folder);raise
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'release/windows');p.add_argument('--cache',type=Path,default=ROOT/'build/runtime-cache');a=p.parse_args()
    print(build(a.output.resolve(),a.cache.resolve()))
