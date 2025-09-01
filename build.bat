pushd %~dp0
pyinstaller --onefile --clean --manifest app.manifest %~dp0/app.py
popd