import json 
import os
from utils.utils import update_matched

for file in os.listdir('./json/bics/'):
    file_path = f'./json/bics/{file}'
    update_matched(file_path)

