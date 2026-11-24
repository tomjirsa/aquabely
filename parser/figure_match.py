from parser.catalogue import CATALOGUE, CatalogueEntry


class UnmatchedFigureError(ValueError):
    def __init__(self, figure_name: str):
        super().__init__(f"Figure not in the catalogue: {figure_name!r}")
        self.figure_name = figure_name


# (level, lowercased normalised sheet name) -> catalogue code, or "no-code:<name>"
# for the L3 entries that have no code. Matching is level-scoped.
ALIASES: dict[tuple[str, str], str] = {
    ("L3", "ballet leg single"): "101",
    ("L3", "straight ballet leg"): "101",
    ("L3", "back layout to surface arch to back layout position"):
        "no-code:From Back Layout Position to Surface Arch Position to Back Layout Position",
    ("L3", "from back layout position to surface arch position to back layout position"):
        "no-code:From Back Layout Position to Surface Arch Position to Back Layout Position",
    ("L3", "kipnus"): "316",
    ("L3", "walkover front variant"): "no-code:Walkover Front Variant",
}


def match_figure(level: str, sheet_name: str, code: str | None) -> CatalogueEntry:
    if code is not None:
        for e in CATALOGUE:
            if e.level == level and e.code == code:
                return e
    target = ALIASES.get((level, sheet_name.strip().lower()))
    if target is not None:
        for e in CATALOGUE:
            if e.level != level:
                continue
            if target.startswith("no-code:"):
                if e.code is None and e.name == target[len("no-code:"):]:
                    return e
            elif e.code == target:
                return e
    raise UnmatchedFigureError(sheet_name)
