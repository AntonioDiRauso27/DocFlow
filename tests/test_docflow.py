import hashlib,io,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from docflow import *
BASE=Path(__file__).resolve().parents[1]
class DocFlowTests(unittest.TestCase):
 def setUp(self):
  self.files=[(p.name,p.read_bytes()) for p in sorted((BASE/'examples').glob('*.pdf'),key=lambda p:p.stem.rsplit('_',1)[-1])]
  self.docs=analyze_batch(self.files,DEFAULT_CLIENTS)
 def test_classification(self):
  ready=[r for r,_ in self.docs if r['ready']];self.assertEqual(len(ready),3);self.assertEqual({r['client'] for r in ready},{'Azienda Alfa','Azienda Beta','Azienda Gamma'})
 def test_review_cases(self):
  byname={r['source']:r for r,_ in self.docs}
  self.assertTrue(byname['copia_004.pdf']['duplicate_of']);self.assertFalse(byname['copia_004.pdf']['ready'])
  self.assertEqual(byname['allegato_005.pdf']['client'],'');self.assertFalse(byname['scansione_006.pdf']['readable']);self.assertTrue(byname['scansione_006.pdf']['valid_pdf']);self.assertEqual(byname['documento_007.pdf']['date'],'')
 def test_archive_hashes_and_copies(self):
  approved=[r for r,_ in self.docs if r['ready']];data,manifest=create_archive(self.docs,approved)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   self.assertIsNone(z.testzip());self.assertEqual(len([n for n in z.namelist() if n.endswith('.pdf')]),3)
   for m in manifest:self.assertEqual(hashlib.sha256(z.read(m['file_archiviato'])).hexdigest(),m['sha256_originale'])
  for name,data in self.files:self.assertEqual((BASE/'examples'/name).read_bytes(),data)
 def test_no_overwrite(self):
  original=self.docs[0][0];duplicate=self.docs[3][0]
  data,manifest=create_archive(self.docs,[original,{**original,'id':duplicate['id']}]);self.assertIn('__2.pdf',manifest[1]['file_archiviato'])
 def test_manual_scanned(self):
  r=next(r for r,_ in self.docs if r['source']=='scansione_006.pdf')
  data,m=create_archive(self.docs,[{**r,'client':'Azienda Beta','kind':'Ricevuta','date':'2026-10-16','number':'79'}]);self.assertEqual(len(m),1)
 def test_invalid_date_and_type(self):
  r=next(r for r,_ in self.docs if r['ready'])
  for patch in [{'date':'2026-02-30'},{'kind':'Altro'},{'client':''},{'number':'?'}]:
   with self.assertRaises(ValueError):create_archive(self.docs,[{**r,**patch}])
 def test_no_duplicate_ids(self):
  r=self.docs[0][0]
  with self.assertRaises(ValueError):create_archive(self.docs,[r,r])
 def test_no_corrupt_pdf(self):
  docs=analyze_batch([('errato.pdf',b'not a pdf')],DEFAULT_CLIENTS);r=docs[0][0];self.assertFalse(r['valid_pdf'])
  with self.assertRaises(ValueError):create_archive(docs,[{**r,'client':'Alfa','kind':'Fattura','number':'1','date':'2026-10-12'}])
 def test_traversal_windows_names(self):
  p=destination({'client':'../../CON','kind':'Fattura','number':'../../x/1','date':'2026-10-12'});self.assertNotIn('..',p);self.assertFalse(p.startswith('/'));self.assertEqual(safe_part('CON'),'_CON')
 def test_ambiguous_date_client_type(self):
  text='FATTURA\nRICEVUTA\nCliente: Azienda Alfa SRL e Azienda Beta SRL\nData documento: 12/10/2026\nData: 2026-10-13\nNumero documento: 12'
  r=extract_metadata(text,clients_from_text(DEFAULT_CLIENTS));self.assertEqual((r['client'],r['kind'],r['date']),('','',''))
 def test_receipt_with_invoice_reference(self):
  r=extract_metadata('RICEVUTA\nCliente: Azienda Alfa SRL\nData: 12/10/2026\nNumero documento: 5\nRiferimento fattura 4',clients_from_text(DEFAULT_CLIENTS));self.assertEqual(r['kind'],'Ricevuta')
 def test_bad_registry(self):
  for text in ['', 'Alfa|xx', 'Alfa|Beta\nGamma|Beta']:
   with self.assertRaises(ValueError):clients_from_text(text)
 def test_limits(self):
  with self.assertRaises(ValueError):analyze_batch([],DEFAULT_CLIENTS)
  with self.assertRaises(ValueError):analyze_batch(self.files*5,DEFAULT_CLIENTS)
if __name__=='__main__':unittest.main(verbosity=2)
