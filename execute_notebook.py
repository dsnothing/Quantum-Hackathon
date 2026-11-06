import sys, os
from pathlib import Path
root=Path(__file__).resolve().parent
for env, name in [('IPYTHONDIR','ipython'),('JUPYTER_CONFIG_DIR','jupyter-config'),('JUPYTER_DATA_DIR','jupyter-data'),('JUPYTER_RUNTIME_DIR','jupyter-runtime')]:
    dest=root/'build'/name; dest.mkdir(parents=True,exist_ok=True);os.environ[env]=str(dest)
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

nb=nbformat.read(root/'Quantum_2048.ipynb',as_version=4)
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
client=NotebookClient(nb,timeout=180,km=km,resources={'metadata':{'path':str(root)}})
client.execute()
nbformat.write(nb,root/'Quantum_2048.ipynb')
print('Executed every cell successfully in a fresh kernel.')
