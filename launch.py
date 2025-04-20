import os
import subprocess

# This only runs Streamlit once
this_file = os.path.abspath("app.py")
subprocess.run(["streamlit", "run", this_file])
