import shutil
from os import makedirs, symlink
from os.path import join as jj
from shutil import rmtree
from typing import List

from pygit2 import init_repository
from workflow.model.term_frequency import compute_term_frequencies
from workflow.model.utility import deprecated, download_url

TEST_PROTOCOLS = [
    'prot-1936--ak--8.xml',
    'prot-1961--ak--5.xml',
    'prot-1961--fk--6.xml',
    'prot-198687--11.xml',
    'prot-200405--7.xml',
]

DEFAULT_ROOT_PATH = jj("tests", "test_data", "work_folder")


def setup_working_folder(root_path: str = DEFAULT_ROOT_PATH):
    """Setup a local test data folder with minimum of necessary data and folders"""

    rmtree(root_path, ignore_errors=True)
    makedirs(root_path, exist_ok=True)

    makedirs(jj(root_path, "logs"), exist_ok=True)
    makedirs(jj(root_path, "annotated"), exist_ok=True)

    source_filenames: List[str] = setup_parla_clarin_repository(root_path, "riksdagen-corpus")

    # setup_sparv_tagging(root_path)

    setup_work_folder_for_tagging_with_stanza(root_path)
    compute_term_frequencies(source=source_filenames, filename=jj(root_path, "riksdagen-corpus-term-frequencies.pkl"))


def setup_parla_clarin_repository(
    root_path: str = DEFAULT_ROOT_PATH, repository_name: str = "riksdagen-corpus"
) -> List[str]:
    """Create a mimimal ParlaClarin XML Git repository"""

    repository_folder: str = jj(root_path, repository_name)
    corpus_folder: str = jj(repository_folder, "corpus")
    source_filenames: List[str] = []

    rmtree(repository_folder, ignore_errors=True)
    init_repository(repository_folder, True)
    makedirs(corpus_folder, exist_ok=True)

    for filename in TEST_PROTOCOLS:

        year_specifier = filename.split('-')[1]
        corpus_sub_folder = jj(corpus_folder, year_specifier)

        makedirs(corpus_sub_folder, exist_ok=True)

        url = f'https://github.com/welfare-state-analytics/riksdagen-corpus/raw/main/corpus/{year_specifier}/{filename}'

        download_url(url, corpus_sub_folder, filename)

        source_filenames.append(jj(corpus_sub_folder, filename))

    return source_filenames


def setup_work_folder_for_tagging_with_stanza(root_path: str):
    makedirs(jj(root_path, "annotated"), exist_ok=True)
    symlink("/data/sparv", jj(root_path, "sparv"))


@deprecated
def setup_work_folder_for_tagging_with_sparv(root_path: str):
    """Write a default Sparv config file (NOT USED)"""

    """Target folder for extracted speeches"""
    speech_folder: str = jj(root_path, "riksdagen-corpus-export", "speech-xml")

    """Create target folder for extracted speeches"""
    rmtree(speech_folder, ignore_errors=True)
    makedirs(speech_folder, exist_ok=True)

    """Target folder for PoS tagged speeches"""

    makedirs(speech_folder, exist_ok=True)

    makedirs(jj(root_path, "sparv"), exist_ok=True)

    shutil.copyfile("tests/test_data/sparv_config.yml", jj(root_path, "sparv", "config.yaml"))
