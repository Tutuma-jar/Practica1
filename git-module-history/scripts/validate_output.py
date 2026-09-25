#!/usr/bin/env python3
"""Validate the dataset's agent analysis against all historical Markdown output."""
import collections
import json
from pathlib import Path
import re
import sys
import traceback

# Import shared helpers without creating files in the installed skill.
sys.dont_write_bytecode = True
from analyze_repo import Failure, Parser, git, report, repository, safe_output

TYPES = ("Feature", "Fix", "Refactor", "Configuration")
LABELS = ("Features", "Fixes", "Refactors", "Configuración")
SECTIONS = ("Vista general", "Estructura", "Descripción", "Evolución del módulo",
            "Análisis del historial", "Commits relacionados")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def cells(line):
    if not line.strip().startswith("|"):
        return []
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def table(text, header):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if cells(line) == header:
            rows = []
            for following in lines[index + 1:]:
                row = cells(following)
                if not row:
                    break
                if all(re.fullmatch(r":?-+:?", cell) for cell in row):
                    continue
                rows.append(row)
            return rows
    return None


def sections(text):
    return re.findall(r"^## (.+?)\s*$", text, re.M)


def validate(data, output):
    errors = []
    def check(condition, code, message):
        if not condition:
            errors.append((code, message))
        return condition

    commits_list = data.get("commits", [])
    analysis = data.get("analysis", {})
    if not isinstance(commits_list, list) or not isinstance(analysis, dict):
        raise Failure("VALIDATION_ERROR", "Dataset sin commits/analysis válidos.", str(output))
    if not all(isinstance(c, dict) and all(k in c for k in
               ("full_hash", "hash", "date", "timestamp", "merge", "files")) for c in commits_list):
        raise Failure("VALIDATION_ERROR", "Dataset con commits incompletos.", str(output))
    commits = {c["full_hash"]: c for c in commits_list}
    check(len(commits) == len(commits_list), "DUPLICATE_COMMIT", "El dataset contiene commits duplicados.")
    classified = analysis.get("classifications", {})
    excluded = analysis.get("excluded_commits", {})
    modules = analysis.get("documented_modules", {})
    reviews = analysis.get("merge_reviews", {})
    if not all(isinstance(x, dict) for x in (classified, excluded, modules, reviews)):
        raise Failure("VALIDATION_ERROR", "El bloque analysis contiene mapas inválidos.", str(output))
    check(analysis.get("scope") in {"full", "focused"}, "INVALID_SCOPE", "scope debe ser full o focused.")
    check(bool(str(analysis.get("scope_description", "")).strip()), "INVALID_SCOPE", "Falta scope_description.")
    check(set(classified).isdisjoint(excluded), "COVERAGE", "Un commit está clasificado y excluido a la vez.")
    check(set(classified) | set(excluded) == set(commits), "COVERAGE",
          "Cada commit recopilado debe estar clasificado o excluido con motivo, sin hashes ajenos.")
    for full, item in classified.items():
        good = isinstance(item, dict)
        check(good and item.get("type") in TYPES, "INVALID_TYPE", f"Clasificación inválida: {full}.")
        check(good and item.get("confidence") in {"high", "medium", "low"}, "CONFIDENCE", f"Falta confianza: {full}.")
        check(good and isinstance(item.get("evidence"), list) and bool(item["evidence"])
              and all(isinstance(e, str) and e.strip() for e in item["evidence"])
              and bool(item.get("rationale")), "EVIDENCE", f"Falta evidencia o justificación: {full}.")
    for full, reason in excluded.items():
        check(isinstance(reason, str) and bool(reason.strip()), "EXCLUSION_REASON", f"Falta motivo: {full}.")
    for full, commit in commits.items():
        if not commit["merge"]:
            continue
        review = reviews.get(full, {})
        good = isinstance(review, dict) and type(review.get("own_changes")) is bool
        check(good and bool(review.get("evidence")) and bool(review.get("reason")),
              "MERGE_REVIEW", f"Falta revisión explícita del merge {commit['hash']}.")
        if good and full in classified:
            paths = review.get("paths", [])
            check(review["own_changes"] and isinstance(paths, list) and bool(paths)
                  and set(paths) <= set(commit["files"]), "MERGE_DOUBLE_COUNT",
                  f"Merge clasificado sin modificaciones propias verificadas: {commit['hash']}.")
    check(set(reviews) <= {h for h, c in commits.items() if c["merge"]}, "MERGE_REVIEW",
          "Hay revisiones de merges desconocidos o de commits ordinarios.")

    def read_document(path):
        if not path.is_file():
            errors.append(("MISSING_DOCUMENT", f"No existe {path.name}."))
            return ""
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(("UNREADABLE_DOCUMENT", f"{path.name}: {exc}"))
            return ""
        check(not re.search(r"\{\{[^{}]+\}\}", text), "UNRESOLVED_PLACEHOLDER", f"{path.name} contiene placeholders.")
        check(bool(text.strip()), "EMPTY_DOCUMENT", f"{path.name} está vacío.")
        return text

    def expected_stats(hashes):
        rows = [commits[h] for h in hashes if h in commits]
        counts = collections.Counter(classified[h].get("type") for h in hashes
                                     if isinstance(classified.get(h), dict))
        dates = sorted(c["date"] for c in rows)
        return [str(len(hashes)), *(str(counts[t]) for t in TYPES),
                dates[0] if dates else "N/A", dates[-1] if dates else "N/A"]

    def dashboard(text, expected, name, global_dashboard=False):
        rows = table(text, ["Elemento", "Detalle"])
        check(rows is not None, "MISSING_TABLE", f"Falta Vista general en {name}.")
        values = {r[0]: r[1] for r in (rows or []) if len(r) == 2}
        check(len(values) == len(rows or []), "INVALID_TABLE", f"Filas duplicadas o inválidas en {name}.")
        labels = ["Total de commits analizados" if global_dashboard else "Total de commits", *LABELS,
                  "Primer cambio registrado", "Último cambio registrado"]
        for label, value in zip(labels, expected):
            check(values.get(label) == value, "COUNT_MISMATCH",
                  f"{name}: {label}: se esperaba {value}, recibido {values.get(label)!r}.")
        return values

    actual_names, normalized_names, used = set(), set(), set()
    stats = {}
    for slug, module in modules.items():
        if not check(bool(SLUG.fullmatch(slug)) and slug != "general", "INVALID_MODULE", f"Slug inválido: {slug!r}."):
            continue
        actual_names.add(slug + ".md")
        if not check(isinstance(module, dict) and isinstance(module.get("commits"), list)
                     and isinstance(module.get("name"), str), "INVALID_MODULE", f"Módulo incompleto: {slug}."):
            continue
        name = module["name"]
        normalized = re.sub(r"[\W_]+", "", name.casefold())
        check(bool(normalized) and normalized not in normalized_names, "DUPLICATE_MODULE", f"Nombre repetido o vacío: {name}.")
        normalized_names.add(normalized)
        check(module.get("status") in {"active", "historical"}, "MODULE_STATUS", f"Estado inválido: {slug}.")
        hashes = module["commits"]
        if not check(all(isinstance(h, str) for h in hashes), "INVALID_MODULE", f"Hashes inválidos: {slug}."):
            continue
        check(len(hashes) == len(set(hashes)), "DUPLICATE_COMMIT", f"Asignaciones duplicadas en {slug}.")
        check(set(hashes) <= set(classified), "UNCLASSIFIED_COMMIT", f"{slug} referencia commits sin clasificar.")
        used.update(hashes)
        text = read_document(output / (slug + ".md"))
        headings = sections(text)
        check(headings == list(SECTIONS), "MODULE_SECTIONS", f"{slug}.md: secciones ausentes, duplicadas o fuera de orden.")
        # No heading of any level may follow the evidence table's section heading.
        ending = text.split("## Commits relacionados", 1)[-1]
        check("## Commits relacionados" in text and not re.search(r"^#{1,6} ", ending, re.M),
              "COMMITS_NOT_LAST", f"Commits relacionados no es la última sección de {slug}.md.")
        for index, section in enumerate(SECTIONS):
            match = re.search(r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            check(bool(match and match.group(1).strip()), "EMPTY_SECTION", f"{slug}.md: sección vacía {section}.")
        if module.get("status") == "historical":
            check(bool(re.search(r"histórico|histórica|eliminado|retirado", text, re.I)),
                  "MODULE_STATUS", f"{slug}.md debe identificar el módulo como histórico.")
        stats[slug] = expected_stats(set(hashes))
        values = dashboard(text, stats[slug], slug + ".md")
        check(values.get("Módulo / Funcionalidad") == name, "MODULE_NAME", f"Nombre inconsistente: {slug}.")
        rows = table(ending, ["Fecha", "Commit", "Tipo", "Descripción"])
        check(rows is not None, "MISSING_TABLE", f"Falta tabla de commits en {slug}.")
        seen, order = [], []
        for row in rows or []:
            if not check(len(row) == 4, "INVALID_TABLE", f"Fila inválida en {slug}: {row!r}."):
                continue
            date, short, kind, description = row
            candidates = [h for h, c in commits.items() if c["hash"] == short]
            if not check(len(candidates) == 1, "UNKNOWN_COMMIT", f"Hash corto desconocido o ambiguo en {slug}: {short}."):
                continue
            full = candidates[0]
            seen.append(full)
            order.append((commits[full]["timestamp"], full))
            item = classified.get(full, {})
            check(date == commits[full]["date"], "COMMIT_DATE", f"Fecha incorrecta de {short} en {slug}.")
            check(isinstance(item, dict) and kind == item.get("type"), "COMMIT_TYPE", f"Tipo incorrecto de {short} en {slug}.")
            check(bool(description), "EMPTY_DESCRIPTION", f"Falta descripción de {short} en {slug}.")
        check(len(seen) == len(set(seen)), "DUPLICATE_COMMIT", f"Hashes duplicados en {slug}.md.")
        check(set(seen) == set(hashes), "EVIDENCE_COVERAGE", f"La tabla de {slug} no coincide con sus commits asignados.")
        check(order == sorted(order), "COMMIT_ORDER", f"Commits fuera de orden cronológico en {slug}.md.")
    check(used == set(classified), "COVERAGE", "Los commits clasificados deben aparecer al menos en un módulo.")
    found = {p.name for p in output.glob("*.md")}
    check(found == actual_names | {"general.md"}, "DOCUMENT_SET",
          f"Documentos sobrantes o ausentes: {sorted(found ^ (actual_names | {'general.md'}))}.")
    check(not any(p.parent != output for p in output.rglob("*.md") if ".analysis" not in p.parts),
          "DOCUMENT_SET", "Los documentos visibles deben estar directamente en docs/commit-history/.")
    general = read_document(output / "general.md")
    base_headings = ["Vista general", "Resumen por módulo", "Distribución de cambios por tipo",
                     "Estructura funcional del proyecto", "Actividad por módulo"]
    check(sections(general) in (base_headings, base_headings + ["Áreas con mayor concentración de cambios"]),
          "GENERAL_SECTIONS", "general.md contiene secciones incorrectas o un historial detallado.")
    check(not re.search(r"\|\s*Fecha\s*\|\s*Commit\s*\|", general)
          and not any(re.search(r"(?<![a-zA-Z0-9])" + re.escape(c["hash"]) + r"(?![a-zA-Z0-9])", general)
                      or c["full_hash"] in general for c in commits_list),
          "DETAILED_GLOBAL_HISTORY", "general.md no debe listar hashes ni tablas individuales de commits.")
    totals = expected_stats(set(classified))
    values = dashboard(general, totals, "general.md", True)
    check(values.get("Módulos detectados") == str(len(modules)), "COUNT_MISMATCH", "Número global de módulos incorrecto.")
    summary = table(general, ["Módulo", "Total", *LABELS, "Primer cambio", "Último cambio"])
    check(summary is not None, "MISSING_TABLE", "Falta Resumen por módulo.")
    listed = []
    for row in summary or []:
        link = re.fullmatch(r"\[([^\]]+)\]\(([a-z0-9-]+)\.md\)", row[0]) if row else None
        if not check(len(row) == 8 and bool(link), "INVALID_TABLE", f"Fila de resumen inválida: {row!r}."):
            continue
        name, slug = link.groups()
        listed.append(slug)
        check(slug in stats and row[1:] == stats[slug], "COUNT_MISMATCH", f"Resumen global inconsistente: {slug}.")
        check(slug in modules and name == modules[slug].get("name"), "MODULE_NAME", f"Enlace o nombre inconsistente: {slug}.")
    check(len(listed) == len(set(listed)) and set(listed) == set(modules), "DUPLICATE_MODULE",
          "Resumen global con módulos duplicados, desconocidos o ausentes.")
    distribution = table(general, ["Tipo", "Commits únicos"])
    expected_distribution = [[kind, value] for kind, value in zip(TYPES, totals[1:5])]
    check(distribution == expected_distribution, "COUNT_MISMATCH", "Distribución global por tipo incorrecta.")
    activity = table(general, ["Módulo", "Commits", "Días activos", "Primer cambio", "Último cambio"])
    expected_activity = []
    for slug in sorted(stats):
        module = modules[slug]
        dates = {commits[h]["date"] for h in module["commits"] if h in commits}
        expected_activity.append([f"[{module['name']}]({slug}.md)", stats[slug][0], str(len(dates)), *stats[slug][-2:]])
    check(activity == expected_activity, "COUNT_MISMATCH", "Actividad por módulo incorrecta o fuera de orden por slug.")
    return errors, len(modules)


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    root, branch, head = repository(args.repo)
    output = safe_output(root)
    dataset = output / ".analysis/history-data.json"
    try:
        data = json.loads(dataset.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Failure("VALIDATION_ERROR", f"No se puede leer el dataset: {exc}", str(dataset)) from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise Failure("VALIDATION_ERROR", "Dataset de versión desconocida.", str(dataset))
    errors, count = validate(data, output)
    if (data.get("branch"), data.get("head")) != (branch, head):
        errors.append(("STALE_DATASET", "La rama o HEAD ha cambiado; regenera dataset y documentación."))
    actual_hashes = set(git(root, "log", "--format=%H", head, "--").splitlines())
    if actual_hashes != {c["full_hash"] for c in data["commits"]}:
        errors.append(("HISTORY_COVERAGE", "El dataset no representa todo el historial local alcanzable desde HEAD."))
    if errors:
        print(f"VALIDATION FAILED\n\nSe encontraron {len(errors)} problemas:\n")
        for index, (code, message) in enumerate(errors, 1):
            print(f"{index}. [{code}]\n   {message}\n")
        raise Failure("VALIDATION_ERROR", "La documentación generada contiene inconsistencias.",
                      str(output), "Corrige todos los problemas indicados y vuelve a validar.")
    print(f"VALIDATION PASSED\n\nDocumentación histórica válida.\n\nMódulos documentados: {count}\n"
          "Dashboard general: OK\nCommits relacionados: OK\nEstadísticas: OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report(exc if isinstance(exc, Failure) else Failure("VALIDATION_ERROR", str(exc), " ".join(sys.argv[1:])))
        if "--debug" in sys.argv:
            traceback.print_exc()
        sys.exit(1)
