include .env


include ./Makefile.dev
log_file=$(date "+%Y%m%d%H%M%S"`_"deploy_${target_db_name}_${source_type}.log)

DATA_FOLDER=$(shell yq '.data_folder' $(CONFIG_FILENAME))
CORPUS_FOLDER=$(shell yq '.corpus.folder' $(CONFIG_FILENAME))
TARGET_FOLDER=$(shell yq '.tagged_frames.folder' $(CONFIG_FILENAME))
VERSION=$(shell yq '.version' $(CONFIG_FILENAME))

.PHONY: tag-it
tag-it:
	@echo "info: Tagging data for version $(VERSION)"
	@echo "info: Using CORPUS_FOLDER: $(CORPUS_FOLDER)"
	@echo "info:       TARGET_FOLDER: $(TARGET_FOLDER)"
	@echo "info:       DATA_FOLDER: $(DATA_FOLDER)"
	@poetry run ./pyriksprot_tagger/scripts/tag.sh \
		--root-folder $(DATA_FOLDER) \
		--corpus-folder $(CORPUS_FOLDER) \
		--target-folder $(TARGET_FOLDER) \
		--tag $(VERSION) --max-procs 4 

.PHONY: tag-it

TEST_CONFIG_FILENAME=tests/config.yml
TEST_DATA_FOLDER=$(shell yq '.data_folder' $(TEST_CONFIG_FILENAME))
TEST_CORPUS_FOLDER=$(shell yq '.corpus.folder' $(TEST_CONFIG_FILENAME))
TEST_TARGET_FOLDER=$(shell yq '.tagged_frames.folder' $(TEST_CONFIG_FILENAME))
TEST_VERSION=$(shell yq '.version' $(TEST_CONFIG_FILENAME))

tag-test-data:
	@./pyriksprot_tagger/scripts/tag.sh \
		--root-folder $(TEST_DATA_FOLDER) \
		--corpus-folder $(TEST_CORPUS_FOLDER) \
		--target-folder $(TEST_TARGET_FOLDER) \
		--tag $(TEST_VERSION) --max-procs 4

vrt-test-data:
	@PYTHONPATH=. poetry run riksprot2vrt \
		--source-folder tests/test_data/source/$(VERSION)/tagged_frames/ \
			--target-folder tests/test_data/source/$(VERSION)/vrt/ -t protocol -t speech --batch-tag year

# .PHONY: cwb
# cwb:
# 	cwb-encode -d tests/output/cwb

