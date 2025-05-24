#!/bin/bash
export OMP_NUM_THREADS=16
export PYTHONPATH=.

source .env

g_config_file=

g_corpus_version=
g_corpus_folder=
g_metadata_version=
g_root_folder=
g_target_folder=
g_stanza_datadir=/data/sparv/models/stanza

g_force=no
g_update=1
MAX_PROCS=1
g_now_timestamp=$(date "+%Y%m%d_%H%M%S")
g_scriptname=$(basename $0)

function usage()
{
    if [ "$1" != "" ]; then
        echo "error: $1"
    fi
    echo "usage: ./${scriptname} [--config-file config.yml] [--root-folder folder]  [--corpus-folder folder] --target-folder folder --corpus-version version --metadata-version version [--force] [--update] [--max-procs n]]"
    echo "Tags XML files found in corpus folder and its subfolders."
    echo ""
    echo "   --config-file             use settings in configuration file"
    echo " or "
    echo "   --root-folder             root data and metadata folder (dehyphen, models, TF etc.)"
    echo "   --corpus-version          source corpus version"
    echo "   --metadata-version        source metadata version"
    echo "   --corpus-folder           source corpus folder"
    echo "   --target-folder           tagged frames target folder"
    echo " "
    echo "   --subfolder-pattern       source subfolder pattern"
    echo "   --force                   drop target if exists"
    echo "   --update                  update target if exists"
    echo "   --max-procs               max number of parallel jobs"
    
    echo ""
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --config-file)
            g_config_file="$2"; shift; shift
        ;;
        --stanza-datadir)
            g_stanza_datadir="$2"; shift; shift
        ;;
        --corpus-version)
            g_corpus_version="$2"; shift; shift
        ;;
        --metadata-version)
            g_metadata_version="$2"; shift; shift
        ;;
        --root-folder|--data-folder)
            g_root_folder="$2"; shift; shift
        ;;
        --corpus-folder)
            corpus_folder="$2"; shift; shift
        ;;
        --target-folder)
            g_target_folder="$2"; shift; shift
        ;;
        --max-procs)
            MAX_PROCS="$2"; shift; shift
        ;;
        --force)
            g_force=yes ;
        ;;
        --update)
            g_update=1 ;
        ;;
        --help)
            usage ;
            exit 0
        ;;
        --*)
            usage "unknown option $1" ;
            exit 0
        ;;
        *)
        POSITIONAL+=("$1")
        shift
        ;;
    esac
done

set -- "${POSITIONAL[@]}"

function check_and_persist_config()
{
    if [ "$g_config_file" != "" ]; then
        if [ ! -f "$g_config_file" ]; then
            usage "configuration file not found: $g_config_file"
            exit 64
        fi
        if [ "${g_root_folder}${g_corpus_folder}${g_target_folder}${g_corpus_version}${g_metadata_version}" != "" ]; then
            echo "error: config file and command line options are mutually exclusive" ;
            exit 64 ;
        fi
    else
        if [ "$g_root_folder" == "" ] || [ ! -d "$g_root_folder" ]; then
            usage "root folder not specified or doesn't exist"
            exit 64
        fi

        if [ "$g_corpus_folder" == "" ] ||  [ ! -d "$g_corpus_folder" ]; then
            usage "source corpus folder not specified or doesn't exist"
            exit 64
        fi

        if [ "$g_corpus_version" == "" ] || [ "$g_metadata_version" == "" ]; then
            usage "corpus and/or metadata version not specified"
            exit 64
        fi
        if [ "$g_target_folder" == "" ]; then
            usage "target folder not specified" ;
            exit 64
        fi

        g_config_file=config_${g_corpus_version}_${g_metadata_version}_${g_now_timestamp}.yml

        make-config $g_config_file \
            --corpus-version $g_corpus_version \
            --metadata-version $g_metadata_version \
            --root-folder ${g_root_folder:-$1} \
            --corpus-folder $g_corpus_folder \
            --stanza-datadir $g_stanza_datadir
    fi

    if [[ $MAX_PROCS < 1 || $MAX_PROCS > 6 ]]; then
        echo "error: max procs must be an integer between 1 and 6" ;
        exit 64
    fi

}

