"""Render one `PRBundle` as a self-contained HTML page.

Modelled on `../overtone/overtone/agent/blueprint.py`, which solved the same problem for
proof search: one Python module, one file per run, no React, no CDN, no server. Colour
lives in a single `PALETTE` dict and every per-state CSS rule is generated from it, so a
state cannot be given two different colours in two places. The stage scrubber is a class
toggle over already-rendered DOM rather than a re-render.

The matrix is HTML, not SVG. Overtone needed graphviz because its structure was a DAG;
ours is a grid of (site x component), which a table lays out for free, keeps selectable,
and lets the browser make searchable with ctrl-F.

Gold arrives as a separate argument and is embedded as its own JSON blob. When it is
`None` the page contains no gold bytes at all — the `input/` vs `gold/` split is a physical
leak barrier and a viewer must not be the thing that quietly breaks it.
"""

from __future__ import annotations

import html
import json
from typing import Dict, List, Optional, Sequence

from .review_overlay import STATE_LABEL, STATES

#: state -> (light fill, light stroke, light ink, dark fill, dark stroke, dark ink)
#:
#: The ladder has to be readable at 21px without reading the legend, so the fills carry a
#: deliberate progression — blank, then grey, then hue — rather than eight tints of the same
#: lightness. The first version used pastels an eighth apart and the three commonest states
#: were indistinguishable in the matrix, which defeated the entire picture.
PALETTE = {
    # Nothing was scheduled here: as close to empty as still leaves a grid.
    "unscheduled":  ("#fafbfc", "#ebedf1", "#9aa1ac", "#14171b", "#21262d", "#4d545e"),
    # Present but dead: solid, uncoloured, obviously inert.
    "unsupported":  ("#d7dae1", "#c1c7d1", "#4d5461", "#2a2f37", "#3b4250", "#98a1af"),
    "unavailable":  ("#e7cdb9", "#d0a480", "#7d4a29", "#3d2a1e", "#6d4830", "#e0a878"),
    # Checked and found nothing: the reviewer's most common real outcome, so it gets a hue.
    "silent":       ("#b8cbe6", "#8aa8ce", "#2f5384", "#22314a", "#3a5478", "#9dbde8"),
    # Scope spillover from a multi-site claim: kin to `finding`, deliberately washed out.
    "touched":      ("#cfe6da", "#a6cbb9", "#2f6b52", "#1a3329", "#325f4a", "#93cbaf"),
    "contradicted": ("#efb7af", "#db8b80", "#9c2f26", "#46231f", "#7d3a31", "#f5a79c"),
    "opportunity":  ("#f0cd86", "#daaf52", "#7d4f06", "#413212", "#7a5c1d", "#f0c96b"),
    "candidate":    ("#aeb8f0", "#8090e4", "#2438b4", "#282e52", "#454f96", "#b0bdfa"),
    "finding":      ("#79c7a5", "#43a37c", "#0a5c3d", "#154736", "#2c7d5d", "#7fdfb4"),
}

ARM_LABEL = {
    "checker": "deterministic checker",
    "generalist": "generalist",
    "focused": "focused specs",
    "file_scoped": "file-scoped",
}

