import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET


def parse_xml(file_path):
    """ Parse XML file and extract address data based on the given XML structure. """
    tree = ET.parse(file_path)
    root = tree.getroot()
    addresses = []
    for ent in root.findall('.//ENT'):
        address = {}
        name = ent.find('NAME').text.strip() if ent.find('NAME').text else ""
        company = ent.find('COMPANY').text.strip() if ent.find('COMPANY').text else ""
        
        # Decide whether the entry is a person's name or a company's name
        if name:
            address['name'] = name.strip()
        elif company:
            address['organization'] = company

        # Concatenate street addresses that are not empty
        streets = [ent.find(f'STREET_{i}').text.strip() for i in range(2, 4)
                   if ent.find(f'STREET_{i}') is not None and ent.find(f'STREET_{i}').text.strip()]
        full_street = ' '.join([ent.find('STREET').text.strip()] + streets)
        address['street'] = full_street

        address['city'] = ent.find('CITY').text.strip()
        address['state'] = ent.find('STATE').text.strip()
        postal_code = ent.find('POSTAL_CODE').text.strip()
        address['zip'] = postal_code.split(' -')[0]  # Assuming ZIP format needs cleaning

        # Optional country, if it's included and not empty
        country = ent.find('COUNTRY').text.strip() if ent.find('COUNTRY').text else None
        if country:
            address['country'] = country

        addresses.append(address)
    return addresses

def parse_tsv(file_path):
    """ Parse TSV file and extract address data. """
    addresses = []
    with open(file_path, newline='') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            address = {}
            if row['organization'] != 'N/A':
                address['organization'] = row['organization']
            else:
                name_parts = [x.strip() for x in [row['first'], row['middle'], row['last']]]
                # Filter out empty strings and join names
                address['name'] = ' '.join(filter(None, name_parts))

            address['street'] = row['address'].strip()
            if (row.get('county') != ''): address['county'] = row['county'].strip()
            address['city'] = row['city'].strip()
            address['state'] = row['state'].strip()
            address['zip'] = row['zip'].strip() + '-' + \
                row['zip4'].strip() if row['zip4'] else row['zip'].strip()
                
            addresses.append(address)
    return addresses

def parse_txt(file_path):
    """ Parse plain text file and extract address data. """
    addresses = []
    with open(file_path, 'r') as file:
        content = file.read().strip().split('\n\n')
        for block in content:
            lines = block.split('\n')
            address = {}
            name_line = lines[0]
            if ',' in name_line:
                address['name'] = name_line.replace(',', '')
            else:
                address['name'] = name_line.strip()

            address['street'] = lines[1].strip()
            if 'COUNTY' in lines[2]:
                address['county'] = lines[2].replace('COUNTY', '').strip()
                city_state_zip = lines[3].split(',')
            else:
                city_state_zip = lines[2].split(',')
            address['city'] = city_state_zip[0].strip()
            state_zip = city_state_zip[1].strip().split(' ')
            address['state'] = state_zip[0].strip()
            address['zip'] = state_zip[1].strip()

            addresses.append(address)
    return addresses

def main(args):
    parser = argparse.ArgumentParser(
        description="Process and combine address data from different file formats.")
    parser.add_argument('files', metavar='FILE', type=str, 
                        nargs='+', help='Path to the input file(s)')
    args = parser.parse_args(args)

    if not args.files:
        sys.stderr.write("Error: No files provided.\n")
        sys.exit(1)

    file_paths = []
    for path in args.files:
        try:
            if path.endswith('.xml'):
                file_paths.extend(parse_xml(path))
            elif path.endswith('.tsv'):
                file_paths.extend(parse_tsv(path))
            elif path.endswith('.txt'):
                file_paths.extend(parse_txt(path))
            else:
                sys.stderr.write(
                    f"Error: Unsupported file format for {path}\n")
                continue
        except Exception as e:
            sys.stderr.write(f"Error processing {path}: {e}\n")
            sys.exit(1)

    # Sort addresses by ZIP code
    file_paths.sort(key=lambda x: x.get('zip', '99999'))

    # Save output to JSON file
    with open('output.json', 'w') as f:
        json.dump(file_paths, f, indent=2)

if __name__ == "__main__":
    main(sys.argv[1:])
