from __future__ import annotations

import os
import warnings
from os.path import isdir
from typing import Any, Callable, List, Literal, Union

import stanza
import stanza.pipeline.processor as spp
from loguru import logger
from pyriksprot import ITagger, ITaggerFactory, SwedishDehyphenator, TaggedDocument
from pyriksprot.configuration import ConfigValue, inject_config
from pyriksprot.foss import sparv_tokenize

from .. import utility

"""PoS tagging using Stanford's Stanza library.
NOTE! THIS CODE IS IN PART BASED ON https://github.com/spraakbanken/sparv-pipeline/blob/master/sparv/modules/stanza/stanza.py
"""

SENTENCE_MARKER = "--SENTENCE--"

jj = os.path.join

# pylint: disable=too-many-arguments

"""Follow Språkbanken Sparv's naming of model names and config keys."""
STANZA_CONFIGS: dict = {
    "sv": {
        "resources_file": "resources.json",
        "lem_model": jj("lem", "sv_suc_lemmatizer.pt"),
        "pos_model": jj("pos", "full_sv_talbanken_tagger.pt"),
        "pretrain_pos_model": jj("pos", "full_sv_talbanken.pretrain.pt"),
        "dep_model": jj("dep", "sv_talbanken_parser.pt"),
        "pretrain_dep_model": jj("pos", "full_sv_talbanken.pretrain.pt"),
    }
}


STANZA_DEFAULT_OPTS: dict = {
    'lang': 'sv',
    'processors': 'tokenize,lemma,pos',
    'tokenize_pretokenized': False,
    'tokenize_no_ssplit': True,
    'use_gpu': True,
    'num_threads': None,
    'preprocessors': 'dedent,dehyphen,strip',
    'tokenize_with_sparv': True,
}


@spp.register_processor_variant('tokenize', 'sparv')
class BetterSparvTokenizer(spp.ProcessorVariant):
    def __init__(self, config: dict):
        """A sparv-based tokenizer for the stanza pipeline."""

        self.no_ssplit: bool = config.get("no_ssplit", False)
        self.tokenize: Callable = sparv_tokenize.SegmenterRepository.create_tokenize(
            sentenize=not self.no_ssplit, return_spans=True
        )

    def process(self, doc: stanza.Document | str) -> stanza.Document:  # type: ignore
        """Tokenize with the Sparv tokenizer and return a stanza Document object."""
        if not isinstance(doc, (stanza.Document, str)):
            raise ValueError("Expected a string or Stanza Document.")

        text: str = doc.text if isinstance(doc, stanza.Document) else doc

        tokenize: Callable = self.tokenize
        if self.no_ssplit:
            sentences: list[dict[str, str | int]] = [
                [
                    {'id': idx, 'text': token, 'start_char': start_char, 'end_char': end_char}
                    for idx, (token, start_char, end_char) in enumerate(tokenize(text))
                ]
            ]

        else:
            sentences: list[dict[str, str | int]] = [
                [
                    {'id': idx, 'text': token, 'start_char': start_char, 'end_char': end_char}
                    for idx, (token, start_char, end_char) in enumerate(sentence)
                ]
                for sentence in tokenize(text)
            ]

        return stanza.Document(sentences=sentences, text=text)


