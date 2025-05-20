import os
import shutil
import tempfile
from os import makedirs, symlink
from os.path import isfile
from os.path import join as jj
from pathlib import Path
from shutil import rmtree

from pygit2 import init_repository
from pyriksprot import compute_term_frequencies
from pyriksprot import corpus as pc
from pyriksprot import ensure_path
from pyriksprot import metadata as md
from pyriksprot import strip_extensions
from pyriksprot.configuration import Config
from pyriksprot.corpus.utility import ls_corpus_folder
from pyriksprot_tagger.scripts import tag as tagger_script

RIKSPROT_SAMPLE_PROTOCOLS = [
    'prot-1936--ak--008.xml',
    'prot-1961--ak--005.xml',
    'prot-1961--fk--006.xml',
    'prot-198687--011.xml',
    'prot-200405--007.xml',
]

RIKSPROT_SAMPLE_DATA_FOLDER = "./tests/output/work_folder"


def setup_working_folder(
    *,
    tag: str,
    folder: str,
    protocols: "list[str]" = None,
    pattern: str = None,
    **gh_opts,
):
    """Setup a local test data folder with minimum of necessary data and folders"""

    if not tag:
        raise ValueError("cannot proceed since tag is undefined")

    rmtree(folder, ignore_errors=True)
    makedirs(jj(folder, "logs"), exist_ok=True)
    makedirs(jj(folder, "annotated"), exist_ok=True)

    create_sample_xml_repository(tag=tag, protocols=protocols, root_path=folder, **gh_opts)

    setup_work_folder_for_tagging_with_stanza(folder)

    corpus_folder: str = jj(folder, gh_opts.get("repository", ""), gh_opts.get("path", ""))

    filenames: list[str] = ls_corpus_folder(corpus_folder, pattern)
    compute_term_frequencies(source=filenames, filename=jj(folder, "word-frequencies.pkl"), multiproc_processes=None)

    Path(jj(folder, tag)).touch()


def create_sample_xml_repository(
    *, tag: str, protocols: "list[str]", root_path: str = RIKSPROT_SAMPLE_DATA_FOLDER, **gh_opts
) -> None:
    """Create a mimimal ParlaClarin XML git repository"""

    folder: str = jj(root_path, "riksdagen-records")

    rmtree(folder, ignore_errors=True)
    init_repository(folder)

    download_sample_data(tag, protocols, folder, **gh_opts)


def download_sample_data(tag: str, protocols: "list[str]", target_folder: str, **gh_opts) -> None:
    source_folder: str = "tests/test_data/source/"
    sample_data_archive: str = jj(source_folder, f"{tag}_data.zip")
    """Create archive instead of downloading each test run"""
    if not isfile(sample_data_archive):
        download_to_archive(tag, protocols, sample_data_archive, **gh_opts)

    """Unzip archive in repository"""
    os.makedirs(target_folder, exist_ok=True)
    shutil.unpack_archive(sample_data_archive, target_folder)


def download_to_archive(tag: str, protocols: "list[str]", target_filename: str, **gh_opts) -> None:
    with tempfile.TemporaryDirectory() as temp_folder:
        pc.download_protocols(
            filenames=protocols, target_folder=jj(temp_folder, "data"), create_subfolder=True, tag=tag, **gh_opts
        )
        schema: md.MetadataSchema = md.MetadataSchema(tag)

        md.gh_download_by_config(schema=schema, tag=tag, folder=jj(temp_folder, "metadata"), force=True)

        ensure_path(target_filename)
        shutil.make_archive(strip_extensions(target_filename), 'zip', temp_folder)


def setup_work_folder_for_tagging_with_stanza(root_path: str) -> None:
    makedirs(jj(root_path, "annotated"), exist_ok=True)
    symlink("/data/sparv", jj(root_path, "sparv"))


def pos_tag_testdata_for_current_version(config_filename: str, force: bool = True) -> None:

    config: Config = Config.load(source=config_filename)

    target_folder: str = config.get("tagged_frames.folder")
    dehyphen_folder: str = config.get("dehyphen.folder")

    if os.path.isdir(target_folder):
        if not force:
            raise ValueError(f"Target folder exists: {target_folder}")

    shutil.rmtree(target_folder, ignore_errors=True)

    os.makedirs(target_folder, exist_ok=True)
    os.makedirs(dehyphen_folder, exist_ok=True)

    corpus_folder: str = config.get("corpus.folder")
    pattern: str = config.get("pattern.folder")

    filenames: list[str] = ls_corpus_folder(corpus_folder, pattern)

    compute_term_frequencies(
        source=filenames, filename=jj(dehyphen_folder, "word-frequencies.pkl"), multiproc_processes=None
    )

    tagger_script.tagit(
        config_filename=config_filename,
        source_folder=corpus_folder,
        target_folder=target_folder,
        force=True,
        recursive=True,
    )


def create_test_config(tag: str, data_folder: str) -> dict:
    return {
        'root_folder': data_folder,
        'data_folder': data_folder,
        'version': tag,
        'corpus': {
            'version': tag,
            'folder': f'{data_folder}/riksdagen-records/data',
            'pattern': "**/prot-*-*.xml",
            'github': {
                'user': "swerik-project",
                'repository': "riksdagen-records",
                'path': "data",
                'local_folder': f"{data_folder}/riksdagen-records",
            },
        },
        'metadata': {
            'version': tag,
            'folder': f'{data_folder}/parlaclarin/metadata',
            'database': {
                'type': 'pyriksprot.metadata.database.SqliteDatabase',
                'options': {
                    'filename': f'{data_folder}/parlaclarin/metadata/riksprot_metadata.db',
                },
            },
            'github': {
                'user': 'swerik-project',
                'repository': 'riksdagen-persons',
                'path': 'data',
                'url': ' https://github.com/swerik-project/riksdagen-records.git',
            },
        },
        'tagged_frames': {
            'folder': f'{data_folder}/tagged_frames',
            'file_pattern': 'prot-*.zip',
            'pattern': f'{data_folder}/tagged_frames/**/prot-*.zip ',
        },
        'tagger': {
            'lang': "sv",
            'processors': "tokenize,lemma,pos",
            'tokenize_no_ssplit': True,
            'tokenize_pretokenized': True,
            'use_gpu': False,
            'num_threads': 1,
            'module': 'pyriksprot_tagger.taggers.stanza_tagger',
            'stanza_datadir': f'{data_folder}/sparv/models/stanza',
            'preprocessors': "dedent,dehyphen,strip,pretokenize",
        },
        'dehyphen': {
            'folder': f'{data_folder}/dehyphen',
            'tf_filename': f'{data_folder}/dehyphen/word-frequencies.pkl',
        },
    }