_CSS = """
*{box-sizing:border-box}
:root{
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:13px/1.5 var(--sans);
     -webkit-font-smoothing:antialiased}
.shell{display:flex;flex-direction:column;height:100vh}
header{display:flex;gap:18px;align-items:flex-start;justify-content:space-between;
       padding:14px 18px 10px;border-bottom:1px solid var(--line);background:var(--panel)}
.eyebrow{font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--faint)}
h1{margin:3px 0 2px;font-size:16px;font-weight:600;letter-spacing:-.01em}
.sub{margin:0;color:var(--soft);font-size:12px;max-width:78ch}
.toggles{display:flex;gap:7px;flex:none;flex-wrap:wrap;justify-content:flex-end}
.tg{border:1px solid var(--line);background:var(--sunk);color:var(--soft);cursor:pointer;
    border-radius:999px;padding:5px 11px;font:inherit;font-size:11.5px;white-space:nowrap}
.tg:hover{border-color:var(--faint)}
.tg.on{background:var(--accent);border-color:var(--accent);color:#fff}
.tg#goldbtn.on{background:var(--gold);border-color:var(--gold)}
.tg a{color:inherit;text-decoration:none}

.ribbon{display:flex;align-items:stretch;gap:0;padding:8px 18px;overflow-x:auto;
        border-bottom:1px solid var(--line);background:var(--panel)}
.stage{position:relative;flex:none;border:0;background:none;color:var(--soft);cursor:pointer;
       font:inherit;text-align:left;padding:4px 20px 4px 11px;border-left:2px solid var(--line)}
.stage:first-child{border-left:0;padding-left:0}
.stage b{display:block;font-size:17px;font-weight:600;color:var(--ink);
         font-variant-numeric:tabular-nums;line-height:1.15}
.stage em{display:block;font-style:normal;font-size:10.5px;letter-spacing:.07em;
          text-transform:uppercase;color:var(--faint)}
.stage i{display:block;font-style:normal;font-size:10.5px;color:var(--faint);
         max-width:22ch;white-space:normal;line-height:1.3;margin-top:2px}
.stage.on{color:var(--ink)}
.stage.on em{color:var(--accent)}
.stage.on b{text-decoration:underline;text-decoration-color:var(--accent);
            text-underline-offset:3px}

.keys{display:flex;flex-wrap:wrap;gap:4px;padding:7px 18px;border-bottom:1px solid var(--line);
      background:var(--panel)}
.key{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);
     background:var(--sunk);border-radius:999px;padding:3px 9px 3px 5px;cursor:pointer;
     font:inherit;font-size:11px;color:var(--soft)}
.key i{width:11px;height:11px;border-radius:3px;border:1px solid var(--line);display:block}
.key b{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600}
.key.off{opacity:.35}

.body{display:flex;flex:1;min-height:0}
.canvas{flex:1;min-width:0;overflow:auto;padding:0 0 40vh}
aside{width:456px;flex:none;border-left:1px solid var(--line);background:var(--panel);
      overflow:auto;padding:14px 16px 60px}
@media(max-width:1080px){
  .body{flex-direction:column}
  aside{width:auto;max-height:56vh;border-left:0;border-top:1px solid var(--line)}
}

/* --- matrix --- */
table.matrix{border-collapse:separate;border-spacing:0;font-size:12px}
.matrix thead th{position:sticky;top:0;z-index:3;background:var(--panel);
                 border-bottom:1px solid var(--line);padding:0}
.matrix th.rowhead{left:0;z-index:4;text-align:left;min-width:340px;max-width:340px;
                   padding:6px 10px;font-weight:600;font-size:10.5px;letter-spacing:.1em;
                   text-transform:uppercase;color:var(--faint);
                   border-right:1px solid var(--line)}
.matrix th.armhead{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;
                   color:var(--faint);font-weight:500;padding:5px 4px 3px;text-align:center;
                   border-left:1px solid var(--line);white-space:nowrap}
.matrix th.colhead{height:114px;vertical-align:bottom;padding:0 0 5px}
.matrix th.colhead span{writing-mode:vertical-rl;transform:rotate(180deg);
                        display:inline-block;font-weight:500;font-size:11px;color:var(--soft);
                        white-space:nowrap}
.matrix th.colhead.grp{border-left:1px solid var(--line)}
.matrix td.cell{width:30px;min-width:30px;padding:0;text-align:center;
                border-bottom:1px solid var(--bg);cursor:pointer}
.matrix td.cell.grp{border-left:1px solid var(--line)}
.matrix td.cell i{display:block;width:21px;height:21px;margin:2px auto;border-radius:4px;
                  border:1px solid transparent}
.matrix td.cell.below i,.matrix td.cell.muted i{opacity:.12}
.matrix td.cell.sel i{outline:2px solid var(--accent);outline-offset:1px}

tr.site td.label{position:sticky;left:0;z-index:2;background:var(--panel);
                 border-right:1px solid var(--line);border-bottom:1px solid var(--bg);
                 padding:2px 10px;max-width:340px;min-width:340px}
tr.site.sel td.label{background:var(--sunk)}
tr.site.dim{opacity:.32}
.label .name{font-family:var(--mono);font-size:11.5px;white-space:nowrap;overflow:hidden;
             text-overflow:ellipsis;display:block}
.label .meta{display:flex;gap:5px;align-items:center;font-size:10px;color:var(--faint);
             font-variant-numeric:tabular-nums}
.lc{border-radius:3px;padding:0 4px;font-size:9.5px;letter-spacing:.04em;
    text-transform:uppercase}
.lc-added{background:var(--addbg);color:var(--add)}
.lc-removed{background:var(--delbg);color:var(--del)}
.lc-modified{background:var(--sunk);color:var(--soft)}
.lc-unknown,.lc-renamed,.lc-moved,.lc-unchanged_context{background:var(--sunk);color:var(--faint)}
.stat .p{color:var(--add)} .stat .m{color:var(--del)}

tr.filerow td{position:sticky;left:0;background:var(--sunk);border-top:1px solid var(--line);
              border-bottom:1px solid var(--line);padding:4px 10px;cursor:pointer;z-index:2}
tr.filerow .fp{font-family:var(--mono);font-size:11px;color:var(--soft)}
tr.filerow .fc{color:var(--faint);font-size:10.5px;margin-left:8px}
tr.filerow.closed .fp::before{content:"\\25B8  "}
tr.filerow .fp::before{content:"\\25BE  ";color:var(--faint)}

td.goldcell{width:30px;min-width:30px;text-align:center;border-left:1px solid var(--line)}
td.goldcell i{display:block;width:18px;height:18px;margin:2px auto;border-radius:9px}
td.goldcell.has i{background:var(--gold)}
td.goldcell.hit i{background:var(--gold);box-shadow:0 0 0 2px var(--panel),0 0 0 4px var(--add)}
th.goldhead,td.goldcell{display:none}
body.gold-on th.goldhead,body.gold-on td.goldcell{display:table-cell}
tr.site.goldrow td.label{box-shadow:inset 3px 0 0 var(--gold)}
body:not(.gold-on) tr.site.goldrow td.label{box-shadow:none}

/* explain mode: keep only what a reader needs to see the shape of the result */
body.explain td.cell[data-rank="0"] i,body.explain td.cell[data-rank="1"] i{opacity:.1}
body.explain tr.site[data-rank="0"],body.explain tr.site[data-rank="1"]{display:none}
body.explain .onlydebug{display:none}

/* --- view tabs: diff is the default spine, matrix a sibling view --- */
.viewwrap{display:flex;flex:1;min-width:0;min-height:0}
body:not(.matrixview) #matrixpane{display:none}
body.matrixview #diffpane,body.matrixview #rail{display:none}

/* --- left rail: the PR map --- */
#rail{width:250px;flex:none;overflow:auto;border-right:1px solid var(--line);
      background:var(--panel);padding:8px 0 40vh}
.railhead{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);
          padding:4px 12px 7px}
.rf{display:block;width:100%;text-align:left;border:0;background:none;cursor:pointer;
    font:inherit;padding:6px 12px;border-left:2px solid transparent;color:var(--ink)}
.rf:hover{background:var(--sunk)}
.rf.on{border-left-color:var(--accent);background:var(--sunk)}
.rf .p{display:block;font-family:var(--mono);font-size:10.5px;line-height:1.35;
       word-break:break-all;color:var(--ink);font-weight:600}
.rf .p .dir{color:var(--faint);font-weight:400}
.rf.on .p .dir{color:var(--soft)}
.rf .m{display:block;font-size:10px;color:var(--faint);margin-top:2px;
       font-variant-numeric:tabular-nums}
/* Strip height is proportional to true reviewed line count; the marks are real positions. */
.strip{display:block;position:relative;height:16px;margin-top:4px;border-radius:2px;background:var(--sunk);
       border:1px solid var(--line);overflow:hidden}
.strip .hit{position:absolute;top:0;bottom:0;background:var(--accent);opacity:.55;
            min-width:1.5px}
.strip .tgt{position:absolute;bottom:0;height:4px;background:var(--gold);opacity:.75;
            min-width:1.5px}
.strip.na{background:repeating-linear-gradient(45deg,var(--sunk),var(--sunk) 3px,
          var(--panel) 3px,var(--panel) 6px)}

/* --- diff pane --- */
#diffpane{flex:1;min-width:0;overflow:auto;padding:0 0 40vh;position:relative}
.dfile{border-bottom:1px solid var(--line)}
.dfh{position:sticky;top:0;z-index:3;background:var(--sunk);
     border-bottom:1px solid var(--line);padding:6px 12px;display:flex;gap:10px;
     align-items:baseline;flex-wrap:wrap}
.dfh .p{font-family:var(--mono);font-size:11.5px;font-weight:600;word-break:break-all}
.dfh .m{font-size:10.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.dbody{font-family:var(--mono);font-size:11.5px;line-height:1.5}
.elide{padding:3px 12px 3px 62px;color:var(--faint);font-size:10.5px;background:var(--bg);
       border-top:1px dashed var(--line);border-bottom:1px dashed var(--line)}
.dl{display:flex;align-items:flex-start;white-space:pre;padding-right:12px}
.dl .ln{flex:none;width:50px;text-align:right;padding-right:10px;color:var(--faint);
        font-size:10.5px;font-variant-numeric:tabular-nums;user-select:none}
.dl .tx{flex:1;min-width:0;overflow-x:auto;padding-left:8px;border-left:2px solid transparent}
.dl.ch .tx{background:var(--addbg);border-left-color:var(--add)}
.dl.in .tx{border-left-color:var(--line)}
.dl.sel .tx{background:color-mix(in srgb,var(--accent) 12%,transparent)}

/* target header: label, routing summary, and the same cells as the matrix row */
.th{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:5px 12px 5px 62px;
    background:var(--panel);border-top:1px solid var(--line);cursor:pointer;
    border-left:2px solid transparent}
.th:hover{background:var(--sunk)}
.th.sel{background:var(--sunk);border-left-color:var(--accent)}
.th .nm{font-family:var(--mono);font-size:11.5px;font-weight:600}
.th .sub{font-size:10px;color:var(--faint);font-family:var(--sans)}
.th .strip2{display:flex;gap:2px;margin-left:auto}
.th .strip2 i{display:block;width:13px;height:13px;border-radius:3px;
              border:1px solid transparent}
.th .strip2 i.gap{border-left:1px solid var(--line);margin-left:3px;padding-left:2px}
.th .strip2.below i,.th .strip2 i.muted{opacity:.12}
.wu{display:inline-flex;align-items:center;gap:5px;font-size:10px;color:var(--faint);
    font-family:var(--sans);background:var(--sunk);border:1px solid var(--line);
    border-radius:3px;padding:0 5px}
.th.newunit{border-top:2px solid var(--accent)}
.sched{font-size:10px;font-family:var(--sans);border-radius:3px;padding:0 5px;
       border:1px solid var(--line);color:var(--soft)}
.sched.none{background:var(--delbg);color:var(--del);border-color:transparent}
.sched.all{background:var(--addbg);color:var(--add);border-color:transparent}
.noloc{padding:8px 12px;color:var(--faint);font-size:11px}

/* relation fan */
#fan{position:absolute;inset:0;pointer-events:none;z-index:2;overflow:visible}
#fan path{fill:none;stroke:var(--gold);stroke-width:1.5;opacity:.75}
#fan path.cross{stroke-dasharray:4 3}
.dl.rel .tx,.th.rel{box-shadow:inset 3px 0 0 var(--gold)}

/* routing explainer in the aside */
.rt{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:11.5px}
.rt i{width:9px;height:9px;border-radius:50%;flex:none;background:var(--faint)}
.rt.yes i{background:var(--add)}
.rt.no i{background:transparent;border:1px solid var(--line)}
.rt .why{color:var(--faint);font-size:10.5px;margin-left:auto;text-align:right}
.rt.no .nm{color:var(--soft)}

/* --- aside --- */
aside h2{margin:0 0 2px;font-size:13.5px;font-weight:600;font-family:var(--mono);
         word-break:break-all}
aside .where{font-family:var(--mono);font-size:11px;color:var(--faint);word-break:break-all}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0}
.chip{border:1px solid var(--line);background:var(--sunk);border-radius:4px;padding:1px 6px;
      font-size:10.5px;color:var(--soft);white-space:nowrap}
.chip.added{background:var(--addbg);color:var(--add);border-color:transparent}
.chip.removed{background:var(--delbg);color:var(--del);border-color:transparent}
.chip.modified{background:var(--sunk);color:var(--ink)}
.sect{margin:16px 0 6px;font-size:10px;letter-spacing:.13em;text-transform:uppercase;
      color:var(--faint);border-top:1px solid var(--line);padding-top:9px}
pre.diff{margin:0;padding:8px 0;background:var(--sunk);border:1px solid var(--line);
         border-radius:6px;font-family:var(--mono);font-size:11px;line-height:1.45;
         overflow-x:auto;max-height:44vh}
pre.diff span{display:block;padding:0 9px;white-space:pre}
pre.diff .a{background:var(--addbg);color:var(--add)}
pre.diff .d{background:var(--delbg);color:var(--del)}
pre.diff .h{color:var(--faint)}
.blk{border:1px solid var(--line);border-radius:6px;padding:8px 10px;margin:6px 0;
     background:var(--panel)}
.blk.q{opacity:.62}
.blk h3{margin:0 0 4px;font-size:11.5px;font-weight:600;display:flex;gap:7px;
        align-items:center;flex-wrap:wrap}
.pill{border-radius:999px;padding:1px 8px;font-size:10px;border:1px solid transparent;
      white-space:nowrap;font-weight:500}
.blk p{margin:4px 0;color:var(--soft);font-size:12px}
.blk p.claim{color:var(--ink)}
.kv{font-size:11px;color:var(--faint);font-family:var(--mono);word-break:break-all;
    margin:3px 0}
.gbox{border:1px solid var(--gold);border-radius:6px;padding:9px 11px;margin:6px 0;
      background:color-mix(in srgb,var(--gold) 8%,var(--panel))}
.gbox h3{margin:0 0 4px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
         color:var(--gold)}
.gbox .crit{font-size:11.5px;color:var(--soft);margin-top:5px}
.empty{color:var(--faint);font-size:12px;padding:8px 0}
button.link{border:0;background:none;color:var(--accent);cursor:pointer;font:inherit;
            font-size:11px;padding:0;text-decoration:underline}

#tip{position:fixed;pointer-events:none;z-index:50;max-width:340px;background:var(--panel);
     border:1px solid var(--line);border-radius:6px;padding:7px 9px;font-size:11.5px;
     box-shadow:0 6px 22px rgba(0,0,0,.16);display:none;line-height:1.4}
#tip b{display:block;font-family:var(--mono);font-size:11px}
#tip em{font-style:normal;color:var(--soft)}

/* --- index page --- */
.idx{max-width:1020px;margin:0 auto;padding:34px 22px 80px}
.idx table{width:100%;border-collapse:collapse;font-size:13px;margin-top:14px}
.idx th{text-align:left;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
        color:var(--faint);font-weight:500;padding:0 10px 7px;border-bottom:1px solid var(--line)}
.idx td{padding:8px 10px;border-bottom:1px solid var(--line);
        font-variant-numeric:tabular-nums}
.idx td.n{text-align:right}
.idx a{color:var(--ink);text-decoration:none;font-weight:600}
.idx a:hover{color:var(--accent)}
.idx .t{color:var(--soft);font-weight:400;display:block;font-size:11.5px;
        max-width:60ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.idx .src{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:16px;
          line-height:1.7}
"""


