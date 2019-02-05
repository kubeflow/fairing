import os

if os.getenv('FAIRING_RUNTIME', None) != None:
  from fairing.runtime_config import config
else:
  from fairing.config import config

name = "fairing"
