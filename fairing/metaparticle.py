import subprocess
import os
import json

def run(svc):
    if not os.path.exists('.metaparticle'):
        os.makedirs('.metaparticle')

    with open('.metaparticle/spec.json', 'w') as out:
        json.dump(svc, out)

    subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])


def cancel(name):
    subprocess.check_call(
        ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])


def logs(name):
    subprocess.check_call(
        ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])
