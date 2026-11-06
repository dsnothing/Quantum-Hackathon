"""Viewing export from the inspected slide renders. Editable source is the PPTX."""
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
import shutil

root=Path(__file__).resolve().parent
slides=sorted((root/'build/five-minute/slides').glob('*.png'))
assert len(slides)==10
dest=root/'output/Quantum_2048_Five_Minute_Previews'
dest.mkdir(exist_ok=True)
pdf=root/'output/Quantum_2048_Five_Minute.pdf'
c=Canvas(str(pdf),pagesize=(960,540))
c.setTitle('Quantum 2048: five-minute presentation with technical appendix')
c.setSubject('Six main slides, four appendix slides. Viewing export; use PPTX for editing and presenter notes.')
for image in slides:
    c.drawImage(ImageReader(str(image)),0,0,960,540)
    c.showPage()
    shutil.copy2(image,dest/image.name)
c.save()
assert len(PdfReader(pdf).pages)==10
print('Created ten-page viewing PDF and matching PNG previews.')
