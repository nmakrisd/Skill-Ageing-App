import xml.etree.ElementTree as ET
import json

def xml_to_single_json(xml_path, json_path):
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json_file.write('[\n')  # Start of JSON array

        context = ET.iterparse(xml_path, events=('start',))
        first = True
        count = 0

        for event, elem in context:
            if elem.tag == 'row':
                if not first:
                    json_file.write(',\n')
                json.dump(elem.attrib, json_file)
                elem.clear()
                first = False
                count += 1

        json_file.write('\n]')  # End of JSON array
    print(f'✅ Completed: {count} items written to {json_path}')

# Usage
xml_to_single_json('Posts.xml', 'Posts.json')


