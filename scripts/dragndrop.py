import json
import os
import sys
import shutil




with open('/mnt/c/INSALyonTC/GNS3_Project_3TC/intent_files/dragndrop.json', 'r') as file:
    architecture = json.load(file)

    for router in architecture['architecture']:
        router_number=router['router_number']
        removed_file=router['removed_file']
        source_file=router['source_file']
        os.remove(removed_file)
        shutil.copyfile(source_file, removed_file)

        