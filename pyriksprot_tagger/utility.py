from __future__ import annotations

import contextlib
import errno
import os
import sys
from os.path import isdir
from os.path import join as jj
from typing import Any, Callable

import loguru
from pyriksprot import dedent, pretokenize
from pyriksprot.gitchen import gh_get_workdir_ref


SPARV_DATADIR = os.environ.get('SPARV_DATADIR')
STANZA_DATADIR = os.environ.get('STANZA_DATADIR')


def setup_logging():
    with contextlib.suppress(Exception):
        if sys.platform == "win32":

            def handler(msg):
                if isinstance(msg, str):
                    print(msg)
                if isinstance(msg, dict):
                    if 'level' in msg and 'debug' in msg['level']:
                        return
                    if 'msg' in msg:
                        print(f"{msg.get('level', '')}: {msg['msg']}")
                        return
                print(msg)

            logger.log_handler = []

            setup_logger(handler=[handler])


WINDOWS_ERROR_INVALID_NAME = 123


def is_valid_path(pathname: str) -> bool:
    """Check if `pathname`is a valid path
    Source: https://stackoverflow.com/questions/9532499/
    """
    try:
        if not isinstance(pathname, str) or not pathname:
            return False
        _, pathname = os.path.splitdrive(pathname)
        root_dir = _root_folder()
        for part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dir + part)
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == WINDOWS_ERROR_INVALID_NAME:  # type: ignore # pylint: disable=no-member
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError:
        return False
    return True


def _root_folder():
    if sys.platform != 'win32':
        return os.path.sep
    return os.environ.get('HOMEDRIVE', 'C:').rstrip(os.path.sep) + os.path.sep


def check_cuda() -> None:
    # with contextlib.suppress(Exception):
    import torch  # pylint: disable=import-outside-toplevel

    print(f"CUDA is{' ' if torch.cuda.is_available() else ' NOT '}avaliable!")
    if not torch.cuda.is_available():
        print(
            "Please try (windows): pip install torch==1.7.0 torchvision==0.8.1 -f https://download.pytorch.org/whl/cu101/torch_stable.html"
        )


def sparv_datadir(root_folder: str):
    if SPARV_DATADIR is not None:
        return SPARV_DATADIR

    for folder in ["..", "."]:
        sparv_folder = jj(root_folder, folder, "sparv")
        if isdir(sparv_folder):
            return sparv_folder

    return None


def stanza_dir(root_folder: str) -> str:
    _sparv_datadir: str | None = sparv_datadir(root_folder)
    _stanza_dir: str = (
        STANZA_DATADIR
        if STANZA_DATADIR is not None
        else jj(_sparv_datadir, "models", "stanza")
        if _sparv_datadir is not None
        else None
    )

    if _stanza_dir is None:
        logger.error("Stanza data dir not found: STANZA_DATADIR, SPARV_DATADIR not set")
        return None

    if not isdir(_stanza_dir):
        raise FileNotFoundError(f"Stanza models folder {_stanza_dir}")

    return _stanza_dir


def create_text_preprocessors(
    pipeline: str = "dedent,dehyphen,strip,pretokenize", fxs_tasks: dict[str, Callable[[str], str]] = None
) -> "list[Callable[[str], str]]":
    fxs: list[Callable[[str], str]] = []
    fxs_tasks = {
        'dedent': dedent,
        'strip': str.strip,
        'pretokenize': pretokenize,
    } | (fxs_tasks or {})
    for fx_id in pipeline.split(","):
        if fx_id in fxs_tasks:
            fxs.append(fxs_tasks[fx_id])
        else:
            raise ValueError(f"Unknown text transform task: {fx_id}")
    return fxs


def remove_csv_item(csv: str, item: str, sep: str = ',') -> str:
    return sep.join([p for p in csv.split(sep) if p != item])


# def kwargs_as_dict(func, args: dict) -> dict[str, any]:
#     import inspect

#     sig_params = inspect.signature(func).parameters
#     opts: dict = {k: args[k] if k in args else s.default for k, s in sig_params.items()}
#     return opts
