import json
from utils.utils import remove_null_fixes

file = './json/raw_data/issues.json'

with open(file) as f:
    data = json.load(f)
    print('Before:', len(data))
    data = remove_null_fixes(file)

with open(file) as f:
    data = json.load(f)
    print('After:', len(data))