class StanzaTagger(ITagger):
    """Stanza PoS tagger wrapper"""

    def __init__(
        self,
        *,
        stanza_datadir: str,
        lang: str = "sv",
        processors: str = "tokenize,lemma,pos",
        tokenize_pretokenized: bool = True,
        tokenize_no_ssplit: bool = True,
        tokenize_with_sparv: bool = True,
        use_gpu: bool = True,
        num_threads: int = None,
        preprocessors: Callable[[str], str] = "pretokenize",
        word_or_token: Literal['words', 'tokens'] = 'words',
        verbose: bool = False,
    ):
        super().__init__(preprocessors=preprocessors or "pretokenize")

        """Initialize stanza pipeline

        Args:
            model_root (str): where Språkbanken's Stanza models are stored
            preprocessors (Callable[[str], str]): Text transforms to do prior to tagging.
            lang (str, optional): Language (only 'sv' supported). Defaults to "sv".
            processors (str, optional): Stanza process steps. Defaults to "tokenize,lemma,pos".
            tokenize_pretokenized (bool, optional): If true, then already tokenized. Defaults to True.
            tokenize_no_ssplit (bool, optional): [description]. Defaults to True.
            use_gpu (bool, optional): If true, use GPU if exists. Defaults to True.
        """
        stanza_datadir = stanza_datadir or os.environ.get("STANZA_DATADIR")
        utility.check_cuda()

        logger.info(f"stanza: processors={processors} preprocessors={preprocessors} use_gpu={use_gpu}")
        logger.info("stanza: loading models")
        config: dict = STANZA_CONFIGS[lang]

        if isinstance(num_threads, (int, str)):
            os.environ['OMP_NUM_THREADS'] = str(num_threads)

        if not isdir(stanza_datadir):
            raise FileNotFoundError("STANZA_DATADIR not set to a valid path")

        tokenize_opts: dict[str, Any] = {
            'tokenize_pretokenized': tokenize_pretokenized,
            'tokenize_no_ssplit': tokenize_no_ssplit,
        } | ({'tokenize_with_sparv': True} if tokenize_with_sparv else {})

        pos_opts: dict = {
            'pretrain_pos_model': jj(stanza_datadir, config["pretrain_pos_model"]),
            'pos_model_path': jj(stanza_datadir, config["pos_model"]),
        }

        opts: dict = (
            {
                'lang': lang,
                'processors': processors,
                'dir': stanza_datadir,
                'lemma_model_path': jj(stanza_datadir, config["lem_model"]),
                'use_gpu': use_gpu,
                'verbose': verbose,
            }
            | tokenize_opts
            | pos_opts
        )
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', FutureWarning)
            self.nlp: stanza.Pipeline = stanza.Pipeline(**opts)

        self.word_or_token: Literal['words'] | Literal['tokens'] = word_or_token
        self.ssplit: bool = not tokenize_no_ssplit

    def _tag(self, text: Union[str, List[str]]) -> List[TaggedDocument]:
        """Tag text. Return dict if lists."""

        documents: list[stanza.Document] = [stanza.Document([], text=d) for d in text]

        tagged_documents: List[stanza.Document] = self.nlp(documents)

        if isinstance(tagged_documents, stanza.Document):
            tagged_documents = [tagged_documents]

        return [self._to_dict(d) for d in tagged_documents]

    def _to_dict(
        self,
        tagged_document: stanza.Document,
        add_sentence_marker: bool = False,
        sentence_marker: str = SENTENCE_MARKER,
    ) -> TaggedDocument:
        """Extract tokens from tagged document. Return dict of list."""
        tokens, lemmas, pos, xpos, sentence_ids = [], [], [], [], []  # type: ignore
        add_sentence_marker = self.ssplit and add_sentence_marker
        add_sentence_id: bool = self.ssplit and not add_sentence_marker

        sentence_id: int = -1
        for sentence in tagged_document.sentences:
            sentence_id += 1
            for w in getattr(sentence, self.word_or_token):
                tokens.append(w.text)
                lemmas.append(w.lemma or w.text.lower())
                pos.append(w.upos)
                xpos.append(w.xpos)
                if add_sentence_marker:
                    sentence_ids.append(sentence_id)

            if add_sentence_id:
                tokens.append(sentence_marker)
                lemmas.append(sentence_marker)
                pos.append('MAD')
                xpos.append('MAD')

        return dict(
            token=tokens,
            lemma=lemmas,
            pos=pos,
            xpos=xpos,
            num_tokens=tagged_document.num_tokens,
            num_words=tagged_document.num_words,
        ) | (
            {'sentence_id': sentence_ids} if add_sentence_id else {}
        )  # type: ignore


# pylint: disable=unused-argument


