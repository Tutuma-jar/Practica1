#!/usr/bin/env python3
"""Collect read-only Git facts. Python 3.10+, standard library only."""
import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback

SKILL = Path(__file__).resolve().parent.parent
OUTPUT = Path("docs/commit-history")


class Failure(Exception):
    def __init__(self, code, message, value="", action="Revisa la entrada y vuelve a ejecutar."):
        super().__init__(message)
        self.code, self.value, self.action = code, value, action


def report(error):
    print(f"[ERROR] {error.code}\n\n{error}\n\nEntrada recibida:\n"
          f"{error.value}\n\nAcción:\n{error.action}", file=sys.stderr)


def warning(code, message):
    print(f"[WARNING] {code}\n\n{message}\n", file=sys.stderr)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Failure("INVALID_INPUT", message, " ".join(sys.argv[1:]), self.format_usage())


def git(root, *args):
    # Deliberately closed read-only command list; no shell or configurable commands.
    if not args or args[0] not in {"status", "branch", "rev-parse", "log", "show", "diff"}:
        raise Failure("GIT_ERROR", "Operación Git no permitida.", repr(args))
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    try:
        result = subprocess.run(
            ["git", "--no-pager", "-c", "core.quotepath=false", "-C", str(root), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False)
    except OSError as exc:
        raise Failure("GIT_ERROR", str(exc), str(root), "Verifica que Git esté instalado.") from exc
    if result.returncode:
        raise Failure("GIT_ERROR", result.stderr.decode("utf-8", "replace").strip(),
                      "git " + " ".join(args), "Verifica el repositorio y su historial disponible.")
    return result.stdout.decode("utf-8", "surrogateescape")


def repository(value):
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise Failure("INVALID_INPUT", "La ruta no es un directorio.", value)
    try:
        root = Path(git(path, "rev-parse", "--show-toplevel").strip()).resolve()
    except Failure as exc:
        if "not a git repository" in str(exc) or "work tree" in str(exc):
            raise Failure("INVALID_INPUT", "La ruta no corresponde a un repositorio Git de trabajo.",
                          value, "Ejecuta la skill dentro del repositorio que deseas analizar.") from exc
        raise
    branch = git(root, "branch", "--show-current").strip()
    head = git(root, "rev-parse", "--verify", "HEAD").strip()
    return root, branch or "DETACHED_HEAD", head


def safe_output(root):
    """Refuse links/junctions along output paths, including existing descendants."""
    output = root / OUTPUT
    for path in (root / "docs", output, output / ".analysis"):
        if path.is_symlink() or path.resolve() != path.absolute():
            raise Failure("OUTPUT_ERROR", "La salida contiene enlaces o redirecciones.", str(path))
    if output.exists():
        for base, dirs, files in os.walk(output, followlinks=False):
            for name in dirs + files:
                path = Path(base) / name
                if path.is_symlink() or path.resolve() != path.absolute():
                    raise Failure("OUTPUT_ERROR", "La salida contiene un enlace.", str(path))
    return output


def load_patterns():
    path = SKILL / "assets/ignore-patterns.txt"
    return [line.strip().strip("/") for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def ignored(path, patterns):
    parts = path.split("/")
    return any(any(fnmatch.fnmatchcase(part, pattern) for part in parts)
               if "/" not in pattern else
               any(fnmatch.fnmatchcase("/".join(parts[:i]), pattern)
                   for i in range(1, len(parts) + 1)) for pattern in patterns)


def inventory(root, patterns):
    files, directories, links = [], [], []
    def fail(exc):
        raise exc
    for base, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        kept = []
        for name in sorted(dirs):
            path = Path(base) / name
            rel = path.relative_to(root).as_posix()
            if ignored(rel, patterns):
                continue
            if path.is_symlink() or path.resolve() != path.absolute():
                links.append(rel)
                continue
            directories.append(rel)
            # Submodules / embedded repositories are boundaries, not this history.
            if (path / ".git").exists():
                links.append(rel)
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = Path(base) / name
            rel = path.relative_to(root).as_posix()
            if not ignored(rel, patterns):
                (links if path.is_symlink() else files).append(rel)
    return {"directories": sorted(directories), "files": sorted(files),
            "links_or_nested_repositories": sorted(links), "source": "working-tree"}


def changes(raw):
    """Parse Git's NUL-delimited name-status, including two-path renames."""
    tokens = raw.split("\0")
    result, index = [], 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index].lstrip("\n")
        index += 1
        if not re.fullmatch(r"[ACDMRTUXB][0-9]*", status):
            raise Failure("ANALYSIS_ERROR", "Estado Git inesperado.", repr(status))
        count = 2 if status[0] in "RC" else 1
        paths = tokens[index:index + count]
        if len(paths) != count or not all(paths):
            raise Failure("ANALYSIS_ERROR", "Salida name-status incompleta.", repr(tokens))
        index += count
        item = {"status": status, "path": paths[-1]}
        if count == 2:
            item["old_path"] = paths[0]
        result.append(item)
    return result


def possible_module(path):
    parts = path.split("/")
    folders = parts[:-1]
    wrappers = {"src", "lib", "app", "apps", "packages", "services", "modules", "features"}
    chosen = []
    for folder in folders:
        if folder not in wrappers:
            chosen.append(folder)
        if len(chosen) == 2:
            break
    match = re.match(r"(.+)\.(controller|service|module|repository|resolver)\.[^.]+$", parts[-1])
    if match and (not chosen or chosen[-1] in {"controllers", "repositories", "resolvers"}):
        chosen = chosen[:1] + [match.group(1)] if chosen else [match.group(1)]
    label = "/".join(chosen) or (folders[-1] if folders else "project-root")
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "module"
    # A short digest keeps distinct physical candidates distinct after normalization.
    return slug + "-" + hashlib.sha256(label.encode("utf-8", "surrogateescape")).hexdigest()[:8], label


def collect(root, branch, head, patterns):
    tree = inventory(root, patterns)  # Inspect the entire tree BEFORE reading history.
    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=normal")
    hashes = git(root, "log", "--reverse", "--topo-order", "--format=%H", head, "--").splitlines()
    commits = []
    for full_hash in hashes:
        meta = git(root, "show", "-s", "--format=%H%x00%h%x00%cI%x00%P%x00%B", full_hash, "--")
        full, short, iso, parent_text, message = meta.split("\0", 4)
        parents = parent_text.split()
        instant = datetime.fromisoformat(iso).astimezone(timezone.utc)
        per_parent = {}
        if len(parents) > 1:
            for parent in parents:
                per_parent[parent] = changes(git(root, "diff", "--no-ext-diff", "--no-textconv",
                                                "--name-status", "-z", "--find-renames", parent, full, "--"))
            entries = []
            for parent_entries in per_parent.values():
                for entry in parent_entries:
                    if entry not in entries:
                        entries.append(entry)
            common = set.intersection(*({c["path"] for c in cs} for cs in per_parent.values()))
        else:
            entries = changes(git(root, "show", "--format=", "--no-ext-diff", "--no-textconv",
                                  "--name-status", "-z", "--find-renames", full, "--"))
            common = set()
        all_paths = sorted({c[key] for c in entries for key in ("path", "old_path") if key in c})
        # Preserve all facts (including ignored paths) but exclude irrelevant paths from mapping.
        relevant = [p for p in all_paths if not ignored(p, patterns)]
        commits.append({"hash": short, "full_hash": full, "date": instant.date().isoformat(),
                        "timestamp": int(instant.timestamp()), "committer_date": iso,
                        "message": message.rstrip("\n"), "parents": parents, "merge": len(parents) > 1,
                        "files": all_paths, "relevant_files": relevant, "changes": entries,
                        "parent_changes": per_parent, "merge_candidate_paths": sorted(common)})
    commits.sort(key=lambda c: (c["timestamp"], c["full_hash"]))
    modules = {}
    current = set(tree["files"])
    for path in sorted(current | {p for c in commits for p in c["relevant_files"]}):
        key, label = possible_module(path)
        module = modules.setdefault(key, {"label": label, "files": [], "current_files": [], "commits": []})
        module["files"].append(path)
        if path in current:
            module["current_files"].append(path)
    for commit in commits:
        keys = sorted({possible_module(p)[0] for p in commit["relevant_files"]})
        commit["possible_modules"] = keys
        for key in keys:
            modules[key]["commits"].append(commit["full_hash"])
    for module in modules.values():
        module["historical_candidate"] = not bool(module["current_files"])
    cross = sum(len(c["possible_modules"]) > 1 for c in commits)
    if cross:
        warning("CROSS_MODULE_CHANGE", f"{cross} commits afectan varios candidatos; revisar impactos por módulo.")
    warning("AMBIGUOUS_MODULE", "El mapa físico es preliminar; confirma límites y nombres funcionales con el código.")
    warning("LOW_CONFIDENCE", "Los commits no están clasificados. El agente debe revisar diffs y evidencias de merges.")
    return {"schema_version": 1, "repository": root.name, "branch": branch, "head": head,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "shallow": git(root, "rev-parse", "--is-shallow-repository").strip() == "true",
            "working_tree_dirty": bool(status), "working_tree_status": status,
            "ignore_patterns": patterns, "structure": tree, "modules": modules, "commits": commits,
            "analysis": {"scope": "full", "scope_description": "", "classifications": {},
                         "excluded_commits": {}, "merge_reviews": {}, "documented_modules": {}}}


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Directorio dentro del repositorio")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    root, branch, head = repository(args.repo)
    output = safe_output(root)
    patterns = load_patterns()
    data = collect(root, branch, head, patterns)
    if repository(root)[1:] != (branch, head):
        raise Failure("ANALYSIS_ERROR", "La rama o HEAD cambió durante la recopilación.", str(root))
    try:
        target = output / ".analysis/history-data.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise Failure("OUTPUT_ERROR", str(exc), str(output), "Comprueba permisos y espacio de salida.") from exc
    print(f"Dataset: {target}\nRama: {branch}\nCommits: {len(data['commits'])}\n"
          f"Candidatos: {len(data['modules'])}")
    if data["shallow"]:
        warning("LOW_CONFIDENCE", "Repositorio shallow: solo se documentará el historial local disponible.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report(exc if isinstance(exc, Failure) else Failure("ANALYSIS_ERROR", str(exc), " ".join(sys.argv[1:])))
        if "--debug" in sys.argv:
            traceback.print_exc()
        sys.exit(1)
