#!/bin/bash
export OMP_NUM_THREADS=16
export PYTHONPATH=.

source .env

g_corpus_version=
g_corpus_folder=
g_metadata_version=
g_root_folder=
g_target_folder=
g_source_pattern="*"
g_force=no
g_update=1
g_max_procs=1
g_now_timestamp=$(date "+%Y%m%d_%H%M%S")
g_log_dir=./logs
g_scriptname=$(basename $0)
g_repository_name=riksdagen-records
g_repository_folder=
g_word_frequency_filename=
g_stanza_datadir=/data/sparv/models/stanza

function usage()
{
    if [ "$1" != "" ]; then
        echo "error: $1"
    fi
    echo "usage: ./${scriptname} [--root-folder folder]  [--corpus-folder folder] --target-folder folder --corpus-version version --metadata-version version [--force] [--update] [--max-procs n]]"
    echo "Tags XML files found in corpus folder and its subfolders."
    echo ""
    echo "   --root-folder             root data and metadata folder (dehyphen, models, TF etc.)"
    echo "   --corpus-version          source corpus version"
    echo "   --metadata-version        source metadata version"
    echo "   --corpus-folder           source corpus folder"
    echo "   --source-pattern          source folder pattern"
    echo "   --target-folder           target folder"
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
        --source-pattern)
            g_source_pattern="$2"; shift; shift
        ;;
        --target-folder)
            g_target_folder="$2"; shift; shift
        ;;
        --max-procs)
            g_max_procs="$2"; shift; shift
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

if [ "$g_root_folder" == "" ]; then
    usage "root folder not specified"
    exit 64
fi

if [ ! -d "$g_root_folder" ]; then
    usage "data folder doesn't exist"
    exit 64
fi

if [ "$g_corpus_folder" == "" ]; then
    usage "source corpus folder not specified"
    exit 64
fi

if [ "$g_corpus_version" == "" ]; then
    usage "corpus version not specified"
    exit 64
fi

if [ "$g_metadata_version" == "" ]; then
    usage "metadata version not specified"
    exit 64
fi

if [ ! -d "$g_corpus_folder" ]; then
    usage  "corpus folder doesn't exist"
    exit 64
fi

if [ "$g_target_folder" == "" ]; then
    usage "target folder not specified" ;
    exit 64
fi

if [ -d "$g_target_folder" ]; then
    if [ "$g_force" == "yes" ]; then
        echo "info: running in force mode, dropping existing target" ;
        echo rm -rf $g_target_folder ;
    elif [ $g_update == 0 ]; then
        echo "error: target folder exists (use --force or --update to remove/update existing tagging)" ;
        exit 64 ;
    fi
fi

if [[ $g_max_procs < 1 || $g_max_procs > 6 ]]; then
    echo "error: max procs must be an integer between 1 and 6" ;
    exit 64
fi

g_word_frequency_filename=${g_root_folder}/${g_corpus_version}/dehyphen/word-frequencies.pkl

mkdir -p ${g_target_folder} ${g_log_dir}

pushd "$g_corpus_folder" > /dev/null || exit 1
g_repository_folder=$(git rev-parse --show-toplevel 2> /dev/null || echo "")
popd > /dev/null

if ! expr "${g_corpus_folder}" : ".*${g_repository_name}$" > /dev/null; then
    echo "info: repository folder is ${g_repository_folder}, skipping tags check..." ;
    g_repository_folder="" ;
else
    echo "info: repository folder is ${g_repository_folder}, checking that tags match..." ;
fi

