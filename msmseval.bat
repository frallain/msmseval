
@echo off
: usage : msmseval.bat fichier.mgf
: python_path a configurer
: msconvert_path a configurer

set mgffilename="%~d1%~p1%~n1.mgf"
echo %mgffilename%
REM set msconvert_path="C:\Program Files\ProteoWizard\ProteoWizard 3.0.6906\msconvert.exe"
set msconvert_path="C:\Program Files\ProteoWizard\ProteoWizard 3.0.6909\msconvert.exe"
set python_path="c:\Python26\python.exe"

%python_path% "msmseval.py" -i %mgffilename% -p "msmsEval.params" -n 5000 -c %msconvert_path%