#: Base tokens per theme. Kept as data rather than literal CSS so the same values can be
#: emitted into all three theme states without being retyped — a token defined in only one
#: of them is the classic unreadable-artifact bug.
THEME = {
    "light": {
        "bg": "#fbfbfc", "panel": "#ffffff", "sunk": "#f4f5f7", "ink": "#14171c",
        "soft": "#5b626d", "faint": "#949aa5", "line": "#e3e6ea", "accent": "#2f4fd8",
        "gold": "#8a5cd6", "add": "#0f7a52", "addbg": "#e8f5ee", "del": "#b03a30",
        "delbg": "#fbeceb",
    },
    "dark": {
        "bg": "#101317", "panel": "#161a1f", "sunk": "#1b1f25", "ink": "#e6e9ee",
        "soft": "#a2aab6", "faint": "#6c7480", "line": "#272c34", "accent": "#8fa4ff",
        "gold": "#bfa0f0", "add": "#6cd2a8", "addbg": "#13291f", "del": "#f0968c",
        "delbg": "#2c1a18",
    },
}


def _tokens(theme: str) -> str:
    """Every colour the page uses, as custom properties, for one theme."""

    offset = 0 if theme == "light" else 3
    parts = [f"--{name}:{value};" for name, value in THEME[theme].items()]
    for state, values in PALETTE.items():
        fill, stroke, ink = values[offset], values[offset + 1], values[offset + 2]
        parts.append(f"--s-{state}-fill:{fill};--s-{state}-stroke:{stroke};"
                     f"--s-{state}-ink:{ink};")
    return "".join(parts)


def _state_css() -> str:
    """Theme blocks, then component rules that only ever read tokens.

    The viewer has three theme states, not two: an explicit choice stamps
    `data-theme` on the root, and the default "system" setting stamps nothing, where only
    `prefers-color-scheme` separates light from dark. A palette defined solely inside a
    media query never applies in the unstamped state; one defined solely under
    `[data-theme]` never applies when the viewer has made no choice. So the light palette
    is the bare `:root`, the dark palette is repeated under a guarded media query and again
    under the explicit stamp, and no component rule sets a colour inside either block.
    """

    light, dark = _tokens("light"), _tokens("dark")
    themes = (
        f":root{{{light}}}\n"
        f'@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{dark}}}}}\n'
        f':root[data-theme="dark"]{{{dark}}}\n'
    )
    rules = []
    for state in PALETTE:
        rules.append(
            f".s-{state}>i,i.s-{state},.key.s-{state} i{{"
            f"background:var(--s-{state}-fill);border-color:var(--s-{state}-stroke)}}"
        )
        rules.append(
            f".pill.s-{state}{{background:var(--s-{state}-fill);"
            f"border-color:var(--s-{state}-stroke);color:var(--s-{state}-ink)}}"
        )
    return themes + "\n".join(rules)


