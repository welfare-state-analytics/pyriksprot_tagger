include .env

include ./Makefile.dev
log_file=$(date "+%Y%m%d%H%M%S"`_"deploy_${target_db_name}_${source_type}.log)

tag-it:
	@nohup poetry run ./tag.sh --data-folder $(RIKSPROT_DATA_FOLDER) --tag $(RIKSPROT_REPOSITORY_TAG) --max-procs 4 --target-folder $(RIKSPROT_DATA_FOLDER)/tagged_frames/$(RIKSPROT_REPOSITORY_TAG) >> tag-it-$(RIKSPROT_REPOSITORY_TAG).nohup.log &

tag_test_cmd := import tests.utility as pu; pu.tag_test_data('tests/test_data/source', '$(RIKSPROT_REPOSITORY_TAG)')
tag-test-data:
	@PYTHONPATH=. poetry run python -c "$(tag_test_cmd)"

vrt-test-data:
	@PYTHONPATH=. poetry run riksprot2vrt --folder-batches tests/test_data/source/$(RIKSPROT_REPOSITORY_TAG)/tagged_frames/ \
		tests/test_data/source/$(RIKSPROT_REPOSITORY_TAG)/vrt/ -t protocol -t speech --batch-tag year

.PHONY: cwb
cwb:
	cwb-encode -d tests/output/cwb

.PHONY: image
image:
	@docker build \
		-t pyriksprot:latest -t pyriksprot:$(RIKSPROT_REPOSITORY_TAG) \
		--build-arg PACKAGE_VERSION=$(PACKAGE_VERSION) .

.PHONY: bash
bash:
	@docker run --gpus all -it --rm \
		--mount "type=bind,src=$(shell pwd),dst=/home/pyriksprot/work" \
		--mount "type=bind,src=/data,dst=/data" pyriksprot:latest /bin/bash

# echo "usage: tag-it [--data-folder folder] [--source-pattern pattern] --target-folder folder --tag tag [--force]"
# echo "Creates new database using source as template. Source defaults to production."
# echo ""
# echo "   --data-folder             source root folder"
# echo "   --target-folder           target folder"
# echo "   --tag                     source corpus tag"
# echo "   --source-pattern          source folder pattern"
# echo "   --force                   drop target if exists"
# echo "   --update                  update target if exists"
# echo "   --max-procs               max number of parallel jobs"
# echo ""
