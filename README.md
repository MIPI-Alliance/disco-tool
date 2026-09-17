# A DisCo tool Python project

This is the README file for the project.

The file should use UTF-8 encoding and can be written using
[reStructuredText][rst] or [markdown][md use] with the appropriate [key set][md
use]. It will be used to generate the project webpage on PyPI and will be
displayed as the project homepage on common code-hosting services, and should be
written for that purpose.

Typical contents for this file would include an overview of the project, basic
usage examples, etc. Generally, including the project changelog in here is not a
good idea, although a simple “What's New” section for the most recent version
may be appropriate.

#how to install disco
#linux
python -m pip install git+https://github.com/MIPI-Alliance/disco-tool.git
#Windows
py -m pip install git+https://github.com/MIPI-Alliance/private-disco-tool.git


# Compiling into single .exe using pyinstaller
pyinstaller --onefile --console --clean --collect-all wx --add-data=".\private-disco-tool\src\disco\images;images"  .\private-disco-tool\src\disco\disco_aui_manager.py