_JS = r"""
const RANK={};STATES.forEach((s,i)=>RANK[s]=i);
const SITE={};PR.sites.forEach(s=>SITE[s.change_id]=s);
const TR=PR.transcripts||{};
const GBY=(GOLD&&GOLD.by_change)||{};
const COL={};PR.columns.forEach(c=>COL[c.id]=c);
const esc=s=>String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const $=q=>document.querySelector(q);
let cur={site:null,col:null,stage:0,muted:new Set()};

/* --- stage scrubber: dim every cell below the selected stage's floor.
   No re-render and no per-stage colouring stored -- the cell already knows its state. */
function setStage(i){
  i=Math.max(0,Math.min(PR.stages.length-1,i));cur.stage=i;
  const st=PR.stages[i],floor=st.min_state==null?-1:RANK[st.min_state];
  document.querySelectorAll('td.cell').forEach(td=>{
    td.classList.toggle('below',(+td.dataset.rank)<floor);
  });
  document.querySelectorAll('tr.site').forEach(tr=>{
    tr.classList.toggle('dim',(+tr.dataset.rank)<floor);
  });
  document.querySelectorAll('.stage').forEach((b,j)=>b.classList.toggle('on',j===i));
  dimStrips(floor);
  $('#sub').textContent=st.note+(st.top_reasons&&st.top_reasons.length
    ?' — '+st.top_reasons.slice(0,2).map(r=>r[0]+' ('+r[1]+')').join('; '):'');
}

function applyMute(){
  document.querySelectorAll('td.cell').forEach(td=>{
    td.classList.toggle('muted',cur.muted.has(td.dataset.state));
  });
  const st=PR.stages[cur.stage];
  dimStrips(st&&st.min_state!=null?RANK[st.min_state]:-1);
}

function select(changeId,col){
  cur.site=changeId;cur.col=col;
  document.querySelectorAll('tr.site.sel').forEach(e=>e.classList.remove('sel'));
  document.querySelectorAll('td.cell.sel').forEach(e=>e.classList.remove('sel'));
  document.querySelectorAll('.th.sel,.dl.sel').forEach(e=>e.classList.remove('sel'));
  if(!changeId){$('#panel').innerHTML=intro();drawFan(null);return;}
  const head=document.querySelector('.th[data-id="'+CSS.escape(changeId)+'"]');
  if(head){
    head.classList.add('sel');
    document.querySelectorAll('.dl[data-id="'+CSS.escape(changeId)+'"]')
      .forEach(e=>e.classList.add('sel'));
    const site=SITE[changeId];
    if(site)document.querySelectorAll('.rf').forEach(
      b=>b.classList.toggle('on',b.dataset.file===site.path));
  }
  drawFan(changeId);
  const row=document.querySelector('tr.site[data-id="'+CSS.escape(changeId)+'"]');
  if(row){row.classList.add('sel');}
  if(col){
    const c=document.querySelector('td.cell[data-id="'+CSS.escape(changeId)+'"][data-col="'+CSS.escape(col)+'"]');
    if(c)c.classList.add('sel');
  }
  renderPanel(changeId,col);
  const into=document.body.classList.contains('matrixview')?row:head;
  if(into)into.scrollIntoView({block:'nearest'});
}

function diffHtml(text){
  return '<pre class="diff">'+String(text||'').split('\n').map(l=>{
    const c=l.startsWith('+')?'a':l.startsWith('-')?'d':l.startsWith('@')?'h':'';
    return '<span class="'+c+'">'+esc(l||' ')+'</span>';
  }).join('')+'</pre>';
}

function pill(state){
  return '<span class="pill s-'+state+'">'+esc(LABEL[state]||state)+'</span>';
}

function goldHtml(changeId){
  if(!document.body.classList.contains('gold-on'))return '';
  const obs=GBY[changeId]||[];if(!obs.length)return '';
  return obs.map(o=>{
    const verdict=o.judged
      ? (o.resolution_match?'resolution match':o.issue_match?'issue match':'judged, no match')
      : (o.finding_location_hit?'a finding is anchored here'
        :o.candidate_location_hit?'a candidate is anchored here':'nothing anchored here');
    return '<div class="gbox"><h3>maintainer asked · '+esc(verdict)+'</h3>'
      +'<p class="claim">'+esc(o.claim)+'</p>'
      +(o.resolution_criteria?'<div class="crit">resolved when: '+esc(o.resolution_criteria)+'</div>':'')
      +'<div class="chips"><span class="chip">'+esc(o.action.kind)+'</span>'
      +'<span class="chip">'+esc(o.blocking_force)+'</span>'
      +o.concern_labels.map(l=>'<span class="chip">'+esc(l)+'</span>').join('')
      +'<span class="chip">'+(o.included?'included':'excluded from scoring')+'</span>'
      +'<span class="chip">'+esc(o.change_ids.length)+' target(s)</span></div>'
      +'<div class="kv onlydebug">'+esc(o.obligation_id)+'</div></div>';
  }).join('');
}

function transcriptBlock(b){
  const st=cellState(cur.site,b.component);
  const quiet=RANK[st]<RANK['opportunity'];
  let h='<div class="blk'+(quiet?' q':'')+'"><h3>'+esc(COL[b.component]?COL[b.component].label:b.component)
    +' '+pill(st)+'<span class="chip">'+esc(ARMS[b.arm]||b.arm)+'</span></h3>';
  b.investigations.forEach(iv=>{
    h+='<div class="onlydebug">';
    h+='<p>'+esc(iv.terminal_stage||iv.disposition||'no execution record')
      +(iv.terminal_reason?' — '+esc(iv.terminal_reason):'')+'</p>';
    if(iv.basis)h+='<p>'+esc(iv.basis)+'</p>';
    iv.assessments.forEach(a=>{h+='<div class="kv">'+esc(a.implementation_id)+' → '
      +esc(a.status)+' ('+esc(a.reason_code)+')</div>';});
    iv.operator_runs.forEach(r=>{h+='<div class="kv">'+esc(r.operator)+' → '+esc(r.status)
      +' · '+r.result_count+' result(s)'+(r.failure_reason?' · '+esc(r.failure_reason):'')
      +'</div>';});
    h+='</div>';
    iv.opportunities.forEach(o=>{
      h+='<p class="claim">'+esc(o.observed_pattern)+'</p>';
      if(o.transformation)h+='<p>→ '+esc(o.transformation.kind)+': '
        +esc(o.transformation.description)+'</p>';
    });
  });
  b.candidates.forEach(c=>{
    h+='<p class="claim">'+esc(c.claim)+'</p>';
    if(c.requested_change)h+='<p>→ '+esc(c.requested_change)+'</p>';
    h+='<div class="chips"><span class="chip">'+esc(c.concern_family)+'</span>'
      +'<span class="chip">'+esc(c.severity)+'</span>'
      +(c.issue_kind?'<span class="chip">'+esc(c.issue_kind)+'</span>':'')
      +(c.packet?'<span class="chip">evidence '+esc(c.packet.status)+'</span>':'')
      +(c.primary?'':'<span class="chip">anchored elsewhere</span>')+'</div>';
    if(c.artifacts&&c.artifacts.length)h+='<div class="onlydebug">'+c.artifacts.map(a=>
      '<div class="kv">'+esc(a.collector)+'/'+esc(a.kind)+' ['+esc(a.polarity)+'] '
      +esc(a.source_ref)+'</div>').join('')+'</div>';
  });
  b.findings.forEach(f=>{
    h+='<p class="claim">'+esc(f.claim)+'</p>';
    h+='<p>→ '+esc(f.requested_change)+'</p>';
    h+='<div class="chips"><span class="chip">'+esc(f.admission)+'</span>'
      +'<span class="chip">'+esc(f.evidence_tier)+'</span>'
      +'<span class="chip">'+esc(f.concern_family)+'</span>'
      +(f.site_count>1?'<span class="chip">spans '+f.site_count+' sites</span>':'')
      +(f.primary?'':'<span class="chip">anchored elsewhere</span>')+'</div>';
    h+='<div class="kv onlydebug">'+esc(f.finding_id)+(f.issue_id?' · '+esc(f.issue_id):'')
      +'</div>';
  });
  return h+'</div>';
}

function cellState(changeId,col){
  const s=SITE[changeId];if(!s)return 'unscheduled';
  const c=s.cells[col];return c?c.state:'unscheduled';
}

function renderPanel(changeId,col){
  const s=SITE[changeId];if(!s){$('#panel').innerHTML=intro();return;}
  let h='<div class="where">'+esc(s.path)+(s.line_start?':'+s.line_start:'')+'</div>'
    +'<h2>'+esc(s.declaration_name)+'</h2>'
    +'<div class="chips"><span class="chip lc-'+esc(s.lifecycle)+'">'+esc(s.lifecycle)+'</span>'
    +'<span class="chip">'+esc(s.subject_kind)+'</span>'
    +'<span class="chip">'+esc(s.declaration_kind)+'</span>'
    +'<span class="chip">'+esc(s.visibility)+'</span>'
    +'<span class="chip onlydebug">'+esc(s.parse_status)+'</span>'
    +'<span class="chip">+'+s.added+' −'+s.removed+'</span></div>';
  h+=goldHtml(changeId);
  h+='<div class="sect">diff at this site</div>'+diffHtml(s.unified_diff);
  if(s.component_deltas.length){
    h+='<div class="sect onlydebug">what changed (inventory)</div><div class="chips onlydebug">'
      +s.component_deltas.map(d=>'<span class="chip '+esc(d.status)+'">'+esc(d.component)
      +' · '+esc(d.status)+'</span>').join('')+'</div>';
  }
  h+=routingHtml(s);
  h+=relatedHtml(s);
  const blocks=(TR[changeId]||[]).slice().sort((a,b)=>
    RANK[cellState(changeId,b.component)]-RANK[cellState(changeId,a.component)]);
  h+='<div class="sect">what each component said ('+blocks.length+')</div>';
  const shown=col?blocks.filter(b=>b.component===col).concat(blocks.filter(b=>b.component!==col))
                 :blocks;
  h+=shown.length?shown.map(transcriptBlock).join('')
     :'<div class="empty">No component was scheduled at this site.</div>';
  if(s.work_unit_ids.length)h+='<div class="kv onlydebug" style="margin-top:12px">work unit '
    +s.work_unit_ids.map(esc).join(', ')+'<br>'+esc(s.change_id)+'</div>';
  $('#panel').innerHTML=h;
}

/* An obligation whose targets are not in this PR's change graph has no row to sit on.
   It has to be shown somewhere or it silently leaves the denominator. */
function unanchoredHtml(){
  const rows=(GOLD&&GOLD.unanchored)||[];
  if(!rows.length||!document.body.classList.contains('gold-on'))return '';
  return '<div class="sect">asks with no site in the change graph ('+rows.length+')</div>'
    +rows.map(o=>'<div class="gbox"><h3>unanchored · '+esc(o.action.kind)+'</h3>'
      +'<p class="claim">'+esc(o.claim)+'</p>'
      +'<div class="chips"><span class="chip">'
      +(o.included?'included in scoring':'excluded')+'</span>'
      +'<span class="chip">'+esc(o.change_ids.length)+' named target(s), none resolvable'
      +'</span></div></div>').join('');
}

function intro(){
  let h=unanchoredHtml()
    +'<div class="sect" style="border-top:0;padding-top:0">how to read this</div>'
    +'<p style="color:var(--soft)">Rows are <b>change targets</b> — the review sites this '
    +'PR’s diff decomposes into, in diff order. Columns are the components that can speak '
    +'about a site. A cell’s colour is how far that component got.</p>'
    +'<p style="color:var(--soft)">Click any cell or row for the diff at that site and what '
    +'every component said about it, including the ones that checked and found nothing.</p>'
    +'<div class="sect">states</div>';
  STATES.forEach(s=>{h+='<div style="display:flex;gap:8px;align-items:center;margin:4px 0">'
    +'<i class="s-'+s+'" style="width:16px;height:16px;border-radius:4px;border:1px solid;'
    +'display:block;flex:none"></i><span style="font-size:11.5px;color:var(--soft)">'
    +esc(LABEL[s])+'</span></div>';});
  h+=budgetHtml();
  h+='<div class="sect">this page</div><div class="kv">'+esc(SRC.release||'')+'</div>';
  (SRC.runs||[]).forEach(r=>{h+='<div class="kv">'+esc(r)+'</div>';});
  (SRC.conditions||[]).forEach(r=>{h+='<div class="kv">'+esc(r)+'</div>';});
  if(SRC.executor)h+='<div class="kv">'+esc(SRC.executor)+'</div>';
  if((SRC.unresolved_run_coverage||[]).length)h+='<p style="color:var(--soft)">Silence '
    +'coverage unavailable for: '+esc(SRC.unresolved_run_coverage.join(', '))
    +' — that run’s release could not be resolved, so its columns show claims only.</p>';
  return h;
}

/* --- the diff pane --------------------------------------------------------------- */
const FILES=PR.files||[],UNITS=PR.work_units||[],BUDGET=PR.call_budget||{};
const UNIT_OF={};UNITS.forEach(u=>u.change_ids.forEach(c=>UNIT_OF[c]=u));

function fmt(n){return (n==null?0:n).toLocaleString();}

/* Strips carry the same state ranks as matrix cells, so one dim pass drives both views. */
function dimStrips(rank){
  document.querySelectorAll('.th .strip2 i').forEach(i=>{
    i.classList.toggle('muted',(+i.dataset.rank)<rank||cur.muted.has(i.dataset.state));
  });
  document.querySelectorAll('.th').forEach(h=>{
    h.style.opacity=((+h.dataset.rank)<rank)?'.35':'';
  });
}

function scrollToFile(path){
  const el=document.querySelector('.dfile[data-file="'+CSS.escape(path)+'"]');
  if(el)el.scrollIntoView({block:'start',behavior:'smooth'});
  document.querySelectorAll('.rf').forEach(b=>b.classList.toggle('on',b.dataset.file===path));
}

/* The relation fan. Edges are drawn between target headers that are currently in the DOM;
   an edge whose other end sits in an elided region has no anchor, so it is reported as a
   count rather than silently dropped. */
function drawFan(changeId){
  const svg=document.getElementById('fan');
  if(!svg)return;
  svg.innerHTML='';
  document.querySelectorAll('.dl.rel,.th.rel').forEach(e=>e.classList.remove('rel'));
  const site=SITE[changeId];
  if(!site||!site.related||!site.related.length||document.body.classList.contains('matrixview'))
    return;
  const pane=document.getElementById('diffpane');
  const from=document.querySelector('.th[data-id="'+CSS.escape(changeId)+'"]');
  if(!from)return;
  const base=pane.getBoundingClientRect(),top=pane.scrollTop,left=pane.scrollLeft;
  const a=from.getBoundingClientRect();
  const ax=18,ay=a.top-base.top+top+a.height/2;
  let drawn=0;
  site.related.forEach(rel=>{
    const to=document.querySelector('.th[data-id="'+CSS.escape(rel.change_id)+'"]');
    if(!to)return;
    to.classList.add('rel');
    const b=to.getBoundingClientRect();
    const by=b.top-base.top+top+b.height/2;
    const bow=Math.min(60,14+Math.abs(by-ay)/12);
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d','M '+ax+' '+ay+' C '+(ax-bow)+' '+ay+' '+(ax-bow)+' '+by+' '+ax+' '+by);
    if(rel.cross_unit)path.classList.add('cross');
    path.setAttribute('title',rel.kind);
    svg.appendChild(path);drawn++;
  });
  svg.setAttribute('width','100%');
  svg.setAttribute('height',pane.scrollHeight+'px');
  return drawn;
}

/* --- routing: why did these methods fire here ------------------------------------ */
const PRED_LABEL={subject_kind:'subject kind',lifecycle:'lifecycle',
                  visibility:'visibility',changed_components:'changed components'};

function routingHtml(site){
  if(!site.routing||!site.routing.length)return '';
  const on=site.routing.filter(r=>r.scheduled);
  let h='<div class="sect">why these jobs were scheduled</div>';
  h+='<p style="color:var(--soft)">This is <b>'+esc(site.lifecycle)+' '+esc(site.visibility)
    +' '+esc(site.subject_kind)+'</b>'
    +(site.component_deltas.length
      ? ', changing '+site.component_deltas.map(d=>esc(d.component)).join(', ')
      :'')
    +'. The scheduler matches that against each method’s declared applicability — four '
    +'membership tests, no model — giving <b>'+on.length+' of '+site.routing.length
    +'</b> methods here.</p>';
  if(!on.length)h+='<p style="color:var(--del)">No method covers this target, so nothing '
    +'was ever scheduled to look at it.</p>';
  site.routing.forEach(r=>{
    const why=r.scheduled
      ? 'matched '+(r.matched_components.join(', ')||'—')
      : r.failed.map(f=>PRED_LABEL[f]||f).join(' + ')+' rejected';
    h+='<div class="rt '+(r.scheduled?'yes':'no')+'"><i></i>'
      +'<span class="nm">'+esc(COL[r.method_id]?COL[r.method_id].label:r.method_id)+'</span>'
      +'<span class="why">'+esc(why)+'</span></div>';
  });
  return h;
}

function relatedHtml(site){
  const rel=site.related||[];
  if(!rel.length)return '';
  const cross=rel.filter(r=>r.cross_unit).length;
  const byKind={};rel.forEach(r=>{byKind[r.kind]=(byKind[r.kind]||0)+1;});
  let h='<div class="sect">related changes in this PR ('+rel.length+')</div>';
  h+='<p style="color:var(--soft)">'+cross+' of '+rel.length+' sit in a different call, so '
    +'a per-call reviewer never sees them alongside this one.</p>';
  h+='<div class="chips">'+Object.keys(byKind).sort().map(k=>
    '<span class="chip">'+esc(k.replace(/_/g,' '))+' '+byKind[k]+'</span>').join('')+'</div>';
  h+=rel.slice(0,12).map(r=>{
    const other=SITE[r.change_id];
    return '<div class="rt '+(r.cross_unit?'no':'yes')+'"><i></i><span class="nm">'
      +esc(other?other.declaration_name:r.change_id.slice(0,18))+'</span>'
      +'<span class="why">'+esc(r.cross_unit?'other call':'same call')+'</span></div>';
  }).join('');
  if(rel.length>12)h+='<div class="kv">and '+(rel.length-12)+' more</div>';
  return h;
}

function budgetHtml(){
  if(!BUDGET.measured)return '';
  return '<div class="sect">what the scheduling cost</div>'
    +'<p style="color:var(--soft)">'+BUDGET.calls+' calls, '+fmt(BUDGET.total_chars)
    +' characters in total; the largest single call is '+fmt(BUDGET.largest_call_chars)
    +'.</p>'
    +'<p style="color:var(--soft)">The same material in one call would be about '
    +fmt(BUDGET.single_call_chars)+' characters — so decomposition costs about <b>'
    +BUDGET.overhead_ratio+'×</b> more, because each call repeats its file’s diff '
    +'and code. What it buys is per-target attribution, not cost and not context room: '
    +'this PR fits in one call either way.</p>';
}

/* --- wiring --- */
const tip=$('#tip');
document.querySelectorAll('td.cell').forEach(td=>{
  td.addEventListener('mouseenter',e=>{
    const c=COL[td.dataset.col];
    tip.innerHTML='<b>'+esc(c?c.label:td.dataset.col)+'</b><em>'
      +esc(LABEL[td.dataset.state])+'</em>'
      +(td.dataset.reason?'<div style="margin-top:4px">'+esc(td.dataset.reason)+'</div>':'');
    tip.style.display='block';
  });
  td.addEventListener('mousemove',e=>{
    const r=tip.getBoundingClientRect();
    tip.style.left=Math.min(e.clientX+14,innerWidth-r.width-10)+'px';
    tip.style.top=Math.min(e.clientY+14,innerHeight-r.height-10)+'px';
  });
  td.addEventListener('mouseleave',()=>{tip.style.display='none';});
  td.addEventListener('click',()=>select(td.dataset.id,td.dataset.col));
});
document.querySelectorAll('tr.site td.label').forEach(td=>{
  td.addEventListener('click',()=>select(td.parentNode.dataset.id,null));
});
document.querySelectorAll('tr.filerow').forEach(tr=>{
  tr.addEventListener('click',()=>{
    tr.classList.toggle('closed');
    const open=!tr.classList.contains('closed');
    document.querySelectorAll('tr.site[data-file="'+CSS.escape(tr.dataset.file)+'"]')
      .forEach(r=>{r.style.display=open?'':'none';});
  });
});
document.querySelectorAll('.stage').forEach((b,i)=>b.addEventListener('click',()=>setStage(i)));
$('#prevstage')&&$('#prevstage').addEventListener('click',()=>setStage(cur.stage-1));
document.querySelectorAll('.key').forEach(b=>{
  b.addEventListener('click',()=>{
    const s=b.dataset.state;
    if(cur.muted.has(s))cur.muted.delete(s);else cur.muted.add(s);
    b.classList.toggle('off');applyMute();
  });
});
const gb=$('#goldbtn');
if(gb)gb.addEventListener('click',()=>{
  document.body.classList.toggle('gold-on');
  gb.classList.toggle('on');
  if(cur.site)renderPanel(cur.site,cur.col);else $('#panel').innerHTML=intro();
});
document.querySelectorAll('.rf').forEach(b=>{
  b.addEventListener('click',()=>scrollToFile(b.dataset.file));
});
document.querySelectorAll('.th').forEach(h=>{
  h.addEventListener('click',e=>{
    const swatch=e.target.closest('.strip2 i');
    select(h.dataset.id,swatch?swatch.dataset.col:null);
  });
});
const vb=$('#viewbtn');
vb.addEventListener('click',()=>{
  document.body.classList.toggle('matrixview');
  vb.classList.toggle('on');
  vb.textContent=document.body.classList.contains('matrixview')?'diff view':'matrix view';
  // The fan is positioned from live DOM geometry, so it has to be redrawn (or cleared)
  // whenever the pane it lives in is hidden or shown.
  drawFan(cur.site);
});
const dp=$('#diffpane');
if(dp)dp.addEventListener('scroll',()=>{if(cur.site)drawFan(cur.site);},{passive:true});
addEventListener('resize',()=>{if(cur.site)drawFan(cur.site);});
const eb=$('#explainbtn');
eb.addEventListener('click',()=>{
  document.body.classList.toggle('explain');eb.classList.toggle('on');
});
// Background click deselects, in whichever pane is showing.
['#matrixpane','#diffpane'].forEach(sel=>{
  const el=$(sel);
  if(el)el.addEventListener('click',e=>{if(e.target===el)select(null,null);});
});
addEventListener('keydown',e=>{
  if(e.key==='Escape')select(null,null);
  else if(e.key==='ArrowRight')setStage(cur.stage+1);
  else if(e.key==='ArrowLeft')setStage(cur.stage-1);
});
setStage(0);select(null,null);
"""


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _distinct_obligations(gold: Optional[dict]) -> Dict[int, set]:
    """Distinct obligation IDs per PR.

    `by_change` deliberately repeats an obligation under every change target it names, so
    that clicking any of its sites shows the ask. Summing those rows counts (obligation x
    site) pairs — which is how PR 33149's 3 asks first displayed as 61.
    """

    per_pr: Dict[int, set] = {}
    if not gold:
        return per_pr
    rows = [row for rows in gold.get("by_change", {}).values() for row in rows]
    rows += gold.get("unanchored", [])
    for row in rows:
        per_pr.setdefault(row["pr_number"], set()).add(row["obligation_id"])
    return per_pr


