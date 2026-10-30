#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"
python3 -m PyInstaller --noconfirm --console --name DocFlowEngine --paths "$project_dir" --paths "$project_dir/vendor" --add-data "$project_dir/web:web" --add-data "$project_dir/examples:examples" --add-data "$project_dir/vendor/PYPDF_LICENSE.txt:." --distpath build/engine --workpath build/work --specpath build server.py
python3 assemble_macos.py build/engine/DocFlowEngine dist/DocFlow.app
