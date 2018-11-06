import subprocess
import os
import stat
import json
from pkg_resources import resource_filename
import platform
import requests
import tempfile
import zipfile
import tarfile
import shutil
import logging

logger = logging.getLogger('fairing')

def get_mp_bin_path():
    plat = platform.system()
    if plat == "Linux":
        return resource_filename(__name__, "bin/metaparticle/linux/mp-compiler")
    elif plat == "Windows":
        return resource_filename(__name__, "bin/metaparticle/windows/mp-compiler.exe")
    elif plat == "Darwin":
        return resource_filename(__name__, "bin/metaparticle/darwin/mp-compiler")
    else:
        raise Exception("Your platform is not supported.")


def update_metaparticle():
    # TODO: we should dynamically find the latest tag using the github API
    # this would allow updating metaparticle without needing a new release of fairing

    # repo = "https://github.com/wbuchwalter/metaparticle-ast"
    # re = "https:\/\/[a-z\.\/-]*tag\/v[0-9].[0-9].[0-9]"
    # requests.get("{repo}/releases/latest".format(repo=repo), headers=headers)

    logger.warn('Downloading Metaparticle compiler...')
    base_url = "https://github.com/wbuchwalter/metaparticle-ast/releases/download/v0.6.0"
    plat = platform.system().lower()
    ext = 'zip' if plat == 'windows' else 'tar.gz'
    full_url = "{base_url}/mp-compiler-{plat}-amd64.{ext}".format(
        base_url=base_url,
        plat=plat,
        ext=ext
    )
    r = requests.get(full_url, allow_redirects=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = os.path.join(tmp_dir, 'mp-archive')
        open(archive_path, 'wb+').write(r.content)

        archive = None
        file_name = 'mp-compiler'
        if plat == 'windows':
            archive = zipfile.ZipFile(archive_path)
            file_name += '.exe'
        else:
            archive = tarfile.open(archive_path)
        archive.extractall(tmp_dir)
        archive.close()
        
        logger.warn('Installing compiler at %s' %  get_mp_bin_path())

        dir_path = os.path.dirname(get_mp_bin_path())
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        shutil.move(os.path.join(tmp_dir, file_name), dir_path)

        os.chmod(get_mp_bin_path(),  stat.S_IEXEC |
                                     stat.S_IREAD |
                                     stat.S_IRGRP |
                                     stat.S_IXGRP |
                                     stat.S_IWRITE |
                                     stat.S_IXOTH |
                                     stat.S_IROTH)
    logger.warn('Metaparticle compiler succesfully installed.')

def ensure_metaparticle_present():
    install_path = get_mp_bin_path()
    if os.path.exists(install_path):
        return
    update_metaparticle()


ensure_metaparticle_present()


class MetaparticleClient(object):

    def run(self, svc):
        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)

        subprocess.check_call([get_mp_bin_path(), '-f', '.metaparticle/spec.json'])

    def cancel(self, name):
        subprocess.check_call(
            [get_mp_bin_path(), '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            [get_mp_bin_path(), '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])