def _blob(name: str, value, ascii_only: bool = False) -> str:
    """Embed JSON safely: a literal `</script>` inside any string would end the tag.

    `ascii_only` escapes non-ASCII as `\\uXXXX`, which is valid JS regardless of how the
    document's encoding was decided. Mathlib source is full of `\u03b5`, `\u03c0` and
    `\u221a`, and a host that wraps this page in its own `<head>` renders our `<meta
    charset>` too late to matter.
    """

    text = json.dumps(value, ensure_ascii=ascii_only, separators=(",", ":"))
    return f"const {name}=" + text.replace("</", "<\\/") + ";"


def _arm_groups(columns: Sequence[dict]) -> List[tuple]:
    """Consecutive runs of one arm. Shared by the matrix header and the inline strips so
    the two views can never disagree about column order or group boundaries."""

    groups: List[tuple] = []
    for column in columns:
        if groups and groups[-1][0] == column["arm"]:
            groups[-1][1].append(column)
        else:
            groups.append((column["arm"], [column]))
    return groups


def _matrix(bundle, gold: Optional[dict]) -> str:
    columns = bundle.columns if isinstance(bundle.columns, list) else []
    by_change = (gold or {}).get("by_change", {}) if gold else {}

    # Two header rows: arm groups, then the components under them.
    groups = _arm_groups(columns)

    head = ['<thead><tr><th class="rowhead" rowspan="2">site</th>']
    for arm, members in groups:
        head.append(
            f'<th class="armhead" colspan="{len(members)}">{_esc(ARM_LABEL.get(arm, arm))}</th>'
        )
    head.append('<th class="armhead goldhead" rowspan="2">gold</th></tr><tr>')
    for arm, members in groups:
        for index, column in enumerate(members):
            grp = " grp" if index == 0 else ""
            head.append(f'<th class="colhead{grp}"><span>{_esc(column["label"])}</span></th>')
    head.append("</tr></thead>")

    body = ["<tbody>"]
    current_file = None
    file_sites = {}
    for site in bundle.sites:
        file_sites[site.path] = file_sites.get(site.path, 0) + 1

    for site in bundle.sites:
        if site.path != current_file:
            current_file = site.path
            body.append(
                f'<tr class="filerow" data-file="{_esc(site.path)}">'
                f'<td colspan="{len(columns) + 2}"><span class="fp">{_esc(site.path)}</span>'
                f'<span class="fc">{file_sites[site.path]} site(s)</span></td></tr>'
            )
        obligations = by_change.get(site.change_id, [])
        gold_class = " goldrow" if obligations else ""
        rank = STATES.index(site.depth) if site.depth in STATES else 0
        body.append(
            f'<tr class="site{gold_class}" data-id="{_esc(site.change_id)}" '
            f'data-file="{_esc(site.path)}" data-rank="{rank}">'
        )
        stat = (
            f'<span class="stat"><span class="p">+{site.added}</span> '
            f'<span class="m">&minus;{site.removed}</span></span>'
        )
        body.append(
            '<td class="label">'
            f'<span class="name">{_esc(site.declaration_name)}</span>'
            f'<span class="meta"><span class="lc lc-{_esc(site.lifecycle)}">'
            f"{_esc(site.lifecycle)}</span>"
            f'<span>{_esc(site.subject_kind)}</span>'
            f"<span>L{site.line_start}</span>{stat}</span></td>"
        )
        for arm, members in groups:
            for index, column in enumerate(members):
                cell = site.cells.get(column["id"])
                state = cell.state if cell else "unscheduled"
                reason = cell.reason if cell else ""
                grp = " grp" if index == 0 else ""
                body.append(
                    f'<td class="cell{grp} s-{state}" data-id="{_esc(site.change_id)}" '
                    f'data-col="{_esc(column["id"])}" data-state="{state}" '
                    f'data-rank="{STATES.index(state)}" data-reason="{_esc(reason)}"><i></i></td>'
                )
        if obligations:
            hit = any(item.get("issue_match") or item.get("finding_location_hit")
                      for item in obligations)
            body.append(f'<td class="goldcell has{" hit" if hit else ""}"><i></i></td>')
        else:
            body.append('<td class="goldcell"><i></i></td>')
        body.append("</tr>")
    body.append("</tbody>")
    return '<table class="matrix">' + "".join(head) + "".join(body) + "</table>"