class StanzaTaggerFactory(ITaggerFactory):
    identifier: str = "stanza_swedish"

    def __init__(self, **opts) -> None:
        self.opts: dict = opts

    @staticmethod
    def factory(**opts) -> "StanzaTaggerFactory":
        """Typed abstract factory"""
        # opts = StanzaTaggerFactory.args_as_dict(locals())

        return StanzaTaggerFactory(**(STANZA_DEFAULT_OPTS | opts))

    def create_dehyphen_task(self) -> Callable[[str], str]:
        return SwedishDehyphenator.create_dehypen(  # type: ignore
            data_folder=self.opts.get("dehyphen_datadir"),
            word_frequencies=self.opts.get("word_frequencies"),
        )

    def create_preprocessor_tasks(self) -> List[Callable[[str], str]]:
        fxs_tasks = (
            {'dehyphen': self.create_dehyphen_task()} if 'dehyphen' in self.opts.get('preprocessors', {}) else {}
        )

        tasks = utility.create_text_preprocessors(
            pipeline=self.opts.get('preprocessors'),
            fxs_tasks=fxs_tasks,
        )
        return tasks

    def create(self) -> ITagger:
        tagger: StanzaTagger = StanzaTagger(
            stanza_datadir=self.opts.get("stanza_datadir"),
            preprocessors=self.create_preprocessor_tasks(),
            use_gpu=self.opts.get("use_gpu", True),
            num_threads=self.opts.get("num_threads", 2),
        )

        return tagger


@inject_config
def tagger_factory(
    tagger_opts: dict | ConfigValue = ConfigValue(key="tagger,tagger:opts", mandatory=True),
    dehyphen_opts: dict | ConfigValue = ConfigValue(key="dehyphen,dehypen:opts", mandatory=True),
) -> ITaggerFactory:
    return create_tagger_factory(tagger_opts, dehyphen_opts)


def create_tagger_factory(tagger_opts: dict[str, Any], dehyphen_opts: dict[str, Any]) -> ITaggerFactory:
    stanza_datadir: str | ConfigValue | None = (
        tagger_opts.get("stanza_datadir") or tagger_opts.get("folder") or os.environ.get("STANZA_DATADIR")
    )

    if stanza_datadir is None:
        raise ValueError("No model folder specified")

    for key in ["module", "stanza_datadir"]:
        if key in tagger_opts:
            tagger_opts.pop(key)

    if 'dehyphen' in tagger_opts.get('preprocessors'):  # type: ignore
        if not dehyphen_opts.get("folder"):
            raise ValueError("No dehyphen folder specified")
        if not dehyphen_opts.get("tf_filename"):
            raise ValueError("No dehyphen TF filename specified")

    tagger_opts = (
        {
            'dehyphen_datadir': dehyphen_opts.get("folder"),
            'word_frequencies': dehyphen_opts.get("tf_filename"),
            'stanza_datadir': stanza_datadir,
        }
        | STANZA_DEFAULT_OPTS
        | (tagger_opts or {})
    )

    if tagger_opts.get("tokenize_with_sparv"):
        tagger_opts['preprocessors'] = utility.remove_csv_item(tagger_opts['preprocessors'], 'pretokenize')
        tagger_opts['tokenize_pretokenized'] = False
        tagger_opts['tokenize_no_ssplit'] = tagger_opts.get("no_ssplit", False)

    if 'dehyphen' in tagger_opts.get('processors'):  # type: ignore
        tagger_opts['preprocessors'] = utility.remove_csv_item(tagger_opts['preprocessors'], 'dehyphen')

    return StanzaTaggerFactory.factory(**tagger_opts)


# @register_processor("sparv_dehyphen")
# class BetterSparvDehypenator(Processor):
#     ''' Processor that lowercases all text '''

#     _requires = set(['tokenize'])
#     _provides = set(['sparv_dehyphen'])

#     def __init__(self, config, pipeline, device):
#         super().__init__(config, pipeline, device)
#         self.dehyphenator: SwedishDehyphenator | None = None

#     def _set_up_model(self, *_):
#         self.dehyphenator = SwedishDehyphenator(self.config.get("data_folder"), self.config.get("word_frequencies"))

#     def __str__(self):
#         return f"BetterSparvDehypenator({self.config.get('data_folder', '')})"

#     def process(self, doc):
#         doc = self.dehyphenator.dehyphen_text(doc)
#         # for sent in doc.sentences:
#         #     for tok in sent.tokens:
#         #         tok.text = tok.text.lower()

#         #     for word in sent.words:
#         #         word.text = word.text.lower()

#         return doc
