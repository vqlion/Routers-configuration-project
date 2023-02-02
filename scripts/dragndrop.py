import json
import os
import shutil
import sys

if len(sys.argv) < 2:
    print('Provide the path of the drag and drop file as an argument')
    sys.exit(1)

file_path = sys.argv[1]

with open(file_path, 'r') as file:
    architecture = json.load(file)

    for router in architecture['architecture']:
        router_number=router['router_number']
        removed_file=router['removed_file']
        source_file=router['source_file']
        try:
            os.remove(removed_file)
        except FileNotFoundError:
            pass
        shutil.copyfile(source_file, removed_file)

        