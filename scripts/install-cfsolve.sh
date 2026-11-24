#!/usr/bin/env bash
set -euo pipefail

# Keep the solver, its patched dependencies, and browser profiles at one revision.
revision=06d58d64f1f2292e77341576d05b00af15d90960
source_dir=${1:-.cfsolve}

for command in git cmake cc c++; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'cfsolve requires %s; install the build prerequisites listed in README.md.\n' "$command" >&2
        exit 1
    fi
done

if [[ $(uname -s) == Linux && ! -s /etc/timezone && ! -L /etc/localtime ]]; then
    printf 'cfsolve requires /etc/timezone or an /etc/localtime symlink to zoneinfo; see README.md.\n' >&2
    exit 1
fi

# rustup installs into the deployment user's account; no shell profile changes.
export PATH="${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
if ! command -v rustup >/dev/null 2>&1; then
    installer=$(mktemp)
    trap 'rm -f "$installer"' EXIT
    curl --proto '=https' --tlsv1.2 -fsS https://sh.rustup.rs -o "$installer"
    sh "$installer" -y --profile minimal --default-toolchain none --no-modify-path
fi

if [[ ! -d "$source_dir/.git" ]]; then
    git clone --depth 1 https://github.com/chris124567/cfsolve.git "$source_dir"
fi

cd "$source_dir"
if [[ -n $(git status --porcelain) ]]; then
    printf 'The cfsolve checkout has local changes; refusing to overwrite them.\n' >&2
    exit 1
fi
if ! git cat-file -e "$revision^{commit}" 2>/dev/null; then
    git fetch --depth 1 origin "$revision"
fi
git checkout --detach "$revision"

# Reads the upstream rust-toolchain.toml; leave the user's default unchanged.
rustup toolchain install --profile minimal --no-self-update
cargo build --locked --release --bin challenge --jobs 2 --target-dir target

for file in profiles/safari-26-ios.json profiles/safari-26-ios/answers.json profiles/safari-26-ios/challenge-page-answers.json; do
    test -s "$file"
done
target/release/challenge --help >/dev/null
printf 'cfsolve %s is ready in %s\n' "$revision" "$PWD"