def _cell_strip(site, columns: Sequence[dict], groups) -> str:
    """The matrix row, inlined next to its diff. Same states, same tokens, same ids.

    Reusing `s-<state>` rather than re-deriving colour is what keeps the two views from
    ever disagreeing about what happened at a site.
    """

    parts = []
    for arm, members in groups:
        for index, column in enumerate(members):
            cell = site.cells.get(column["id"])
            state = cell.state if cell else "unscheduled"
            gap = " gap" if index == 0 and parts else ""
            parts.append(
                f'<i class="s-{state}{gap}" data-col="{_esc(column["id"])}" '
                f'data-state="{state}" data-rank="{STATES.index(state)}" '
                f'title="{_esc(column["label"])}: {_esc(STATE_LABEL[state])}"></i>'
            )
    return f'<span class="strip2">{"".join(parts)}</span>'


def _target_header(site, columns, groups, new_unit: Optional[dict]) -> str:
    scheduled = [row for row in site.routing if row["scheduled"]]
    total = len(site.routing)
    if total:
        klass = "all" if len(scheduled) == total else ("none" if not scheduled else "")
        sched = (
            f'<span class="sched {klass}">{len(scheduled)}/{total} methods</span>'
        )
    else:
        sched = ""
    unit = ""
    if new_unit is not None:
        unit = (
            f'<span class="wu">call · {len(new_unit["change_ids"])} target(s)'
            + (f' · {new_unit["chars"]:,} ch' if new_unit["chars"] else "")
            + "</span>"
        )
    return (
        f'<div class="th{" newunit" if new_unit is not None else ""}" '
        f'data-id="{_esc(site.change_id)}" data-rank="{STATES.index(site.depth)}">'
        f'<span class="nm">{_esc(site.declaration_name)}</span>'
        f'<span class="sub">{_esc(site.lifecycle)} {_esc(site.subject_kind)}'
        f" · L{site.line_start}</span>"
        f"{sched}{unit}"
        f"{_cell_strip(site, columns, groups)}</div>"
    )


