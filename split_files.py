from utils.utils import split_json_file

split_json_file('data/data.json', 'data/pulsar', max_items_per_file=40)