import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pygit2
from pyriksprot_tagger.utility import VersionSpecification, gh_get_workdir_ref

TEST_BASENAMES = [
    'prot-198687--011',
    'prot-200405--007',
    'prot-1961--fk--006',
    'prot-1961--ak--005',
    'prot-1936--ak--008',
]


def _setup_test_files(folder: str):
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder, exist_ok=True)
    for basename in TEST_BASENAMES:
        target_folder: str = f'{folder}/{basename.split("-")[1]}'
        os.makedirs(target_folder, exist_ok=True)
        with open(os.path.join(target_folder, f"{basename}.xml"), 'w', encoding='utf8') as f:
            f.write('')


