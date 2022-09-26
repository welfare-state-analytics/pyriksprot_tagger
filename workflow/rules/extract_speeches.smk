# type: ignore
# pylint: skip-file, disable-all
"""
Transforms Para-Clarin XML file to TXT file
"""
from os.path import join as jj

from pyriksprot.parlaclarin.convert import convert_protocol

rule extract_speeches:
    message:
        "step: extract_speeches"
    # log:
    #     typed_config.log_filename,
    params:
        template=typed_config.extract_opts.template,
    input:
        filename=jj(typed_config.corpus.source_folder, "{year}", "{basename}.xml"),
    output:
        filename=jj(typed_config.tagged_frames_folder, "{year}", f"{{basename}}.{typed_config.target_extension}"),
    run:
        try:
            convert_protocol(input.filename, output.filename, params.template)
        except Exception as ex:
            print(
                f"failed: parla_transform {input.filename} --output-filename {output.filename} --template-name {params.template}"
            )
            raise