def _diff_pane(bundle, columns: Sequence[dict], groups) -> str:
    """The PR, as a PR: real files, real line numbers, real context, elisions counted.

    Targets are emitted as header rows in the flow rather than absolutely-positioned
    brackets. Entity spans tile each file without overlapping (measured: 0 overlaps across
    all 85 medium files), so a target owns a contiguous run of lines and a header placed at
    its first line is unambiguous — and it survives elision, which an overlay would not.
    """

    sites_by_id = {site.change_id: site for site in bundle.sites}
    units_by_change = {}
    for unit in bundle.work_units:
        for change_id in unit["change_ids"]:
            units_by_change[change_id] = unit

    out = []
    for meta in bundle.files:
        file_sites = [sites_by_id[cid] for cid in meta["change_ids"] if cid in sites_by_id]
        starts: Dict[int, list] = {}
        placed = set()
        for site in file_sites:
            if site.line_start:
                starts.setdefault(site.line_start, []).append(site)
                placed.add(site.change_id)

        bits = [
            f'<section class="dfile" data-file="{_esc(meta["path"])}">',
            '<div class="dfh">'
            f'<span class="p">{_esc(meta["path"])}</span>'
            f'<span class="m">{_esc(meta["file_status"])}'
            + (f' · {meta["reviewed_lines"]:,} lines' if meta["reviewed_lines"] else "")
            + f' · +{meta["added"]} &minus;{meta["removed"]}'
            f' · {meta["sites"]} target(s)'
            f' · {len(meta["work_unit_ids"])} call(s)</span></div>',
            '<div class="dbody">',
        ]

        if meta["context"] != "full":
            # No reconstructed source: say so rather than silently showing fragments as if
            # they were the file.
            bits.append(
                f'<div class="noloc">Full source unavailable ({_esc(meta["context"])}) — '
                "showing targets without file context.</div>"
            )
            for site in file_sites:
                bits.append(_target_header(site, columns, groups,
                                           units_by_change.get(site.change_id)))
        else:
            seen_units = set()
            for window in meta["windows"]:
                if window["elided_before"] > 0:
                    bits.append(
                        f'<div class="elide">&vellip; {window["elided_before"]:,} '
                        "unchanged lines</div>"
                    )
                for line in window["lines"]:
                    for site in starts.get(line["n"], []):
                        unit = units_by_change.get(site.change_id)
                        fresh = unit if unit and unit["work_unit_id"] not in seen_units else None
                        if unit:
                            seen_units.add(unit["work_unit_id"])
                        bits.append(_target_header(site, columns, groups, fresh))
                    owner = _owner(line["n"], file_sites)
                    klass = "ch" if line["changed"] else ("in" if owner else "")
                    bits.append(
                        f'<div class="dl {klass}" data-n="{line["n"]}"'
                        + (f' data-id="{_esc(owner)}"' if owner else "")
                        + f'><span class="ln">{line["n"]}</span>'
                        f'<span class="tx">{_esc(line["text"]) or "&nbsp;"}</span></div>'
                    )

        orphans = [site for site in file_sites if site.change_id not in placed]
        if orphans:
            bits.append(
                '<div class="noloc">Targets with no resolvable line span:</div>'
            )
            for site in orphans:
                bits.append(_target_header(site, columns, groups,
                                           units_by_change.get(site.change_id)))
        bits.append("</div></section>")
        out.append("".join(bits))
    return f'<div id="diffpane"><svg id="fan"></svg>{"".join(out)}</div>'


def _owner(line: int, file_sites: Sequence) -> str:
    for site in file_sites:
        if site.line_start and site.line_start <= line <= max(site.line_end, site.line_start):
            return site.change_id
    return ""


def _rail(bundle) -> str:
    """One proportional strip per file: which files, how big, and where the edits landed.

    The strip is scaled by the true reviewed line count. That is the whole reason the
    builder reconstructs sources: hunk extents run a median 0.41 of true file length and
    0.01 on an import-only edit, so a strip drawn from them would put every import bump in
    the middle of a file it actually sits at the top of.
    """

    sites_by_id = {site.change_id: site for site in bundle.sites}
    rows = []
    for meta in bundle.files:
        head, _, name = meta["path"].rpartition("/")
        head = f"{head}/" if head else ""
        total = meta["reviewed_lines"]
        marks = []
        if total:
            for hunk in meta["hunks"]:
                top = 100.0 * (hunk["new_start"] - 1) / total
                height = 100.0 * max(hunk["new_lines"], 1) / total
                marks.append(
                    f'<span class="hit" style="left:{top:.2f}%;width:{height:.2f}%"></span>'
                )
            for change_id in meta["change_ids"]:
                site = sites_by_id.get(change_id)
                if site is None or not site.line_start:
                    continue
                top = 100.0 * (site.line_start - 1) / total
                height = 100.0 * max(site.line_end - site.line_start + 1, 1) / total
                marks.append(
                    f'<span class="tgt" style="left:{top:.2f}%;width:{height:.2f}%"></span>'
                )
        rows.append(
            f'<button class="rf" data-file="{_esc(meta["path"])}" '
            f'title="{_esc(meta["path"])}">'
            # Directory dimmed, basename bold: fifteen Mathlib paths wrapped to two lines
            # each are unreadable, and the basename is what identifies the file.
            f'<span class="p"><span class="dir">{_esc(head)}</span>{_esc(name)}</span>'
            f'<span class="strip{"" if total else " na"}">{"".join(marks)}</span>'
            f'<span class="m">'
            + (f'{total:,} lines · ' if total else "no source · ")
            + f'{meta["sites"]} target(s) · {len(meta["work_unit_ids"])} call(s)</span>'
            "</button>"
        )
    budget = bundle.call_budget or {}
    head = (
        f'<div class="railhead">{len(bundle.files)} file(s) · '
        f'{len(bundle.sites)} targets · {budget.get("calls", 0)} calls</div>'
    )
    return f'<div id="rail">{head}{"".join(rows)}</div>'

def _ribbon(bundle) -> str:
    parts = []
    for stage in bundle.stages:
        parts.append(
            f'<button class="stage"><em>{_esc(stage["label"])}</em>'
            f'<b>{stage["count"]}</b><i>{_esc(stage["note"])}</i></button>'
        )
    return '<div class="ribbon">' + "".join(parts) + "</div>"


