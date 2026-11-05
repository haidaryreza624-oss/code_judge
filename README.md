Below is a complete, pasteable setup guide for configuring the Judge Engine on a completely new Windows machine.

It assumes Python, g++, and Java are already installed, but their installation locations are unknown.

# CodeArena Judge Engine – New Machine Setup

## 1. Open PowerShell and locate the installed tools

First, check Python:

```
python --version
where.exe python
```

Check g++:

```
g++ --version
where.exe g++
```

Check Java compiler and runtime:

```
javac -version
where.exe javac

java -version
where.exe java
```

Important: `javac` and `java` must both use Java 21. If they show different versions, fix the Java PATH before continuing.

## 2. Automatically configure environment variables

Instead of manually searching for installation directories, let Windows locate the executables.

Run:

```
$GPP = (Get-Command g++).Source
$JAVAC = (Get-Command javac).Source
$JAVA = (Get-Command java).Source

$GPP_DIR = Split-Path $GPP
$JDK_BIN = Split-Path $JAVAC

$env:JAVA_HOME = Split-Path $JDK_BIN
$env:Path = "$GPP_DIR;$JDK_BIN;$env:Path"
```

Verify:

```
python -c "import shutil; print('g++:', shutil.which('g++')); print('javac:', shutil.which('javac')); print('java:', shutil.which('java'))"
```

Check that Java 21 is being used:

```
java -version
javac -version
```

If any executable cannot be found, install the missing tool or add its installation directory to PATH first.

## 3. Get the Judge Engine project

Clone your repository:

```
git clone 
```

Or navigate to an existing project:

```
cd D:\code_judge
```

Make sure you are in the directory containing:

```
app/
tests/
requirements.txt
README.md
```

## 4. Create a Python virtual environment

```
python -m venv .venv


Activate it:

```
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```
python -m pip install --upgrade pip
```

## 5. Install project requirements

Install all dependencies:

```
python -m pip install -r requirements.txt
```

Install the tested pytest versions:

```
python -m pip install pytest==8.3.5 pluggy==1.5.0
```

## 6. Verify the complete environment

Run:

```
python -c "import sys, shutil, pytest, pluggy; print('Python:', sys.version); print('Python executable:', sys.executable); print('pytest:', pytest.__version__); print('pluggy:', pluggy.__version__); print('g++:', shutil.which('g++')); print('javac:', shutil.which('javac')); print('java:', shutil.which('java'))"
```

Expected:

| Component | Expected                           |
| --------- | ---------------------------------- |
| Python    | 3.10 or compatible project version |
| pytest    | 8.3.5                              |
| pluggy    | 1.5.0                              |
| g++       | Valid executable path              |
| javac     | Valid executable path              |
| java      | Valid executable path              |

None of the compiler paths should show `None`.

## 7. Run the tests

Make sure `.venv` is activated and run:

```
python -m pytest -v
```

Expected result:

```
14 passed
```

The tests cover:

- Python: 4 tests
- C++: 5 tests
- Java: 5 tests

## 8. Start the Judge Engine

Start the FastAPI server:

```
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the API documentation:

```
http://127.0.0.1:8000/docs
```

You can now test your submission endpoints.

## Important notes

1. The `$env:` configurations apply only to the current PowerShell session. Repeat the configuration when opening a new terminal, or configure Windows PATH permanently.
2. Always activate `.venv` before running the Judge Engine.
3. The server must have Python, g++, and Java installed and accessible through PATH.
4. The current queue is in-memory, so pending jobs disappear when the server restarts.
5. The current implementation does not isolate submitted programs. Do not expose it to untrusted student submissions until proper sandboxing and resource enforcement are implemented.

Setup sequence to remember:

```
Install/check tools
       ↓
Configure PATH
       ↓
Clone project
       ↓
Create virtual environment
       ↓
Install requirements
       ↓
Verify compilers
       ↓
Run 14 tests
       ↓
Start FastAPI
```