function update_word_frequency()
{
    local config_file=$1
    local tf_filename=$(yq -r '.dehyphen.tf_filename' "$config_file")

    if [ -f "${tf_filename}" ]; then
        if [ "$g_force" == "yes" ]; then
            echo "info: force mode, dropping existing word frequency file: ${tf_filename}"
            rm -f ${tf_filename}
        else
            echo "info: word frequency file exists: ${tf_filename}"
        fi
    fi

    if [ ! -f "${tf_filename}" ]; then
        echo "info: generating word frequency file ${tf_filename}..."
        riksprot2tfs "${config_file}"  "${tf_filename}"
    fi
}


function reset_target_folder()
{
    local config_file=$1
    local target_folder=$(yq -r '.tagged_frames.folder' "$config_file")
    local corpus_version=$(yq -r '.corpus.version' "$config_file")
    local metadata_version=$(yq -r '.metadata.version' "$config_file")

    if [ -d "$target_folder" ]; then
        echo "info: removing existing target folder $target_folder"
        rm -rf $target_folder
    fi
    if [ -d "$target_folder" ]; then
        if [ "$g_force" == "yes" ]; then
            echo "info: running in force mode, dropping existing target" ;
            echo rm -rf $target_folder ;
        elif [ $g_update == 0 ]; then
            echo "error: target folder exists (use --force or --update to remove/update existing tagging)" ;
            exit 64 ;
        fi
    fi

    local log_dir="logs/${corpus_version}"

    mkdir -p ${target_folder} ${log_dir}
    echo $(yq -r '.corpus.version' "$config_file") > ${target_folder}/version
    echo $(yq -r '.metadata.version' "$config_file") > ${target_folder}/metadata_version

    cp -f $config_file ${target_folder}/config_${corpus_version}_${metadata_version}.yml
    cp -f $config_file $log_dir/tag_config_${g_now_timestamp}.yml
}

function show_settings()
{
    local config_file=$1

    echo "info: configuration file:" $config_file
    echo ""
    echo "info: corpus version:"      $(yq -r '.corpus.version' "$config_file")
    echo "info: metadata version:"    $(yq -r '.metadata.version' "$config_file")
    echo "info: root folder:"         $(yq -r '.root_folder' "$config_file")
    echo "info: corpus folder:"       $(yq -r '.corpus.folder' "$config_file")
    echo "info: target folder:"       $(yq -r '.tagged_frames.folder' "$config_file")
    echo "info: word frequency file:" $(yq -r '.dehyphen.tf_filename' "$config_file")
    echo ""
    echo "info: force: $g_force"
    echo "info: using $MAX_PROCS processes"
}

function tagit()
{
    local config_file=$1
    local corpus_folder=$(yq -r '.corpus.folder' "$config_file")
    local corpus_version=$(yq -r '.corpus.version' "$config_file")
    local log_dir="logs/${corpus_version}"
    local sub_folders=`find ${corpus_folder} -maxdepth 1 -mindepth 1 -name "*" -type d -printf '%f\n' | sort`
    local target_folder=$(yq -r '.tagged_frames.folder' "$config_file")

    if [[ $MAX_PROCS > 1 ]]; then

        tag_command_file="$log_dir/tag_commands_${g_now_timestamp}.txt"

        echo "command file: $tag_command_file"
        rm -f $tag_command_file

        for sub_folder in $sub_folders; do
            echo "poetry run python ./pyriksprot_tagger/scripts/tag.py --skip-version-check $config_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder" >> ${tag_command_file}
            # echo "pos_tag  $config_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder" >> ${tag_command_file}
        done
        echo "info: running in parallel mode using $MAX_PROCS processes"
        cat $tag_command_file | xargs -I CMD --max-procs=$MAX_PROCS bash -c CMD

    else
        echo "info: running in sequential mode"
        for sub_folder in $sub_folders; do
            PYTHONPATH=. python ./pyriksprot_tagger/scripts/tag.py --skip-version-check $config_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder
            # PYTHONPATH=. pos_tag $config_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder 
        done
    fi
}

check_and_persist_config
show_settings $g_config_file
reset_target_folder $g_config_file
update_word_frequency $g_config_file
tagit $g_config_file

