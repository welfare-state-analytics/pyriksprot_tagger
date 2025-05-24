import tempfile
from os.path import join as jj
from typing import List

from pyriksprot.utility import ensure_path, touch, unlink

TEST_DUMMY_FILENAMES = [
    'prot-200708--013',
    'prot-200001--037',
    'prot-198485--141',
    'prot-197576--121',
    'prot-199697--042',
    'prot-1944-höst-fk--028',
    'prot-200607--073',
    'prot-200304--074',
    'prot-1952--fk--022',
    'prot-1932--fk--038',
]


def create_test_source_tree(corpus_path: str, filenames: List[str]):
    unlink(corpus_path)
    for filename in filenames:
        year_folder = jj(corpus_path, filename.split('-')[1])
        target_file = jj(year_folder, f"{filename}.xml")
        ensure_path(target_file)
        touch(target_file)

