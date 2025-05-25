import os
from dotenv import load_dotenv
from pyriksprot.configuration import ConfigStore, ConfigValue
from pyriksprot.utility import generate_default_config

from .utility import RIKSPROT_SAMPLE_DATA_FOLDER, RIKSPROT_SAMPLE_PROTOCOLS, setup_working_folder

CONFIG_FILENAME: str = "tests/output/config.yml"

def pytest_sessionstart(session):  # pylint: disable=unused-argument

    load_dotenv('tests/test.env')

    required_variables: list[str] = ['CORPUS_VERSION', 'METADATA_VERSION', 'STANZA_DATADIR']

    if not all(os.environ.get(v) for v in required_variables):
        raise ValueError(f"Environment variables {', '.join(required_variables)} are not set or are empty")
    
    generate_default_config(
        target_filename=CONFIG_FILENAME,
        corpus_version=os.environ['CORPUS_VERSION'],
        metadata_version=os.environ['METADATA_VERSION'],
        corpus_folder='tests/test_data/source',
        root_folder='tests/test_data/source',
        stanza_datadir=os.environ['STANZA_DATADIR'],
    )

    ConfigStore.configure_context(source=CONFIG_FILENAME, context="default", env_prefix="RIKSPROT")

    setup_working_folder(
        corpus_version=ConfigValue("corpus.version").value,
        metadata_version=ConfigValue("metadata.version").value,
        folder=RIKSPROT_SAMPLE_DATA_FOLDER,
        protocols=RIKSPROT_SAMPLE_PROTOCOLS,
        pattern=ConfigValue("corpus.pattern").value,
        **ConfigValue("corpus.github").value,
    )
