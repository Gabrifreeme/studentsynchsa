import xml.etree.ElementTree as ET

tree = ET.parse('ui_dump_after_ok.xml')
root = tree.getroot()

for node in root.iter('node'):
    text = node.attrib.get('text', '').strip()
    res_id = node.attrib.get('resource-id', '').strip()
    desc = node.attrib.get('content-desc', '').strip()
    bounds = node.attrib.get('bounds', '').strip()
    if text or res_id or desc:
        print(f"ID: '{res_id}' | Text: '{text}' | Desc: '{desc}' | Bounds: {bounds}")