def _legend(bundle) -> str:
    counts = {state: 0 for state in STATES}
    for site in bundle.sites:
        for cell in site.cells.values():
            counts[cell.state] = counts.get(cell.state, 0) + 1
    parts = []
    for state in STATES:
        parts.append(
            f'<button class="key s-{state}" data-state="{state}"><i></i>'
            f'{_esc(STATE_LABEL[state])} <b>{counts.get(state, 0)}</b></button>'
        )
    return '<div class="keys">' + "".join(parts) + "</div>"


def _ascii_markup(markup: str) -> str:
    """Numeric-entity-escape non-ASCII so the markup survives any document encoding."""

    return "".join(
        char if ord(char) < 128 else f"&#{ord(char)};" for char in markup
    )


def _ascii_js(script: str) -> str:
    """JS-escape non-ASCII. Characters above the BMP need a surrogate pair."""

    out = []
    for char in script:
        point = ord(char)
        if point < 128:
            out.append(char)
        elif point <= 0xFFFF:
            out.append(f"\\u{point:04x}")
        else:
            point -= 0x10000
            out.append(f"\\u{0xD800 + (point >> 10):04x}")
            out.append(f"\\u{0xDC00 + (point & 0x3FF):04x}")
    return "".join(out)


def to_html(
    bundle,
    gold: Optional[dict],
    sources: Optional[dict] = None,
    *,
    standalone: bool = False,
) -> str:
    """One PR, one file. No external requests, no build step.

    `standalone` targets a host that serves this page alone: it drops the index link, which
    would be dead, and emits pure ASCII so the page does not depend on a charset
    declaration the host may place out of reach.
    """

    sources = sources or {}
    pr_gold = None
    if gold:
        # Ship only this PR's obligations, so a page is never a side channel for another's.
        change_ids = {site.change_id for site in bundle.sites}
        pr_gold = {
            "by_change": {
                change_id: rows
                for change_id, rows in gold.get("by_change", {}).items()
                if change_id in change_ids
            },
            "unanchored": [
                row for row in gold.get("unanchored", [])
                if row.get("pr_number") == bundle.pr_number
            ],
        }

    obligations = len(_distinct_obligations(pr_gold).get(bundle.pr_number, ()))
    columns = bundle.columns if isinstance(bundle.columns, list) else []
    groups = _arm_groups(columns)
    title = f"PR {bundle.pr_number} Review Overlay"
    gold_button = (
        f'<button class="tg" id="goldbtn" title="show maintainer obligations">'
        f"gold ({obligations})</button>"
        if pr_gold is not None
        else ""
    )

    payload = {
        "pr_number": bundle.pr_number,
        "columns": bundle.columns,
        "stages": bundle.stages,
        "transcripts": bundle.transcripts,
        "files": bundle.files,
        "ranges": bundle.ranges,
        "methods": bundle.methods,
        "relations": bundle.relations,
        "work_units": bundle.work_units,
        "call_budget": bundle.call_budget,
        "totals": bundle.totals,
        "sites": [
            {
                "change_id": site.change_id,
                "path": site.path,
                "declaration_name": site.declaration_name,
                "declaration_kind": site.declaration_kind,
                "kind": site.kind,
                "parse_status": site.parse_status,
                "line_start": site.line_start,
                "line_end": site.line_end,
                "changed_range_ids": site.changed_range_ids,
                "routing": site.routing,
                "related": site.related,
                "unified_diff": site.unified_diff,
                "added": site.added,
                "removed": site.removed,
                "lifecycle": site.lifecycle,
                "subject_kind": site.subject_kind,
                "visibility": site.visibility,
                "component_deltas": site.component_deltas,
                "work_unit_ids": site.work_unit_ids,
                # Only cells that say something. `cellState` defaults to `unscheduled`,
                # and on PR 33294 the silent majority was 359 KB of `{"unscheduled",""}`.
                "cells": {
                    key: {"state": cell.state, "reason": cell.reason}
                    for key, cell in site.cells.items()
                    if cell.state != "unscheduled" or cell.reason
                },
                "depth": site.depth,
            }
            for site in bundle.sites
        ],
    }

    subtitle = (
        f"{len(bundle.sites)} review sites across {len(bundle.files)} file(s) · "
        f"{bundle.totals['investigations']} investigations · "
        f"{bundle.totals['candidates']} candidates · "
        f"{bundle.totals['findings']} findings · "
        f"{bundle.totals['published']} published"
    )

    page = (
        # Without an explicit charset the browser falls back to latin-1 and every `·`, `→`
        # and `’` in the page — and every one in Lean source — renders as mojibake.
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(title)}</title>"
        f"<style>{_CSS}\n{_state_css()}</style>"
        '<div class="shell">'
        "<header><div>"
        f'<div class="eyebrow">review overlay · {_esc(bundle.repo)} '
        f"· PR #{bundle.pr_number} · round {bundle.round_index}"
        + (
            ""
            if bundle.title_provenance == "review_time_verified"
            else f" · title {_esc(bundle.title_provenance)}"
        )
        + "</div>"
        f"<h1>{_esc(bundle.title)}</h1>"
        f'<p class="sub" id="sub">{_esc(subtitle)}</p>'
        "</div><div class=\"toggles\">"
        f"{gold_button}"
        '<button class="tg" id="viewbtn" title="switch between the diff and the matrix">'
        "matrix view</button>"
        '<button class="tg" id="explainbtn" title="hide unscheduled and unsupported detail">'
        "explain mode</button>"
        + ("" if standalone else '<button class="tg"><a href="index.html">all PRs</a></button>')
        + "</div></header>"
        f"{_ribbon(bundle)}{_legend(bundle)}"
        '<div class="body"><div class="viewwrap">'
        f"{_rail(bundle)}"
        f"{_diff_pane(bundle, columns, groups)}"
        '<div class="canvas" id="matrixpane">'
        f"{_matrix(bundle, gold)}"
        "</div></div>"
        '<aside id="panel"></aside></div></div>'
        '<div id="tip"></div>'
        "<script>"
        f"{_blob('PR', payload, standalone)}"
        f"{_blob('GOLD', pr_gold, standalone)}"
        f"{_blob('SRC', sources, standalone)}"
        f"{_blob('STATES', list(STATES), standalone)}"
        f"{_blob('LABEL', STATE_LABEL, standalone)}"
        f"{_blob('ARMS', ARM_LABEL, standalone)}"
        f"{_JS}</script>"
    )
    if standalone:
        # The two halves need different escapes. HTML entities are not decoded inside a
        # <script>, and `\uXXXX` is not decoded outside one, so the markup gets numeric
        # entities and the script gets JS escapes. Non-ASCII in `_JS` only ever appears
        # inside string literals and comments, where a `\uXXXX` is equivalent.
        head, _, script = page.partition("<script>")
        page = _ascii_markup(head) + "<script>" + _ascii_js(script)
    return page


def write_index(bundles: Sequence, gold: Optional[dict], sources: Optional[dict] = None) -> str:
    sources = sources or {}
    by_pr = {pr: len(ids) for pr, ids in _distinct_obligations(gold).items()}

    rows = []
    for bundle in bundles:
        rows.append(
            f"<tr><td><a href='pr-{bundle.pr_number}.html'>#{bundle.pr_number}</a>"
            f"<span class='t'>{_esc(bundle.title)}</span></td>"
            f"<td class='n'>{bundle.totals['sites']}</td>"
            f"<td class='n'>{bundle.totals['investigations']}</td>"
            f"<td class='n'>{bundle.totals['candidates']}</td>"
            f"<td class='n'>{bundle.totals['findings']}</td>"
            f"<td class='n'>{bundle.totals['published']}</td>"
            f"<td class='n'>{by_pr.get(bundle.pr_number, '') if gold else ''}</td></tr>"
        )

    src = "".join(
        f"<div>{_esc(key)}: {_esc(value)}</div>"
        for key, value in sources.items()
        if value not in (None, [], "")
    )
    return (
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Review overlays</title>"
        f"<style>{_CSS}\n{_state_css()}</style>"
        '<div class="idx">'
        '<div class="eyebrow">review overlay</div>'
        "<h1>How the reviewer reviewed each PR</h1>"
        f'<p class="sub">{len(bundles)} PR(s). Each page shows the PR\'s change targets '
        "against every component that could speak about them.</p>"
        "<table><thead><tr><th>PR</th><th class='n'>sites</th>"
        "<th class='n'>investigations</th><th class='n'>candidates</th>"
        "<th class='n'>findings</th><th class='n'>published</th>"
        f"<th class='n'>{'obligations' if gold else ''}</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f'<div class="src">{src}</div></div>'
    )
