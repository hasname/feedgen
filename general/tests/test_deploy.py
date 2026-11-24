import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


class DeployTestCase(SimpleTestCase):
    root = Path(__file__).resolve().parents[2]

    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.bin = self.directory / 'cargo' / 'bin'
        self.bin.mkdir(parents=True)
        self.log = self.directory / 'commands.jsonl'
        self.env = {
            **os.environ,
            'PATH': f'{self.bin}:{os.environ["PATH"]}',
            'CARGO_HOME': str(self.directory / 'cargo'),
            'CLANG_PATH': '',
            'DEPLOY_TEST_LOG': str(self.log),
        }
        fake = self.directory / 'fake-command'
        fake.write_text(f'#!{sys.executable}\n' + '''
import json
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['DEPLOY_TEST_LOG'], 'a') as log:
    log.write(json.dumps([name, *args]) + '\\n')
if name == 'uname':
    print('Darwin')  # Host time zone configuration is checked in the real install.
elif name.startswith('clang'):
    source = sys.stdin.read()
    assert '#include <stddef.h>' in source and '#include <stdint.h>' in source
    if os.environ.get('DEPLOY_TEST_MISSING_HEADERS'):
        print("fatal error: 'stddef.h' file not found", file=sys.stderr)
        sys.exit(1)
elif name == 'ssh' and 'activate-cfsolve.sh' in args[-1]:
    sys.exit(int(os.environ.get('DEPLOY_TEST_FAIL_ACTIVATE', '0')))
elif name == 'rsync' and os.environ.get('DEPLOY_TEST_REAL_RSYNC'):
    os.execv(os.environ['DEPLOY_TEST_REAL_RSYNC'], ['rsync', *args])
elif name == 'git':
    if args[0] == 'clone':
        checkout = Path(args[-1])
        (checkout / '.git').mkdir(parents=True)
        (checkout / 'LICENSE').write_text('Upstream license')
        profiles = checkout / 'profiles'
        (profiles / 'safari-26-ios').mkdir(parents=True)
        for filename in ('safari-26-ios.json', 'safari-26-ios/answers.json',
                         'safari-26-ios/challenge-page-answers.json'):
            (profiles / filename).write_text('{}')
    elif args[0] == 'status':
        print(os.environ.get('DEPLOY_TEST_DIRTY', ''), end='')
elif name == 'cargo':
    with open(os.environ['DEPLOY_TEST_LOG'], 'a') as log:
        log.write(json.dumps(['bindgen-clang', os.environ.get('CLANG_PATH')]) + '\\n')
    if os.environ.get('DEPLOY_TEST_FAIL_BUILD'):
        sys.exit(19)
    binary = Path('target/release/challenge')
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text('#!/bin/sh\\nexit 0\\n')
    binary.chmod(0o755)
''')
        fake.chmod(0o755)
        for command in ('rsync', 'ssh', 'git', 'rustup', 'cargo', 'cmake', 'cc', 'c++', 'clang', 'uname'):
            (self.bin / command).symlink_to(fake)

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def deploy(self, **env):
        return subprocess.run(
            ['make', 'deploy', 'DEPLOY_USER=test-user', 'DEPLOY_HOST=example.test',
             f'CFSOLVE_SOURCE_DIR={self.directory / "cfsolve checkout"}'],
            cwd=self.root, env={**self.env, **env}, capture_output=True, text=True, check=False,
        )

    def install(self, **env):
        return subprocess.run(
            ['bash', str(self.root / 'scripts/install-cfsolve.sh'), str(self.directory / 'cfsolve')],
            env={**self.env, **env}, capture_output=True, text=True, check=False,
        )

    def runtime_upload(self):
        return next(command for command in self.commands()
                    if command[0] == 'rsync' and command[-1].endswith('.cfsolve-upload/'))

    def stage_runtime(self):
        rsync = shutil.which('rsync')
        if rsync is None:
            self.skipTest('rsync is not installed')
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stderr)
        staging = self.directory / 'staging'
        command = self.runtime_upload()
        subprocess.run([rsync, *command[1:-1], f'{staging}/'], check=True, capture_output=True)
        return staging

    def activate(self):
        return subprocess.run(
            ['bash', str(self.root / 'scripts/activate-cfsolve.sh'),
             str(self.directory / 'staging'), str(self.directory / 'active')],
            env={**self.env, 'DEPLOY_TEST_REAL_RSYNC': shutil.which('rsync')},
            capture_output=True, text=True, check=False,
        )

    def test_deploy_builds_locally_before_upload_and_activates_before_restart(self):
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        build = next(index for index, command in enumerate(commands) if command[0] == 'cargo')
        uploads = [index for index, command in enumerate(commands) if command[0] in ('rsync', 'ssh')]
        self.assertLess(build, min(uploads))
        runtime_copy = self.runtime_upload()
        self.assertIn('-avzR', runtime_copy)
        self.assertEqual([path.split('/./')[1] for path in runtime_copy[3:-1]], [
            'target/release/challenge', 'profiles/safari-26-ios.json',
            'profiles/safari-26-ios/answers.json', 'profiles/safari-26-ios/challenge-page-answers.json',
            'LICENSE',
        ])
        env_copy = next(command for command in commands if command[0] == 'rsync' and '.env' in command)
        self.assertIn('--chmod=600', env_copy)
        remote = [command[-1] for command in commands if command[0] == 'ssh']
        self.assertFalse(any('install-cfsolve.sh' in command or 'cargo' in command or 'rustup' in command
                             for command in remote))
        activate = next(command for command in commands
                        if command[0] == 'ssh' and 'activate-cfsolve.sh' in command[-1])
        self.assertLess(commands.index(runtime_copy), commands.index(activate))
        self.assertLess(commands.index(activate), commands.index(env_copy))
        install = remote.index(activate[-1])
        sync = next(index for index, command in enumerate(remote) if 'uv sync' in command)
        restart = next(index for index, command in enumerate(remote) if 'systemctl --user restart' in command)
        self.assertLess(install, sync)
        self.assertLess(sync, restart)

    def test_failed_local_build_stops_deployment_before_upload(self):
        result = self.deploy(DEPLOY_TEST_FAIL_BUILD='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(command[0] in ('rsync', 'ssh') for command in self.commands()))

    def test_failed_cfsolve_activation_stops_deployment_before_env_and_restart(self):
        result = self.deploy(DEPLOY_TEST_FAIL_ACTIVATE='17')
        self.assertNotEqual(result.returncode, 0)
        remote = [command[-1] for command in self.commands() if command[0] == 'ssh']
        self.assertTrue(any('activate-cfsolve.sh' in command for command in remote))
        self.assertFalse(any('systemctl' in command or 'uv sync' in command for command in remote))
        self.assertFalse(any(command[0] == 'rsync' and '.env' in command for command in self.commands()))

    def test_runtime_upload_and_activation_preserve_layout_and_existing_cache(self):
        staging = self.stage_runtime()
        self.assertEqual(sorted(str(path.relative_to(staging)) for path in staging.rglob('*') if path.is_file()), [
            'LICENSE', 'profiles/safari-26-ios.json', 'profiles/safari-26-ios/answers.json',
            'profiles/safari-26-ios/challenge-page-answers.json', 'target/release/challenge',
        ])
        active = self.directory / 'active'
        (active / 'target/release').mkdir(parents=True)
        cache = active / 'target/release/cache'
        cache.write_text('keep')
        result = self.activate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cache.read_text(), 'keep')
        for path in staging.rglob('*'):
            if path.is_file():
                self.assertEqual((active / path.relative_to(staging)).read_bytes(), path.read_bytes())
        self.assertTrue(os.access(active / 'target/release/challenge', os.X_OK))

    def test_incompatible_binary_does_not_replace_active_runtime(self):
        staging = self.stage_runtime()
        (staging / 'target/release/challenge').write_text('#!/bin/sh\necho "GLIBC not found" >&2\nexit 1\n')
        active = self.directory / 'active/target/release/challenge'
        active.parent.mkdir(parents=True)
        active.write_text('previous binary')
        result = self.activate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('GLIBC not found', result.stderr)
        self.assertIn('Build on a compatible OS/CPU', result.stderr)
        self.assertEqual(active.read_text(), 'previous binary')
        self.assertFalse((self.directory / 'active/profiles').exists())

    def test_incomplete_upload_does_not_install_runtime(self):
        staging = self.stage_runtime()
        (staging / 'profiles/safari-26-ios/challenge-page-answers.json').unlink()
        result = self.activate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing cfsolve runtime file', result.stderr)
        self.assertFalse((self.directory / 'active').exists())

    def test_install_pins_revision_and_reuses_checkout(self):
        for _ in range(2):
            result = self.install()
            self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertEqual(sum(command[:2] == ['git', 'clone'] for command in commands), 1)
        checkouts = [command for command in commands if command[:2] == ['git', 'checkout']]
        self.assertEqual(len(checkouts), 2)
        self.assertEqual(checkouts[0], checkouts[1])
        self.assertRegex(checkouts[0][-1], r'^[0-9a-f]{40}$')
        for command in commands:
            if command[0] == 'cargo':
                self.assertIn('--locked', command)
                self.assertIn('--release', command)
                self.assertEqual(command[command.index('--bin') + 1], 'challenge')
                self.assertEqual(command[command.index('--target-dir') + 1], 'target')

    def test_failed_build_is_reported(self):
        result = self.install(DEPLOY_TEST_FAIL_BUILD='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('is ready', result.stdout)

    def test_missing_clang_stops_before_rust_install_or_build(self):
        result = self.install(CLANG_PATH=str(self.directory / 'missing-clang'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('install clang and libclang-dev', result.stderr)
        self.assertFalse(self.log.exists())

    def test_missing_c_headers_stop_before_rust_install_or_build(self):
        result = self.install(DEPLOY_TEST_MISSING_HEADERS='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("'stddef.h' file not found", result.stderr)
        self.assertIn('Clang cannot read the standard C headers', result.stderr)
        self.assertFalse(any(command[0] in ('git', 'rustup', 'cargo') for command in self.commands()))

    def test_bindgen_uses_the_validated_clang(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['bindgen-clang', str(self.bin / 'clang')], self.commands())

    def test_custom_clang_path_is_absolute_and_handles_spaces(self):
        clang = self.directory / 'custom LLVM' / 'clang-18'
        clang.parent.mkdir()
        clang.symlink_to(self.bin / 'clang')
        result = self.install(CLANG_PATH=os.path.relpath(clang))
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = next(command[1] for command in self.commands() if command[0] == 'bindgen-clang')
        self.assertTrue(Path(selected).is_absolute())
        self.assertEqual(Path(selected).absolute().resolve(), clang.resolve())

    def test_local_source_changes_are_preserved(self):
        self.assertEqual(self.install().returncode, 0)
        result = self.install(DEPLOY_TEST_DIRTY=' M Cargo.toml')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('refusing to overwrite', result.stderr)
        self.assertEqual(sum(command[0] == 'cargo' for command in self.commands()), 1)

    def test_missing_profile_answers_stop_installation(self):
        self.assertEqual(self.install().returncode, 0)
        answer = self.directory / 'cfsolve/profiles/safari-26-ios/challenge-page-answers.json'
        answer.unlink()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('is ready', result.stdout)

    def test_rsync_preserves_remote_cfsolve_cache(self):
        rsync = shutil.which('rsync')
        if rsync is None:
            self.skipTest('rsync is not installed')
        source = self.directory / 'source'
        remote = self.directory / 'remote'
        for directory, marker in ((source, 'local-only'), (remote, 'server-build')):
            for name in ('.cfsolve', '.cfsolve-upload'):
                (directory / name).mkdir(parents=True)
                (directory / name / marker).write_text(marker)
        (source / 'application').write_text('updated')
        (remote / 'stale').write_text('remove')
        subprocess.run([
            rsync, '-a', '--delete-after', f'--exclude-from={self.root / ".gitignore"}',
            f'{source}/', f'{remote}/',
        ], check=True, capture_output=True)
        self.assertEqual((remote / 'application').read_text(), 'updated')
        for name in ('.cfsolve', '.cfsolve-upload'):
            self.assertTrue((remote / name / 'server-build').exists())
            self.assertFalse((remote / name / 'local-only').exists())
        self.assertFalse((remote / 'stale').exists())
