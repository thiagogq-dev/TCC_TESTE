import argparse
import json
from pathlib import Path


def load_edges(json_path: Path):
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    adjacency = {}
    for item in data:
        source = item.get("commit")
        targets = item.get("fixed_by", [])

        if not source:
            continue

        adjacency.setdefault(source, [])
        for target in targets:
            if not target:
                continue
            adjacency[source].append(target)
            adjacency.setdefault(target, [])

    return adjacency


def find_cycles(adjacency):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in adjacency}
    stack = []
    cycles = []
    seen_cycles = set()

    def register_cycle(cycle_nodes):
        if not cycle_nodes:
            return
        core = cycle_nodes[:-1]
        if not core:
            return

        rotations = []
        size = len(core)
        for index in range(size):
            rotations.append(tuple(core[index:] + core[:index]))

        canonical = min(rotations)
        if canonical in seen_cycles:
            return

        seen_cycles.add(canonical)
        cycles.append(list(canonical) + [canonical[0]])

    def dfs(node):
        color[node] = GRAY
        stack.append(node)

        for neighbor in adjacency[node]:
            state = color[neighbor]
            if state == WHITE:
                dfs(neighbor)
            elif state == GRAY:
                start = stack.index(neighbor)
                cycle_path = stack[start:] + [neighbor]
                register_cycle(cycle_path)

        stack.pop()
        color[node] = BLACK

    for node in adjacency:
        if color[node] == WHITE:
            dfs(node)

    return cycles


def check_file(json_path: Path, max_cycles: int):
    adjacency = load_edges(json_path)
    cycles = find_cycles(adjacency)

    edge_count = sum(len(targets) for targets in adjacency.values())
    print(f"\nArquivo: {json_path}")
    print(f"Nós: {len(adjacency)} | Arestas: {edge_count}")

    if not cycles:
        print("Sem ciclos ✅")
        return False

    print(f"Com ciclos ❌ (total detectado: {len(cycles)})")
    for index, cycle in enumerate(cycles[:max_cycles], start=1):
        print(f"  {index}. {' -> '.join(cycle)}")

    if len(cycles) > max_cycles:
        print(f"  ... ({len(cycles) - max_cycles} ciclos adicionais omitidos)")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Verifica ciclos em JSONs de relations (commit -> fixed_by)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Arquivo .json específico ou diretório contendo JSONs (padrão: diretório atual).",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=5,
        help="Quantidade máxima de ciclos exibidos por arquivo (padrão: 5).",
    )

    args = parser.parse_args()
    target = Path(args.path)

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("*.json"))
    else:
        raise SystemExit(f"Caminho inválido: {target}")

    if not files:
        raise SystemExit("Nenhum arquivo .json encontrado.")

    found_any_cycle = False
    for json_file in files:
        found_any_cycle = check_file(json_file, args.max_cycles) or found_any_cycle

    raise SystemExit(1 if found_any_cycle else 0)


if __name__ == "__main__":
    main()
