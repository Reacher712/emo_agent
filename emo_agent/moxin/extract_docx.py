# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET

path = r'C:\Users\33788\Desktop\大创模板2-OperaChain-立项申请书.docx'
with zipfile.ZipFile(path, 'r') as z:
    xml_content = z.read('word/document.xml')

root = ET.fromstring(xml_content)

def get_text(element):
    texts = []
    for t in element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
        if t.tail:
            texts.append(t.tail)
    return ''.join(texts)

paragraphs = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    text = get_text(p).strip()
    if text:
        paragraphs.append(text)

for i, p in enumerate(paragraphs):
    print(f'[{i+1}] {p}')
