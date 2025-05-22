from dotenv import load_dotenv
from pyriksprot.configuration import ConfigStore, ConfigValue

from .utility import RIKSPROT_SAMPLE_DATA_FOLDER, RIKSPROT_SAMPLE_PROTOCOLS, setup_working_folder


def pytest_sessionstart(session):  # pylint: disable=unused-argument

    load_dotenv('tests/test.env')

    ConfigStore.configure_context(source="./tests/config.yml", context="default", env_prefix="RIKSPROT")

    setup_working_folder(
        corpus_version=ConfigValue("corpus.version").value,
        metadata_version=ConfigValue("metadata.version").value,
        folder=RIKSPROT_SAMPLE_DATA_FOLDER,
        protocols=RIKSPROT_SAMPLE_PROTOCOLS,
        pattern=ConfigValue("corpus.pattern").value,
        **ConfigValue("corpus.github").value,
    )
