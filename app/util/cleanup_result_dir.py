from pathlib import Path
import os

artifacts_dir = os.environ.get('TAURUS_ARTIFACTS_DIR')
files_to_remove = ['jmeter.out',
                   'jmeter-bzt.properties',
                   'merged.json',
                   'merged.yml',
                   'PyTestExecutor.ldjson',
                   'system.properties']


for _ in files_to_remove:
    file_path = Path(artifacts_dir + f'/{_}')
    try:
        os.remove(file_path)
    except OSError as e:
        print(f'Deleting of the {_} failed!'
              f'Error: {file_path}: {e.strerror}')

