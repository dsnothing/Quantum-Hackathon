"""Read-only PPTX triage using only Python's standard library."""
import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def audit(path):
    findings = []
    with zipfile.ZipFile(path) as archive:
        size = ET.fromstring(archive.read('ppt/presentation.xml')).find('p:sldSz', NS)
        width, height = int(size.get('cx')), int(size.get('cy'))
        names = sorted((n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)),
                       key=lambda n: int(re.search(r'(\d+)\.xml', n).group(1)))
        for number, name in enumerate(names, 1):
            root = ET.fromstring(archive.read(name))
            for shape in root.findall('.//p:sp', NS):
                text = ' '.join(t.text or '' for t in shape.findall('.//a:t', NS))
                label = text[:90]
                for run in (shape.findall('.//a:rPr', NS) if text else []):
                    if run.get('sz') and int(run.get('sz')) < 1800:
                        findings.append({'slide': number, 'kind': 'small explicit text',
                                         'points': int(run.get('sz')) / 100, 'text': label})
                        break
                transform = shape.find('p:spPr/a:xfrm', NS)
                if transform is not None:
                    off, ext = transform.find('a:off', NS), transform.find('a:ext', NS)
                    if off is not None and ext is not None:
                        x, y = int(off.get('x')), int(off.get('y'))
                        w, h = int(ext.get('cx')), int(ext.get('cy'))
                        if x < 0 or y < 0 or x + w > width + 12700 or y + h > height + 12700:
                            findings.append({'slide': number, 'kind': 'off-canvas shape', 'text': label})
    return {'slides': len(names), 'findings': findings,
            'limits': 'Explicit geometry/font triage only. Render and inspect theme text, inherited images, wrapping and contrast.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('presentation')
    args = parser.parse_args()
    print(json.dumps(audit(args.presentation), indent=2))
