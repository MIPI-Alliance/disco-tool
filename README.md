# A DisCo tool Python project

# How to install disco

### linux
python -m pip install git+https://github.com/MIPI-Alliance/private-disco-tool.git
### Windows
py -m pip install git+https://github.com/MIPI-Alliance/private-disco-tool.git

# For Developers:

1. **Clone the repository** and move into the project directory:

   ```powershell
   git clone https://github.com/MIPI-Alliance/disco-tool
   cd private-disco-tool
   ```

2. **Create and activate a virtual environment** (recommended):

   Installing dependencies to a virtual environment avoids conflicts with the existing version of Python and Python libraries on your machine.

   ```bash
   # linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   ```powershell
   # Windows
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

---

## Running the Application

From the root (`private-disco-tool`) move into the package folder and run the main file:

```bash
# linux
python3 src/disco/disco_aui_manager.py
```

```powershell
# Windows
python src\disco\disco_aui_manager.py
```

When debugging in an IDE such as VS Code, set `src/disco/disco_aui_manager.py` as the startup file.


## Running Tests

The unit tests live in `src\disco\test.py` and use Python's `unittest` framework.

From the repository root (`private-disco-tool`), run the test file with:

```bash
# linux
python3 src/disco/test.py
```

```powershell
# Windows
python src\disco\test.py
```

The test file will write the results to **`log_file.txt`**.

# Compiling into single .exe using pyinstaller
```powershell
# Windows
pyinstaller --onefile --console --clean --collect-all wx --add-data=".\private-disco-tool\src\disco\images;images" .\private-disco-tool\src\disco\disco_aui_manager.py
```
The build file will be created at `private-disco-tool\dist`\. When releaseing the file, please zip the executable and use the following naming convention: `DisCo_Tool_v1.x.x.zip`.
