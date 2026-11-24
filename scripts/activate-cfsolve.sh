#!/usr/bin/env bash
set -euo pipefail

staging_dir=${1:-.cfsolve-upload}
install_dir=${2:-.cfsolve}
files=(
    target/release/challenge
    profiles/safari-26-ios.json
    profiles/safari-26-ios/answers.json
    profiles/safari-26-ios/challenge-page-answers.json
    LICENSE
)
sources=()
for file in "${files[@]}"; do
    if [[ ! -s "$staging_dir/$file" ]]; then
        printf 'Missing cfsolve runtime file: %s\n' "$staging_dir/$file" >&2
        exit 1
    fi
    sources+=("$staging_dir/./$file")
done

# Check architecture and shared libraries before replacing the running version.
if ! "$staging_dir/target/release/challenge" --help >/dev/null; then
    printf 'The cfsolve binary cannot run on this server. Build on a compatible OS/CPU with glibc and libstdc++ versions no newer than the server.\n' >&2
    exit 1
fi
if [[ $(uname -s) == Linux && ! -s /etc/timezone && ! -L /etc/localtime ]]; then
    printf 'cfsolve requires /etc/timezone or an /etc/localtime symlink to zoneinfo; see README.md.\n' >&2
    exit 1
fi

mkdir -p "$install_dir"
# rsync replaces each file by rename; keep any existing source/build cache.
rsync -aR -- "${sources[@]}" "$install_dir/"
printf 'cfsolve runtime is ready in %s\n' "$install_dir"
