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


def test_version_specification() -> None:

    with tempfile.TemporaryDirectory() as temp_folder:

        repo: pygit2.repository.Repository = create_dummy_repository(temp_folder)

        tag = "v9.9.9"
        repo.create_reference(f"refs/tags/{tag}", repo.head.target)
        repo.set_head(f"refs/tags/{tag}")

        repo.checkout_head(strategy=pygit2.GIT_CHECKOUT_NOTIFY_NONE)

        ref_type, value = gh_get_workdir_ref(temp_folder)

        assert ref_type == "tag"
        assert value == tag

        assert VersionSpecification.is_satisfied(temp_folder, tag) is True
        assert VersionSpecification.is_satisfied(temp_folder, 'dummy') is False


def create_dummy_repository(temp_folder):
    repo: pygit2.repository.Repository = pygit2.init_repository(temp_folder, bare=False, initial_head="main")

    assert repo is not None
    assert repo.head_is_unborn

    author = pygit2.Signature("Your Name", "you@example.com")

    (Path(temp_folder) / "README.md").write_text("# My new repo\n")

    tree = repo.index.write_tree()
    repo.create_commit("refs/heads/main", author, author, "Initial commit", tree, [])
    return repo
