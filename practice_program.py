

import os
import yaml

config = {
    'photo_dir': 'photos',
    'data_dir': 'photo_info',
    'extensions': ['jpg', 'jpeg']
}

config_filename = 'config_yaml'
writer = open(config_filename, 'w')
yaml.dump(config, writer)
writer.close()


os.makedirs(config['data_dir'], exist_ok=True)
db_file = os.path.join(config['data_dir'], 'captions')
print(db_file)

import shelve
db = shelve.open(db_file, 'c')
print(db)