include .env

ifndef CORPUS_VERSION
$(error CORPUS_VERSION is undefined)
endif

ifndef METADATA_VERSION
$(error METADATA_VERSION is undefined)
endif

include ./Makefile.dev

log_file=$(date "+%Y%m%d%H%M%S"`_"deploy_${target_db_name}_${source_type}.log)

CONFIG_FILENAME:="configs/config_$(CORPUS_VERSION)_$(METADATA_VERSION).yml"

config: $(CONFIG_FILENAME)
	@echo "info: Config file $(CONFIG_FILENAME) is up to date"

$(CONFIG_FILENAME): .env
	@python -c "from pyriksprot.utility import generate_default_config; \
	generate_default_config( \
		target_filename='$(CONFIG_FILENAME)', \
		root_folder='/data/riksdagen_corpus_data', \
		corpus_version='$(CORPUS_VERSION)', \
		corpus_folder='/data/riksdagen_corpus_data/riksdagen-records/data', \
		metadata_version='$(METADATA_VERSION)',
		stanza_datadir='$(STANZA_DATADIR)' \
    )"

# DATA_FOLDER=$(shell yq '.data_folder' $(CONFIG_FILENAME))
# CORPUS_FOLDER=$(shell yq '.corpus.folder' $(CONFIG_FILENAME))
# TARGET_FOLDER=$(shell yq '.tagged_frames.folder' $(CONFIG_FILENAME))
# CORPUS_VERSION=$(shell yq '.corpus.version' $(CONFIG_FILENAME))
# METADATA_VERSION=$(shell yq '.metadata.version' $(CONFIG_FILENAME))

.PHONY: tag-it
tag-it:
	@poetry run ./pyriksprot_tagger/scripts/tag.sh \
		--root-folder $(DATA_FOLDER) \
		--corpus-folder $(CORPUS_FOLDER) \
		--target-folder $(TARGET_FOLDER) \
		--corpus-version $(CORPUS_VERSION) \
		--metadata-version $(METADATA_VERSION) \
		--max-procs 4

.PHONY: tag-it

TEST_CONFIG_FILENAME=tests/output/config.yml

$(TEST_CONFIG_FILENAME): .env
	@echo "info: Generating test config file $(TEST_CONFIG_FILENAME)"
	@python -c "from pyriksprot.utility import generate_default_config; \
	generate_default_config( \
		target_filename='$(TEST_CONFIG_FILENAME)', \
		root_folder='tests/test_data/source', \
		corpus_version='$(CORPUS_VERSION)', \
		corpus_folder='tests/test_data/source/$(CORPUS_VERSION)/riksdagen-records', \
		metadata_version='$(METADATA_VERSION)',
		stanza_datadir='$(STANZA_DATADIR)' \
    )"
# Same as above 
# @make-config 
# 	--corpus-version $(CORPUS_VERSION) 
# 	--metadata-version $(METADATA_VERSION) 
# 	--root-folder tests/test_data/source 
# 	--corpus-folder tests/test_data/source/$(CORPUS_VERSION)/riksdagen-records


tag-test-data: $(TEST_CONFIG_FILENAME)
	@./pyriksprot_tagger/scripts/tag.sh \
		--root-folder $(shell yq '.data_folder' $(TEST_CONFIG_FILENAME)) \
		--corpus-folder $(shell yq '.corpus.folder' $(TEST_CONFIG_FILENAME)) \
		--target-folder $(shell yq '.tagged_frames.folder' $(TEST_CONFIG_FILENAME)) \
		--corpus-version $(shell yq '.corpus.version' $(TEST_CONFIG_FILENAME)) \
		--metadata-version $(shell yq '.metadata.version' $(TEST_CONFIG_FILENAME)) \
		--max-procs 4

vrt-test-data:
	@PYTHONPATH=. poetry run riksprot2vrt \
		--source-folder tests/test_data/source/$(CORPUS_VERSION)/tagged_frames/ \
			--target-folder tests/test_data/source/$(CORPUS_VERSION)/vrt/ -t protocol -t speech --batch-tag year
