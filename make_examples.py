from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image,ImageDraw,ImageFont
import io,shutil
BASE=Path(__file__).parent/'examples';BASE.mkdir(exist_ok=True)
def document(name,kind,number,client,day):
    c=canvas.Canvas(str(BASE/name),pagesize=(595,842));c.setTitle('DocFlow - documento sintetico')
    c.setFillColor(HexColor('#355a57'));c.rect(0,830,595,12,fill=1,stroke=0);c.setFont('Helvetica-Bold',12);c.drawString(45,787,'DOCFLOW / DATI FITTIZI');c.setFillColor(HexColor('#243b3a'));c.setFont('Helvetica-Bold',25);c.drawString(45,720,kind.upper());c.setFont('Helvetica',12)
    y=675
    for text in [f'Numero documento: {number}',f'Cliente: {client}',f'Data documento: {day}' if day else 'Data documento: non indicata','Emittente: Demo Servizi SRL','Descrizione: prestazione dimostrativa','Importo: 240,00 EUR']:
        c.drawString(45,y,text);y-=35
    c.setStrokeColor(HexColor('#d7e1df'));c.line(45,395,550,395);c.setFont('Helvetica',10);c.drawString(45,367,'Esempio creato per verificare le regole di classificazione.');c.drawString(45,80,'Documento fittizio: non valido per finalita fiscali.');c.save()
document('documento_001.pdf','Fattura','104','Azienda Alfa SRL','12/10/2026')
document('allegato_002.pdf','Ricevuta','77','Azienda Beta SRL','2026-10-13')
document('documento_003.pdf','Fattura','205','Azienda Gamma SRL','14/10/2026')
shutil.copy2(BASE/'documento_001.pdf',BASE/'copia_004.pdf')
document('allegato_005.pdf','Fattura','306','Azienda Delta SRL','15/10/2026')
document('documento_007.pdf','Ricevuta','78','Azienda Beta SRL','')
# Image-only PDF: readable visually, no extractable text layer.
im=Image.new('RGB',(1190,1684),'#ffffff');d=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',28)
for n,t in enumerate(['DOCFLOW - DATI FITTIZI','RICEVUTA','Numero documento: 79','Cliente: Azienda Beta SRL','Data documento: 16/10/2026','Documento simulato senza testo selezionabile.']):d.text((90,160+n*100),t,font=font,fill='#263e3c')
c=canvas.Canvas(str(BASE/'scansione_006.pdf'),pagesize=(595,842));c.drawImage(ImageReader(im),0,0,595,842);c.save()
