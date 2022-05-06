# Riksdagens Protokoll Part-Of-Speech Tagging (Parla-Clarin Workflow)

This package implements Stanza part-of-speech annotation of `Riksdagens Protokoll` Parla-Clarin XML files.


## Prerequisites

# Parla-Clarin to penelope pipeline

## How to install

## How to configure

## How to setup data

### Riksdagens corpus

Create a shallow clone (no history) of repository:

```bash
make init-repository
```

Sync shallow clone with changes on origin (Github):

```bash
make update-repository
```

Update modified date of repository file. This is necessary since the pipeline uses last commit date of
each XML-files to determine which files are outdated, whilst `git clone` sets current time.

```bash
$ make update-repository-timestamps
```

## How to annotate protocols

```bash
nohup make annotate PROCESSES_COUNT=4 >& run.log &
or
$ nohup poetry run snakemake -j4 --keep-going --keep-target-files &
```

Windows:

```bash
poetry shell
nohup poetry run snakemake -j4 -j4 --keep-going --keep-target-files &
```

Run a specific year:

```bash
poetry shell
nohup poetry run snakemake --config -j4 --keep-going --keep-target-files &
```
## Install

(This workflow will be simplified)

Verify current Python version (`pyenv` is recommended for easy switch between versions).

Create a new Python virtual environment (sandbox):

```bash
cd /some/folder
mkdir riksprot_tagging
cd riksprot_tagging
python -m venv .venv
source .venv/bin/activate
```

Install the pipeline and run setup script.

```bash
pip install pyriksprot_tagger
setup-pipeline
```

## Initialize local clone of Parla-CLARIN repository

## Run PoS tagging

Move to sandbox and activate virtual environment:

```bash
cd /some/folder/pyriksprot
source .venv/bin/activate
```

Update repository:

```bash
make update-repository
make update-repository-timestamps
```

Update all (changed) annotations:

```bash
make annotate
```

Update a single year (and set cpu count):

```bash
make annotate YEAR=1960 CPU_COUNT=1
```

## Configuration


```yaml
work_folders: !work_folders &work_folders
  data_folder: /data/westac/riksdagen_corpus_data

parla_clarin: !parla_clarin &parla_clarin
  repository_folder: path-to-repository
  repository_url: https://github.com/welfare-state-analytics/riksdagen-corpus.git
  repository_branch: main
  folder: path-to-corpus-corpus

extract_speeches: !extract_speeches &extract_speeches
  folder: path-to-speech-xml
  template: speeches.cdata.xml
  extension: xml

word_frequency: !word_frequency &word_frequency
  <<: *work_folders
  filename: riksdagen-corpus-term-frequencies.pkl

dehyphen: !dehyphen &dehyphen
  <<: *work_folders
  whitelist_filename: dehyphen_whitelist.txt.gz
  whitelist_log_filename: dehyphen_whitelist_log.pkl
  unresolved_filename: dehyphen_unresolved.txt.gz

config: !config
    work_folders: *work_folders
    parla_clarin: *parla_clarin
    extract_speeches: *extract_speeches
    word_frequency: *word_frequency
    dehyphen: *dehyphen
    annotated_folder: path-to-annotated
```
