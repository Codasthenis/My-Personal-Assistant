#!/bin/sh
set -e
cd /home/container
python <<'BOTKEEP_PIP_CACHE_V1'
"""Runs inside the customer container, never as a host installer.

Reuses only a successful installation of simple index requirements whose inputs
and installed file metadata still match. Complex/local/VCS/configured installs
keep the previous pip behavior. No package cache or credentials are shared.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import site
import stat
import subprocess
import sys
import time

STAMP = Path('.botkeep/pip-install-state-v1.json')
MAX_FILES = 20000
MAX_SCAN_SECONDS = 3


def digest(value):
    return hashlib.sha256(value).hexdigest()


def input_details():
    launch = Path('.botkeep/launch.sh')
    s = launch.stat()
    env = {k: digest(v.encode()) for k, v in sorted(os.environ.items())
           if k not in {'HOSTNAME', 'SHLVL', '_', 'PWD', 'OLDPWD'}}
    return {
        'version': 1, 'python': sys.version, 'executable': sys.executable,
        'prefix': sys.prefix, 'base': sys.base_prefix, 'env': env,
        'launch': [digest(launch.read_bytes()), s.st_mtime_ns, s.st_ino],
        'requirements': digest(Path('requirements.txt').read_bytes()),
    }


def inputs():
    return digest(json.dumps(input_details(), sort_keys=True).encode())


def reusable_project():
    p = Path('requirements.txt')
    if p.is_symlink() or p.stat().st_size > 262144:
        return False
    # Reject option files, local paths, VCS, URL and editable dependencies.
    # Markers/extras are retained; pip remains the authoritative resolver.
    for raw in p.read_text().splitlines():
        line = raw.split(' #', 1)[0].strip()
        if not line or line.startswith('#'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.\[\],<>=!~; \'"()*+-]*', line):
            return False
    # Custom pip settings can request upgrades/targets/force-reinstallation.
    # Do not claim equivalent reuse for those configurations.
    if any(k.startswith('PIP_') for k in os.environ):
        return False
    configs = [Path('/etc/pip.conf'), Path(sys.prefix)/'pip.conf',
               Path.home()/'.pip/pip.conf', Path.home()/'.config/pip/pip.conf']
    configs += [Path(x)/'pip/pip.conf' for x in
                os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':') if x]
    if os.environ.get('XDG_CONFIG_HOME'):
        configs.append(Path(os.environ['XDG_CONFIG_HOME'])/'pip/pip.conf')
    return not any(p.exists() for p in configs)


def tree_state():
    """Bounded stat scan, no import of pip or customer modules, no file reads.

    Missing, changed, added files and symlinks invalidate reuse. Ignore only
    Python bytecode, which the application legitimately generates at runtime.
    """
    started = time.monotonic()
    roots = [Path(site.getusersitepackages()), Path(site.getuserbase())/'bin']
    roots += [Path(p) for p in site.getsitepackages()]
    rows = []
    for root in sorted(set(roots)):
        if root.is_symlink():
            return None
        if not root.exists():
            rows.append([str(root), 'absent'])
            continue
        for parent, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d != '__pycache__')
            for name in dirs:
                if (Path(parent)/name).is_symlink():
                    return None
            for name in sorted(files):
                if name.endswith(('.pyc', '.pyo')):
                    continue
                p = Path(parent)/name
                s = p.lstat()
                if not stat.S_ISREG(s.st_mode):
                    return None
                # Wings repairs ownership on every boot; even an unchanged
                # chown updates ctime. Compare actual ownership/mode, not ctime.
                rows.append([str(p), s.st_ino, s.st_size, s.st_mtime_ns,
                             s.st_mode & 0o777, s.st_uid, s.st_gid])
                if len(rows) > MAX_FILES or time.monotonic()-started > MAX_SCAN_SECONDS:
                    return None
    return digest(json.dumps(rows, separators=(',', ':')).encode())


def main():
    if not Path('requirements.txt').is_file():
        return 0
    before = None
    cacheable = False
    try:
        cacheable = reusable_project()
        if cacheable:
            before = inputs()
        if cacheable and os.environ.get('BOTKEEP_REINSTALL') != '1' and STAMP.stat().st_size < 16384:
            old = json.loads(STAMP.read_text())
            if old.get('input') != before and isinstance(old.get('details'), dict):
                current_details = input_details()
                changed = [k for k in current_details if current_details[k] != old['details'].get(k)]
                if 'env' in changed:
                    changed += ['env:'+k for k in set(current_details['env']) | set(old['details'].get('env', {}))
                                if current_details['env'].get(k) != old['details'].get('env', {}).get(k)]
                print('[Botkeep] Dependency inputs changed: '+', '.join(sorted(changed)), flush=True)
            if old.get('input') == before and old.get('tree'):
                current = tree_state()
                if current and current == old['tree']:
                    print('[Botkeep] Dependencies unchanged; reusing the successful Python installation.', flush=True)
                    return 0
    except (OSError, ValueError, TypeError, KeyError):
        pass
    try:
        STAMP.unlink(missing_ok=True)
    except OSError:
        cacheable = False
    print('[Botkeep] Checking Python dependencies; reuse requires a successful unchanged installation.', flush=True)
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user',
                             '--no-cache-dir', '--disable-pip-version-check', '-r', 'requirements.txt'])
    if result.returncode:
        print('[Botkeep] Dependency installation failed; no successful cache saved.', flush=True)
        return result.returncode if result.returncode > 0 else 1
    try:
        if cacheable and before == inputs():
            tree = tree_state()
            if tree:
                tmp = STAMP.with_name(STAMP.name + '.' + str(os.getpid()) + '.tmp')
                with tmp.open('x') as out:
                    os.chmod(tmp, 0o600)
                    json.dump({'input': before, 'tree': tree, 'details':input_details()}, out)
                os.replace(tmp, STAMP)
    except (OSError, ValueError, TypeError):
        print('[Botkeep] Dependency cache unavailable; next startup checks normally.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

BOTKEEP_PIP_CACHE_V1
printf '__BOTKEEP_PROCESS_START__\n';
python -m uvicorn api:app --host 0.0.0.0 --port 61112
