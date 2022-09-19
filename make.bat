@echo on
set PY_FILE=mini_kit_creator.py
set PROJECT_NAME=Mini Kit Creator
set VERSION=1.0.0
set FILE_VERSION=file_version_info.txt
set EXTRA_ARG=--add-data=resources/*;resources --additional-hooks-dir=. 
set ICO_DIR=resources/pes_indie.ico

pyinstaller --onefile --window "%PY_FILE%" --name "%PROJECT_NAME%_%VERSION%"  %EXTRA_ARG% --version-file "%FILE_VERSION%"

cd dist
tar -acvf "%PROJECT_NAME%_%VERSION%.zip" *
pause
