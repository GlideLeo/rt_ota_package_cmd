$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition
cd $dir
conda activate package
python .\Package.py -c .\config.json