function ensure_corpus_version_is_same_as_workdir()
{
    if [ "$g_repository_folder" != "" ]; then

        workdir_tag=undefined
        if command -v "$tag_info" > /dev/null; then
            workdir_tag=$(tag_info --key tag ${corpus_folder})
        elif [ -f "pyriksprot_tagger/scripts/tag_info.py" ]; then
            export PYTHONPATH=.
            workdir_tag=$(poetry run python pyriksprot_tagger/scripts/tag_info.py --key tag ${g_repository_folder})
        else

            tag_info_filename=$(python - "$input" <<'END_SCRIPT'
import pyriksprot_tagger, os
print(os.path.join(os.path.dirname(pyriksprot_tagger.__file__), "scripts/tag_info.py"))
END_SCRIPT
)

            if [ -f "$tag_info_filename" ]; then
                workdir_tag=$(poetry run python ${tag_info_filename} --key tag ${g_repository_folder})
            else
                echo "error: tag_info not found - unable to verify that workdir tag is ${corpus_version}"
                exit 64 ;
            fi
        fi

        if [ "$corpus_version" != "$workdir_tag" ]; then
            echo "error: workdir tag is $workdir_tag, expected ${corpus_version}" ;
            exit 64 ;
        fi

        tag_info $g_repository_folder > ${target_folder}/version.yml

    fi
}

ensure_corpus_version_is_same_as_workdir

echo $corpus_version > ${target_folder}/version

sub_folders=`find ${g_corpus_folder} -maxdepth 1 -mindepth 1 -name "${g_source_pattern}" -type d -printf '%f\n' | sort`

yaml_file=$g_log_dir/tag_config_${now_timestamp}.yml

echo "info: corpus version: $g_corpus_version"
echo "info: metadata version: $g_metadata_version"
echo "info: force: $g_force"
echo "info: root folder: $g_root_folder"
echo "info: corpus folder: $g_corpus_folder"
echo "info: target folder: $g_target_folder"
echo "info: word frequency filename: $g_word_frequency_filename"

poetry run jinja2 configs/template.yml.j2 \
    -D root_folder=$g_root_folder \
    -D corpus_version=$g_corpus_version \
    -D corpus_folder=$g_corpus_folder \
    -D metadata_version=$g_metadata_version \
    -D stanza_datadir=$g_stanza_datadir > $yaml_file

echo "info: using configuration file $yaml_file"
cp $yaml_file ${target_folder}/tag_config.yml

echo "info: using $g_max_procs processes"
if [ -f "${g_word_frequency_filename}" ]; then
    if [ "$g_force" == "yes" ]; then
        echo "info: force mode, dropping existing word frequency file: ${g_word_frequency_filename}"
        rm -f ${g_word_frequency_filename}
    else
        echo "info: word frequency file exists: ${g_word_frequency_filename}"
    fi

fi

if [ ! -f "${g_word_frequency_filename}" ]; then
    echo "info: generating word frequency file ${g_word_frequency_filename}..."
    riksprot2tfs $yaml_file
fi

# if [ ! command -v "pos_tag" > /dev/null ]; then
#     echo "error: pos_tag command not found - unable to run tagging"
#     echo " info: install the `pyriksprot_tagger` package and make sure that the pos_tag command is available"
#     exit 64 ;
# fi

if [[ $max_procs > 1 ]]; then

    tag_command_file="$log_dir/tag_commands_${now_timestamp}.txt"

    echo "command file: $tag_command_file"

    rm -rf $tag_command_file

    for sub_folder in $sub_folders; do
        echo "poetry run python ./pyriksprot_tagger/scripts/tag.py $yaml_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder" >> ${tag_command_file}
        # echo "pos_tag  $yaml_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder" >> ${tag_command_file}
    done

    echo "info: running in parallel mode using $max_procs processes"
    cat $tag_command_file | xargs -I CMD --max-procs=$max_procs bash -c CMD

else
    echo "info: running in sequential mode"
    for sub_folder in $sub_folders; do
        PYTHONPATH=. python ./pyriksprot_tagger/scripts/tag.py $yaml_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder
        # PYTHONPATH=. pos_tag $yaml_file ${corpus_folder}/$sub_folder ${target_folder}/$sub_folder 
    done
fi
