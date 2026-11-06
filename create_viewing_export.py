"""Authoring helper: reportlab + Pillow; not required by game or notebook."""
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import shutil

root=Path(__file__).resolve().parent
images=sorted((root/'build/slides').glob('*.png'),key=lambda p:int(p.stem))
assert len(images)==9
out=root/'output/slide-previews';out.mkdir(parents=True,exist_ok=True)
pdf=Canvas(str(root/'output/Quantum_2048_Slides.pdf'),pagesize=(960,540))
pdf.setTitle('Quantum 2048: Planning with Shared Fate')
for image in images:
    pdf.drawImage(ImageReader(str(image)),0,0,960,540)
    pdf.showPage()
    shutil.copy2(image,out/f'{int(image.stem):02d}.png')
pdf.save()
html='<!doctype html><meta charset="utf-8"><title>Quantum 2048 slides</title><style>body{margin:0;background:#101a1b}img{display:block;width:100%;max-width:1280px;margin:16px auto}a{color:#b4edc7}</style>'
html+=''.join(f'<img alt="Slide {i}" src="slide-previews/{i:02d}.png">' for i in range(1,10))
(root/'output/Slides.html').write_text(html,encoding='utf8')
print('Created nine-page viewing PDF and portable slide gallery.')
