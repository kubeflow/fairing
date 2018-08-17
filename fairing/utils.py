import os

def is_runtime_phase():
    """ Returns wether the code is currently in the runtime or building phase"""
    return os.getenv('FAIRING_RUNTIME', None) != None 
    
    # elif mp_in_container in ['false', '0']:
    #     return False

    # We should probably just stick with the environment variable
    # as the user may be running fairing in a container already
#   try:
#       with open('/proc/1/cgroup', 'r+t') as f:
#           lines = f.read().splitlines()
#           last_line = lines[-1]
#           if 'docker' in last_line:
#               return True
#           elif 'kubepods' in last_line:
#               return True
#           else:
#               return False

#   except IOError:
#       return False