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
    # Declined: visible enough to read as a decision, quiet enough not to compete with work.
    "pruned":       ("#eceef3", "#dadfe8", "#79808d", "#1d2027", "#2e333d", "#6d7583"),
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

/* The same obligation, marked in the diff. The matrix's gold column is invisible in the
   default view, which made the toggle look broken: a target the maintainer wrote about
   has to be visible where the reading actually happens. A tint rather than `.rel`'s left
   border, so a related target and an asked-about one stay tellable apart. */
.gmark{display:none;font-size:10px;font-family:var(--sans);border-radius:3px;padding:0 5px;
       border:1px solid color-mix(in srgb,var(--gold) 45%,transparent);color:var(--gold);
       background:color-mix(in srgb,var(--gold) 12%,var(--panel))}
.gmark.g-res{background:var(--addbg);color:var(--add);border-color:var(--add);font-weight:700}
.gmark.g-iss{background:var(--addbg);color:var(--add);border-color:transparent}
.gmark.g-no{background:var(--delbg);color:var(--del);border-color:transparent}
body.gold-on .gmark{display:inline-block}
body.gold-on .th.goldtarget{background:color-mix(in srgb,var(--gold) 7%,var(--panel))}
body.gold-on .th.goldtarget:hover{background:color-mix(in srgb,var(--gold) 13%,var(--sunk))}

/* Every ask on this PR in one row, so a match is found by reading rather than by hunting
   for a filled dot in a hidden column. Chips are keyed by obligation, not by target: an
   obligation naming 13 targets is one ask, and listing it 13 times would bury the others. */
.goldbar{display:none;gap:6px;flex-wrap:wrap;align-items:center;padding:7px 14px;
         border-bottom:1px solid var(--line);
         background:color-mix(in srgb,var(--gold) 5%,var(--panel))}
body.gold-on .goldbar{display:flex}
.gb-lab{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--gold);
        font-family:var(--sans);font-weight:600;margin-right:2px}
.gchip{display:inline-flex;align-items:center;gap:6px;font-size:10.5px;
       font-family:var(--sans);border:1px solid var(--line);border-radius:4px;
       padding:2px 7px;cursor:pointer;background:var(--panel);color:var(--soft)}
.gchip:hover{background:var(--sunk)}
.gchip.off{cursor:default;opacity:.65}
.gchip .gn{font-family:var(--mono);color:var(--ink)}
.gchip .gv{font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--faint)}
.gchip.g-res{border-color:var(--add);background:var(--addbg)}
.gchip.g-res .gv{color:var(--add);font-weight:700}
.gchip.g-iss{border-color:color-mix(in srgb,var(--add) 55%,transparent)}
.gchip.g-iss .gv{color:var(--add)}
.gchip.g-no .gv{color:var(--del)}
.gchip.g-anc .gv{color:var(--gold)}

/* Debug is opt-in: the clean page is what a reader gets, not what they must ask for.
   IDs, hashes and pipeline internals stay hidden until the toggle is on. */
.onlydebug{display:none}
body.debug .onlydebug{display:revert}

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

/* --- lead + timeline panes --- */
body:not(.leadview) #leadpane{display:none}
body.leadview #diffpane,body.leadview #rail,body.leadview #matrixpane{display:none}
body.leadview.matrixview #leadpane{display:none}
#leadpane{flex:1;min-width:0;overflow:auto;padding:16px 20px 40vh}
.lsec{margin:0 0 22px}
.lsec>h2{margin:0 0 3px;font-size:13px;font-weight:600}
.lsec>p.n{margin:0 0 10px;color:var(--soft);font-size:12px;max-width:74ch}
.cards{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.card{border:1px solid var(--line);border-radius:7px;padding:8px 12px;background:var(--panel);
      min-width:116px}
.card b{display:block;font-size:17px;font-weight:600;font-variant-numeric:tabular-nums;
        line-height:1.2}
.card em{display:block;font-style:normal;font-size:10px;letter-spacing:.09em;
         text-transform:uppercase;color:var(--faint);margin-top:1px}
.card i{display:block;font-style:normal;font-size:10.5px;color:var(--faint);margin-top:3px}
.card.warn{border-color:var(--del)}
.card.warn b{color:var(--del)}

/* gantt */
.gantt{border:1px solid var(--line);border-radius:7px;overflow:hidden;background:var(--panel)}
.grow{display:flex;align-items:center;gap:8px;padding:1px 10px;font-size:11px}
.grow.head{background:var(--sunk);border-bottom:1px solid var(--line);padding:5px 10px;
           font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}
.grow .gl{flex:none;width:190px;font-family:var(--mono);font-size:10.5px;
          white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.grow .gt{position:relative;flex:1;height:15px;min-width:120px}
.grow .gt span{position:absolute;top:2px;height:11px;border-radius:3px;min-width:2px;
               background:var(--accent);opacity:.85;cursor:pointer}
.grow .gt span.mandatory{background:var(--soft);opacity:.55}
.grow .gt span.failed{background:var(--del)}
.grow .gm{flex:none;width:150px;text-align:right;color:var(--faint);font-size:10.5px;
          font-variant-numeric:tabular-nums}
.grow.lead .gt span{background:var(--gold);height:15px;top:0;border-radius:2px}
.wband{background:var(--sunk);border-top:1px solid var(--line);
       border-bottom:1px solid var(--line);padding:3px 10px;font-size:10.5px;color:var(--soft)}
.wband b{color:var(--ink);font-weight:600}

/* ladder */
.ladder{border-left:2px solid var(--line);margin:6px 0 0 8px;padding-left:14px}
.lturn{position:relative;padding:7px 0}
.lturn::before{content:"";position:absolute;left:-21px;top:12px;width:9px;height:9px;
               border-radius:50%;background:var(--panel);border:2px solid var(--line)}
.lturn.act::before{border-color:var(--gold);background:var(--gold)}
.lturn .tno{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}
.lturn .say{margin:2px 0;font-size:12px;color:var(--ink);max-width:76ch}
.jobs{margin:5px 0 0;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.job{display:flex;align-items:center;gap:8px;padding:4px 9px;font-size:11.5px;
     border-top:1px solid var(--line);cursor:pointer}
.job:first-child{border-top:0}
.job:hover{background:var(--sunk)}
.job .ja{flex:none;width:118px;font-weight:600}
.job .jw{flex:1;min-width:0;color:var(--faint);font-family:var(--mono);font-size:10.5px;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.job .jm{flex:none;color:var(--soft);font-size:10.5px;font-variant-numeric:tabular-nums}
.job.declined{opacity:.5}
.brief{border-left:2px solid var(--gold);padding:5px 0 5px 10px;margin:5px 0;
       background:color-mix(in srgb,var(--gold) 6%,transparent)}
.brief h4{margin:0 0 3px;font-size:10px;letter-spacing:.1em;text-transform:uppercase;
          color:var(--gold);font-weight:600}
.brief p{margin:2px 0;font-size:11.5px;color:var(--soft)}
.brief p.claim{color:var(--ink)}
a.convlink{color:var(--accent);font-size:11px}

/* the declined table */
table.decl{width:100%;border-collapse:collapse;font-size:11.5px}
.decl th{text-align:left;font-size:10px;letter-spacing:.1em;text-transform:uppercase;
         color:var(--faint);font-weight:500;padding:0 8px 5px;border-bottom:1px solid var(--line)}
.decl td{padding:4px 8px;border-bottom:1px solid var(--line);
         font-variant-numeric:tabular-nums}
.decl td.n{text-align:right}
.decl tr.mand td{color:var(--soft)}
.bar{display:inline-block;height:8px;border-radius:2px;background:var(--accent);
     vertical-align:middle;opacity:.7}
.bar.d{background:var(--faint);opacity:.45}

/* conversation page */
.cpage{max-width:1000px;margin:0 auto;padding:22px 20px 70px}
.cturn{border:1px solid var(--line);border-radius:7px;margin:9px 0;overflow:hidden;
       background:var(--panel)}
.cturn>.ch{display:flex;gap:9px;align-items:baseline;padding:5px 11px;background:var(--sunk);
           border-bottom:1px solid var(--line);font-size:10.5px;color:var(--faint)}
.cturn>.ch b{color:var(--ink);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.cturn .body{padding:9px 11px}
.cturn p{margin:0 0 8px;font-size:12.5px;line-height:1.55;white-space:pre-wrap}
.cturn p:last-child{margin-bottom:0}
.tcall{border:1px solid var(--line);border-radius:5px;margin:7px 0;background:var(--bg)}
.tcall .th2{display:flex;gap:8px;align-items:baseline;padding:4px 9px;font-size:11px;
            border-bottom:1px solid var(--line)}
.tcall .th2 b{font-family:var(--mono);font-weight:600}
.tcall pre{margin:0;padding:7px 9px;font-family:var(--mono);font-size:10.5px;
           white-space:pre-wrap;word-break:break-word;max-height:280px;overflow:auto;
           color:var(--soft)}
.tcall.res{background:var(--sunk)}
.trunc{padding:3px 9px;font-size:10px;color:var(--faint);border-top:1px dashed var(--line)}

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
  /* v5 delegations: what the lead asked this arm to do here, and what it cost. */
  (b.delegations||[]).forEach(d=>{
    if(d.disposition==='pruned'){
      h+='<p>Declined'+(d.reason?': '+esc(d.reason):'.')+'</p>';
      return;
    }
    h+='<div class="chips"><span class="chip">'+esc(d.disposition)+'</span>'
      +(d.tier?'<span class="chip">'+esc(d.tier)+'</span>':'')
      +(d.cost!=null?'<span class="chip">$'+d.cost.toFixed(4)+'</span>':'')
      +(d.execution_time!=null?'<span class="chip">'+Math.round(d.execution_time)+'s</span>':'')
      +(d.turns?'<span class="chip">'+d.turns+' turns</span>':'')+'</div>';
    if(d.brief)h+=briefHtml(d.brief);
    (d.claims||[]).forEach(c=>{
      h+='<p class="claim">'+esc(c.claim)+'</p>';
      if(c.requested_change)h+='<p>&rarr; '+esc(c.requested_change)+'</p>';
    });
    if(!(d.claims||[]).length)h+='<p>Ran over this site and said nothing about it.</p>';
    /* The arm answers per work unit, so it may have spoken about a sibling target in the
       same call. Say so rather than dropping the fact silently. */
    if(d.claims_elsewhere)h+='<p>'+d.claims_elsewhere+' further claim(s) in this call were '
      +'about other targets in the same work unit.</p>';
    if(d.has_transcript)h+='<p>'+convLink(d.invocation_id,'read the conversation')
      +'</p>';
  });
  /* v4 investigations: only the outcome and its basis. The capability assessments,
     per-operator run rows and terminal reason codes were executor vocabulary -- unreadable
     without having read the executor, and never actionable. */
  b.investigations.forEach(iv=>{
    if(iv.basis)h+='<p>'+esc(iv.basis)+'</p>';
    iv.opportunities.forEach(o=>{
      h+='<p class="claim">'+esc(o.observed_pattern)+'</p>';
      if(o.transformation)h+='<p>&rarr; '+esc(o.transformation.kind)+': '
        +esc(o.transformation.description)+'</p>';
    });
    h+='<div class="kv onlydebug">'+esc(iv.investigation_id||'')+'</div>';
  });
  b.candidates.forEach(c=>{
    h+='<p class="claim">'+esc(c.claim)+'</p>';
    if(c.requested_change)h+='<p>&rarr; '+esc(c.requested_change)+'</p>';
    h+='<div class="chips"><span class="chip">'+esc(c.concern_family)+'</span>'
      +'<span class="chip">'+esc(c.severity)+'</span>'
      +(c.issue_kind?'<span class="chip">'+esc(c.issue_kind)+'</span>':'')
      /* The packet verdict stays; the collector/kind/polarity/source_ref lines and raw
         artifact excerpts do not -- they describe how evidence was gathered, not what it says. */
      +(c.packet?'<span class="chip">evidence '+esc(c.packet.status)+'</span>':'')
      +(c.primary?'':'<span class="chip">anchored elsewhere</span>')+'</div>';
  });
  b.findings.forEach(f=>{
    h+='<p class="claim">'+esc(f.claim)+'</p>';
    h+='<p>&rarr; '+esc(f.requested_change)+'</p>';
    h+='<div class="chips"><span class="chip">'+esc(f.admission)+'</span>'
      +'<span class="chip">'+esc(f.evidence_tier)+'</span>'
      +'<span class="chip">'+esc(f.concern_family)+'</span>'
      +(f.site_count>1?'<span class="chip">spans '+f.site_count+' sites</span>':'')
      +(f.primary?'':'<span class="chip">anchored elsewhere</span>')+'</div>';
    h+='<div class="kv onlydebug">'+esc(f.finding_id)+(f.issue_id?' \u00b7 '+esc(f.issue_id):'')
      +'</div>';
  });
  return h+'</div>';
}

function briefHtml(b){
  if(!b)return '';
  let h='<div class="brief"><h4>the lead asked</h4><p class="claim">'+esc(b.question)+'</p>';
  if(b.because)h+='<p><b>because</b> '+esc(b.because)+'</p>';
  if(b.look_at&&b.look_at.length)h+='<p><b>look at</b> '+esc(b.look_at.join('; '))+'</p>';
  if(b.already_checked)h+='<p><b>already checked</b> '+esc(b.already_checked)+'</p>';
  if(b.abstain_if)h+='<p><b>abstain if</b> '+esc(b.abstain_if)+'</p>';
  return h+'</div>';
}

function convLink(conversationId,label){
  const slug=String(conversationId).replace(/[^A-Za-z0-9]+/g,'-');
  return '<a class="convlink" href="conv/'+slug+'.html">'+esc(label)+'</a>';
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
    +'<p style="color:var(--soft)">The page opens on the <b>diff</b>. Each bracketed block '
    +'is a <b>change target</b> — one changed declaration — and the swatches beside it '
    +'are what each reviewer did there. Click one for the detail.</p>'
    +(PR.lead
      ? '<p style="color:var(--soft)">The <b>lead</b> tab retraces the routing: what the '
        +'agenda offered, which specialists ran and which the lead declined, in what order, '
        +'and what each conversation cost. Every conversation is readable in full.</p>'
      : '<p style="color:var(--soft)">The <b>matrix</b> tab puts every site against every '
        +'component at once, which is the better view on a large PR.</p>')
    +'<div class="sect">states</div>';
  // Only the states this page can actually produce. On a v5 page five of the v4 executor's
  // states are structurally impossible and listing them at zero is noise.
  const present=new Set();
  PR.sites.forEach(s=>Object.values(s.cells||{}).forEach(c=>present.add(c.state)));
  STATES.filter(s=>present.has(s)).forEach(s=>{
    h+='<div style="display:flex;gap:8px;align-items:center;margin:4px 0">'
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
  if(PR.lead)return leadCostHtml();
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

function leadCostHtml(){
  const c=PR.lead.cost||{},run=RUNCOST||{};
  const usd=v=>'$'+(v==null?0:v).toFixed(4);
  let h='<div class="sect">what this review cost</div>'
    +'<p style="color:var(--soft)">'+usd(c.total)
    +' for this PR: the lead\u2019s own turns '+usd(c.lead)+', the mandatory floor '
    +usd(c.mandatory)+', the specialists it chose '+usd(c.proposed)+'.</p>';
  if(run.actual_total!=null){
    h+='<p style="color:var(--soft)">Across the run: <b>$'+run.actual_total.toFixed(2)
      +'</b>, of which the floor is $'+(run.mandatory||0).toFixed(2)+' \u2014 '
      +Math.round(100*(run.mandatory||0)/run.actual_total)+'% of the bill for work the lead '
      +'did not choose.</p>';
    if(run.manifest_understates_by>0.005){
      h+='<p style="color:var(--del)">The run manifest reports $'
        +run.manifest_total.toFixed(2)+'. It omits the mandatory floor, so it understates '
        +'the run by $'+run.manifest_understates_by.toFixed(2)+'.</p>';
    }
  }
  return h;
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
document.querySelectorAll('[data-goto]').forEach(b=>{
  b.addEventListener('click',()=>select(b.dataset.goto,null));
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
const lb=$('#leadbtn');
if(lb)lb.addEventListener('click',()=>{
  document.body.classList.toggle('leadview');
  lb.classList.toggle('on');
  // The fan is positioned from live geometry; hiding its pane must clear it.
  drawFan(cur.site);
});
// A Gantt bar or a ladder row selects the site its job was scheduled on, so the timeline
// and the diff stay two views of one thing.
document.querySelectorAll('[data-inv]').forEach(el=>{
  el.addEventListener('click',()=>{
    const job=(PR.lead&&PR.lead.delegations||[]).find(j=>j.invocation_id===el.dataset.inv);
    if(job&&job.site_change_ids&&job.site_change_ids.length){
      document.body.classList.remove('leadview');
      if(lb)lb.classList.remove('on');
      select(job.site_change_ids[0],job.arm_id);
    }
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
const eb=$('#debugbtn');
eb.addEventListener('click',()=>{
  document.body.classList.toggle('debug');eb.classList.toggle('on');
  if(cur.site)renderPanel(cur.site,cur.col);
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


def _obligations_where(gold: Optional[dict], key: str) -> Dict[int, set]:
    """Distinct obligation IDs per PR whose verdict has `key` set.

    De-duplicated exactly as `_distinct_obligations` is, and for the same reason: a verdict
    belongs to the obligation, not to each target the obligation happens to name.
    """

    per_pr: Dict[int, set] = {}
    if not gold:
        return per_pr
    rows = [row for rows in gold.get("by_change", {}).values() for row in rows]
    rows += gold.get("unanchored", [])
    for row in rows:
        if row.get(key):
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


#: `goldHtml`'s ladder, as data. Ordered worst to best so `max` picks the best outcome at
#: a target carrying several asks. `resolution_match` is the top rung and reads differently
#: from `issue_match` on purpose: the run proposed an edit that satisfies the ask, not
#: merely a claim that names it. `judged` outranks a location hit because it is an answer
#: rather than a hint, which is the precedence `goldHtml` already uses.
def _gold_rung(row: dict) -> tuple:
    if row.get("resolution_match"):
        return (4, "res", "resolved")
    if row.get("issue_match"):
        return (3, "iss", "matched")
    if row.get("judged"):
        return (2, "no", "no match")
    if row.get("finding_location_hit"):
        return (1, "anc", "anchored")
    if row.get("candidate_location_hit"):
        return (1, "anc", "candidate here")
    return (0, "none", "nothing here")


def _gold_bar(bundle, gold: Optional[dict]) -> str:
    """Every maintainer ask on this PR, as one clickable row.

    The verdicts were reachable only by hunting: the matrix's gold column is invisible in
    the default view, and a badge in the diff is only found by scrolling onto it. A chip
    carries the verdict and selects the ask's target, so `resolved` and `matched` can be
    read off the page and jumped to.
    """

    if not gold:
        return ""
    by_change = gold.get("by_change", {})
    #: First target in page order wins: an obligation repeats under every target it names,
    #: and the chip has to land somewhere the reader can see it.
    anchored: Dict[str, tuple] = {}
    for site in bundle.sites:
        for row in by_change.get(site.change_id, ()):
            anchored.setdefault(row["obligation_id"], (row, site))

    chips = []
    for row, site in anchored.values():
        _, cls, label = _gold_rung(row)
        chips.append(
            f'<button class="gchip g-{cls}" data-goto="{_esc(site.change_id)}" '
            f'title="{_esc(row.get("claim") or "")}">'
            f'<span class="gn">{_esc(site.declaration_name)}</span>'
            f'<span class="gv">{_esc(label)}</span></button>'
        )
    for row in gold.get("unanchored", []):
        if row.get("pr_number") != bundle.pr_number:
            continue
        _, cls, label = _gold_rung(row)
        chips.append(
            f'<span class="gchip g-{cls} off" title="{_esc(row.get("claim") or "")}">'
            f'<span class="gn">unanchored</span>'
            f'<span class="gv">{_esc(label)}</span></span>'
        )
    if not chips:
        return ""
    return (
        f'<div class="goldbar"><span class="gb-lab">{len(chips)} maintainer ask'
        f"{'' if len(chips) == 1 else 's'}</span>" + "".join(chips) + "</div>"
    )


def _target_header(site, columns, groups, new_unit: Optional[dict],
                   obligations: Sequence[dict] = ()) -> str:
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
    gold_mark = ""
    gold_class = ""
    if obligations:
        # The best outcome among the asks anchored here — see `_gold_rung`.
        _, cls, label = max(_gold_rung(item) for item in obligations)
        gold_class = " goldtarget"
        gold_mark = (
            f'<span class="gmark g-{cls}">'
            f"{len(obligations)} ask{'' if len(obligations) == 1 else 's'} · "
            f"{label}</span>"
        )
    return (
        f'<div class="th{" newunit" if new_unit is not None else ""}{gold_class}" '
        f'data-id="{_esc(site.change_id)}" data-rank="{STATES.index(site.depth)}">'
        f'<span class="nm">{_esc(site.declaration_name)}</span>'
        f'<span class="sub">{_esc(site.lifecycle)} {_esc(site.subject_kind)}'
        f" · L{site.line_start}</span>"
        f"{sched}{unit}{gold_mark}"
        f"{_cell_strip(site, columns, groups)}</div>"
    )


def _diff_pane(bundle, columns: Sequence[dict], groups, gold: Optional[dict] = None) -> str:
    """The PR, as a PR: real files, real line numbers, real context, elisions counted.

    Targets are emitted as header rows in the flow rather than absolutely-positioned
    brackets. Entity spans tile each file without overlapping (measured: 0 overlaps across
    all 85 medium files), so a target owns a contiguous run of lines and a header placed at
    its first line is unambiguous — and it survives elision, which an overlay would not.
    """

    by_change = (gold or {}).get("by_change", {})
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
                                           units_by_change.get(site.change_id),
                                           by_change.get(site.change_id, ())))
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
                        bits.append(_target_header(
                            site, columns, groups, fresh,
                            by_change.get(site.change_id, ())))
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
                                           units_by_change.get(site.change_id),
                                           by_change.get(site.change_id, ())))
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

def _fmt_money(value) -> str:
    return "—" if value is None else f"${value:,.4f}"


def _lead_pane(bundle) -> str:
    """The lead's work: what it was given, what it decided, and what that cost.

    Rendered server-side rather than from the payload because it is a document, not an
    interactive surface -- and because the Gantt's geometry is arithmetic over timestamps
    that is easier to get right, and to test, in Python.
    """

    lead = bundle.lead
    if not lead:
        return '<div id="leadpane"></div>'

    ran = [job for job in lead["delegations"]
           if job["disposition"] in ("mandatory", "proposed", "agent_added")]
    declined = [job for job in lead["delegations"] if job["disposition"] == "pruned"]
    cost = lead.get("cost") or {}
    coverage = lead.get("coverage") or {}
    briefed = [job for job in ran if job.get("brief")]

    cards = [
        ("Proposed", len(lead["delegations"]), "(arm × site) jobs enumerated"),
        ("Delegated", len(ran),
         f"{sum(1 for j in ran if j['disposition'] == 'mandatory')} floor, "
         f"{sum(1 for j in ran if j['disposition'] != 'mandatory')} chosen"),
        ("Declined", len(declined), "the lead said no"),
        ("Briefed", len(briefed), "carried an instruction"),
        ("Cost", _fmt_money(cost.get("total")),
         f"lead {_fmt_money(cost.get('lead'))}, floor {_fmt_money(cost.get('mandatory'))}"),
    ]
    card_html = "".join(
        f'<div class="card"><em>{_esc(label)}</em><b>{_esc(value)}</b>'
        f'<i>{_esc(note)}</i></div>'
        for label, value, note in cards
    )

    caps = lead.get("caps") or {}
    given = (
        '<div class="lsec"><h2>What the lead was given</h2>'
        f'<p class="n">One lead runs per PR. It may route, and only route — it has '
        f'<code>delegate</code>, <code>read_agenda</code> and <code>submit_routing</code>, '
        f'and no way to emit a finding itself. Its budget: '
        f'{_fmt_money(caps.get("lead_cost_cap"))} for its own turns, '
        f'{_fmt_money(caps.get("per_pr_cost_cap"))} for this PR in total.</p>'
        f'<div class="cards">{card_html}</div>'
        f"{_arms_table(lead)}</div>"
    )

    return (
        '<div id="leadpane">'
        f"{given}"
        f"{_gantt(bundle, lead, ran)}"
        f"{_ladder(bundle, lead, ran)}"
        f"{_declined_table(declined)}"
        f"{_assessments(lead)}"
        "</div>"
    )


def _arms_table(lead) -> str:
    rows = lead.get("arms") or []
    if not rows:
        return ""
    widest = max((row["enumerated"] for row in rows), default=1) or 1
    body = []
    for row in rows:
        ran_w = 100.0 * row["ran"] / widest
        dec_w = 100.0 * row["declined"] / widest
        body.append(
            f'<tr class="{"mand" if row["mandatory"] else ""}">'
            f'<td>{_esc(row["arm_id"].replace("_", " "))}</td>'
            f'<td>{"floor" if row["mandatory"] else _esc(row.get("kind") or "")}</td>'
            f'<td style="width:36%"><span class="bar" style="width:{ran_w:.1f}%"></span>'
            f'<span class="bar d" style="width:{dec_w:.1f}%"></span></td>'
            f'<td class="n">{row["ran"]}</td><td class="n">{row["declined"]}</td>'
            f'<td class="n">{row["candidates"]}</td>'
            f'<td class="n">{_fmt_money(row["cost"])}</td></tr>'
        )
    return (
        '<table class="decl"><thead><tr><th>arm</th><th></th><th>ran / declined</th>'
        '<th class="n">ran</th><th class="n">declined</th><th class="n">claims</th>'
        f'<th class="n">cost</th></tr></thead><tbody>{"".join(body)}</tbody></table>'
    )


def _epoch(stamp) -> Optional[float]:
    """Parse an ISO stamp to seconds. Returns None rather than raising on a partial run."""

    if not stamp:
        return None
    from datetime import datetime

    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def _gantt(bundle, lead, ran) -> str:
    """Wall-clock bars, from the sidecar's per-invocation timestamps.

    Never from `delegations.jsonl::wall_seconds`, which is the tier's duration copied onto
    every job in it — on the held-out run 239 rows share 29 values, one repeated 108 times,
    so bars drawn from it would all be the same length and all wrong.
    """

    spans = [(job, _epoch(job.get("started_at")), _epoch(job.get("completed_at")))
             for job in ran]
    spans = [(job, start, end) for job, start, end in spans if start and end]
    if not spans:
        return (
            '<div class="lsec"><h2>Timeline</h2>'
            '<p class="n">No per-invocation timings — the trajectory sidecar was not '
            'extracted for this run, so only the logical sequence below is available. Run '
            '<code>-m src.datasets.pr_review_v5.trajectory --run &lt;run&gt;</code> to add it.'
            "</p></div>"
        )

    lead_start, lead_end = _epoch(lead.get("started_at")), _epoch(lead.get("completed_at"))
    origin = min([start for _job, start, _end in spans] + ([lead_start] if lead_start else []))
    finish = max([end for _job, _start, end in spans] + ([lead_end] if lead_end else []))
    total = max(finish - origin, 1e-6)

    def bar(start, end, klass, title):
        left = 100.0 * (start - origin) / total
        width = max(100.0 * (end - start) / total, 0.4)
        return (f'<span class="{klass}" style="left:{left:.2f}%;width:{width:.2f}%" '
                f'title="{_esc(title)}"></span>')

    rows = ['<div class="grow head"><span class="gl">who</span>'
            '<span class="gt"></span><span class="gm">time · cost</span></div>']
    if lead_start and lead_end:
        rows.append(
            '<div class="grow lead"><span class="gl">lead</span><span class="gt">'
            + bar(lead_start, lead_end, "", "lead")
            + f'</span><span class="gm">{lead_end - lead_start:.0f}s · '
              f'{_fmt_money(lead.get("lead_cost"))}</span></div>'
        )

    # Group by wave, in start order, so the bands read as the lead's successive decisions.
    waves: Dict[str, list] = {}
    for job, start, end in spans:
        waves.setdefault(job.get("wave") or "—", []).append((job, start, end))
    for wave in sorted(waves, key=lambda key: min(s for _j, s, _e in waves[key])):
        group = sorted(waves[wave], key=lambda item: item[1])
        floor = sum(1 for job, _s, _e in group if job["disposition"] == "mandatory")
        tiers = sorted({job.get("tier") or "?" for job, _s, _e in group})
        cost = sum(job.get("cost") or 0 for job, _s, _e in group)
        rows.append(
            f'<div class="wband"><b>{_esc(wave)}</b> · {len(group)} job(s) · '
            f'{floor} floor, {len(group) - floor} chosen · {_esc(", ".join(tiers))} · '
            f"{_fmt_money(cost)}</div>"
        )
        for job, start, end in group:
            klass = "mandatory" if job["disposition"] == "mandatory" else ""
            if job.get("status") and job["status"] != "success":
                klass = "failed"
            rows.append(
                f'<div class="grow" data-inv="{_esc(job["invocation_id"])}">'
                f'<span class="gl">{_esc(job["arm_id"].replace("_", " "))}</span>'
                f'<span class="gt">'
                + bar(start, end, klass,
                      f"{job['arm_id']} · {end - start:.0f}s · {_fmt_money(job.get('cost'))}")
                + f'</span><span class="gm">{end - start:.0f}s · '
                  f'{_fmt_money(job.get("cost"))}</span></div>'
            )

    concurrency = sum(end - start for _job, start, end in spans) / total
    return (
        '<div class="lsec"><h2>Timeline</h2>'
        f'<p class="n">{finish - origin:.0f} s wall for '
        f"{sum(end - start for _j, start, end in spans):.0f} s of agent time — "
        f"about {concurrency:.1f}× concurrent. Grey bars are the mandatory floor, which runs "
        f"whatever the lead asks; coloured bars are its own choices.</p>"
        f'<div class="gantt">{"".join(rows)}</div></div>'
    )


def _ladder(bundle, lead, ran) -> str:
    """The lead's turns, with each `delegate` batch expanded into the jobs it launched.

    This is where the reasoning is, and unlike the Gantt it survives without the sidecar:
    the ledger alone gives the jobs and their briefs.
    """

    conversation = (bundle.conversations or {}).get(lead.get("conversation_id") or "", [])
    names = {site.change_id: site.declaration_name for site in bundle.sites}
    by_wave: Dict[str, list] = {}
    for job in ran:
        by_wave.setdefault(job.get("wave") or "—", []).append(job)
    wave_order = sorted(by_wave, key=lambda key: min(
        (job.get("started_at") or "") for job in by_wave[key]))

    turns, batch = [], 0
    for turn in conversation:
        if turn.get("role") != "assistant":
            continue
        says = [item["v"] for item in turn.get("items", []) if item["t"] == "text"]
        uses = [item for item in turn.get("items", []) if item["t"] == "use"]
        if not says and not uses:
            continue
        tools = ", ".join(sorted({item.get("name") or "?" for item in uses}))
        block = [
            f'<div class="lturn{" act" if any(u.get("name") == "delegate" for u in uses) else ""}">'
            f'<div class="tno">turn {len(turns) + 1}'
            + (f" · {_esc(tools)}" if tools else "")
            + "</div>"
        ]
        for text in says:
            block.append(f'<div class="say">{_esc(text[:1200])}</div>')
        if any(item.get("name") == "delegate" for item in uses):
            wave = wave_order[batch] if batch < len(wave_order) else None
            batch += 1
            if wave is not None:
                block.append(_job_rows(by_wave[wave], wave, names))
        block.append("</div>")
        turns.append("".join(block))

    if not turns:
        # No transcript: fall back to the waves themselves, which the ledger always gives.
        for wave in wave_order:
            turns.append(
                f'<div class="lturn act"><div class="tno">{_esc(wave)}</div>'
                + _job_rows(by_wave[wave], wave, names) + "</div>"
            )

    note = (
        "Each <code>delegate</code> call launches a wave. The floor is prepended to wave 1 "
        "whatever the lead asks for, so an empty first <code>delegate</code> is the "
        "idiomatic opening move."
    )
    return (
        '<div class="lsec"><h2>What the lead did, in order</h2>'
        f'<p class="n">{note}</p><div class="ladder">{"".join(turns)}</div></div>'
    )


def _job_rows(jobs, wave, names=None) -> str:
    """One row per job. The work unit is identified by what it contains, not by its hash.

    A row used to read `wu:28601c8d1538799b6c5d4edc`, which tells a reader nothing; the
    declarations the unit covers tell them what the specialist was pointed at.
    """

    names = names or {}
    rows = []
    for job in sorted(jobs, key=lambda item: (item.get("started_at") or "", item["arm_id"])):
        sites = [names.get(change_id) for change_id in job.get("site_change_ids", [])]
        sites = [name for name in sites if name]
        if sites:
            label = ", ".join(sites[:2])
            if len(sites) > 2:
                label += f" +{len(sites) - 2} more"
        else:
            label = f'{len(job.get("site_change_ids", []))} site(s)'
        meta = " · ".join(filter(None, [
            job.get("tier"),
            f"{job['candidate_count']} claim(s)" if job.get("candidate_count") else "no claim",
            _fmt_money(job.get("cost")) if job.get("cost") is not None else None,
            f"{job['turns']} turns" if job.get("turns") else None,
        ]))
        link = (_conv_link(job["invocation_id"], "read") if job.get("has_transcript") else "")
        rows.append(
            f'<div class="job" data-inv="{_esc(job["invocation_id"])}">'
            f'<span class="ja">{_esc(job["arm_id"].replace("_", " "))}</span>'
            f'<span class="jw">{_esc(label)}'
            f'<span class="onlydebug"> {_esc(job["work_unit_id"])}</span></span>'
            f'<span class="jm">{_esc(meta)} {link}</span></div>'
            + (_brief_html(job["brief"]) if job.get("brief") else "")
        )
    return f'<div class="jobs">{"".join(rows)}</div>'


def _brief_html(brief) -> str:
    if not brief:
        return ""
    parts = [f'<div class="brief"><h4>the lead asked</h4>'
             f'<p class="claim">{_esc(brief.get("question"))}</p>']
    for key, label in (("because", "because"), ("already_checked", "already checked"),
                       ("abstain_if", "abstain if")):
        if brief.get(key):
            parts.append(f"<p><b>{label}</b> {_esc(brief[key])}</p>")
    if brief.get("look_at"):
        parts.append(f'<p><b>look at</b> {_esc("; ".join(brief["look_at"]))}</p>')
    return "".join(parts) + "</div>"


def _conv_link(conversation_id: str, label: str) -> str:
    return f'<a class="convlink" href="conv/{_conv_slug(conversation_id)}.html">{_esc(label)}</a>'


def _conv_slug(conversation_id: str) -> str:
    return "".join(
        char if char.isalnum() else "-" for char in str(conversation_id)
    ).strip("-")


def _declined_table(declined) -> str:
    """What the lead chose not to do. The larger half of the routing decision."""

    if not declined:
        return ""
    by_arm: Dict[str, int] = {}
    for job in declined:
        by_arm[job["arm_id"]] = by_arm.get(job["arm_id"], 0) + 1
    reasons = {job.get("reason") for job in declined if job.get("reason")}
    chips = "".join(
        f'<span class="chip">{_esc(arm.replace("_", " "))} {count}</span>'
        for arm, count in sorted(by_arm.items(), key=lambda item: -item[1])
    )
    return (
        '<div class="lsec"><h2>What the lead declined</h2>'
        f'<p class="n">{len(declined)} of the enumerated jobs were never run. The mandatory '
        "floor means no site goes unlooked-at, so what is declined here is always "
        "<em>specialist</em> coverage at a site the generalist already saw.</p>"
        f'<div class="chips">{chips}</div>'
        + (f'<p class="n">Stated reason: {_esc("; ".join(sorted(reasons))[:300])}</p>'
           if reasons else "")
        + "</div>"
    )


def _assessments(lead) -> str:
    """The lead's verdicts on what came back — recorded by design, and never applied."""

    rows = lead.get("assessments") or []
    if not rows:
        return ""
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.get("verdict") or "?"] = counts.get(row.get("verdict") or "?", 0) + 1
    chips = "".join(f'<span class="chip">{_esc(key)} {value}</span>'
                    for key, value in sorted(counts.items()))
    body = "".join(
        f'<tr><td>{_esc(row.get("verdict"))}</td>'
        f'<td>{_esc((row.get("reason") or "")[:180])}</td></tr>'
        for row in rows[:20]
    )
    return (
        '<div class="lsec"><h2>What the lead thought of the results</h2>'
        f'<p class="n">v1 gives the lead authority over routing only. These verdicts are '
        "recorded because they are the evidence for whether arbitration is worth building "
        "next — the finalization chain never reads them, so nothing here changed what was "
        "published.</p>"
        f'<div class="chips">{chips}</div>'
        f'<table class="decl"><thead><tr><th>verdict</th><th>reason</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )

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
        if not counts.get(state):
            continue
        parts.append(
            f'<button class="key s-{state}" data-state="{state}"><i></i>'
            f'{_esc(STATE_LABEL[state])} <b>{counts[state]}</b></button>'
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

    # The PR itself, from the episode's own `repo` rather than a hardcoded host: the
    # overlay renders whatever release it is pointed at, and a wrong link is worse than
    # none. Opens in a new tab so the reader does not lose the page's toggled state.
    gh_button = (
        f'<button class="tg"><a href="https://github.com/{_esc(bundle.repo)}/pull/'
        f'{bundle.pr_number}" target="_blank" rel="noopener noreferrer" '
        f'title="open PR #{bundle.pr_number} on GitHub">github &#8599;</a></button>'
        if bundle.repo
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
        # Slim: the browser needs the cost split and a click index from invocation to sites.
        # The delegation detail is rendered server-side, and re-shipping it would duplicate
        # ~1,000 rows into PR 33149's page for nothing.
        "lead": (
            {
                "cost": bundle.lead["cost"],
                "lead_cost": bundle.lead.get("lead_cost"),
                "coverage": bundle.lead.get("coverage"),
                "delegations": [
                    {
                        "invocation_id": job["invocation_id"],
                        "arm_id": job["arm_id"],
                        "site_change_ids": job["site_change_ids"],
                    }
                    for job in bundle.lead["delegations"]
                ],
            }
            if bundle.lead else None
        ),
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
        + ('<button class="tg" id="leadbtn" title="what the lead routed and what it cost">'
           "lead</button>" if bundle.lead else "")
        + '<button class="tg" id="viewbtn" title="switch between the diff and the matrix">'
        "matrix view</button>"
        '<button class="tg" id="debugbtn" title="show ids, hashes and pipeline internals">'
        "debug</button>"
        + gh_button
        + ("" if standalone else '<button class="tg"><a href="index.html">all PRs</a></button>')
        + "</div></header>"
        f"{_ribbon(bundle)}{_legend(bundle)}{_gold_bar(bundle, gold)}"
        '<div class="body"><div class="viewwrap">'
        f"{_rail(bundle)}"
        f"{_diff_pane(bundle, columns, groups, gold)}"
        '<div class="canvas" id="matrixpane">'
        f"{_matrix(bundle, gold)}"
        "</div>"
        f"{_lead_pane(bundle)}"
        "</div>"
        '<aside id="panel"></aside></div></div>'
        '<div id="tip"></div>'
        "<script>"
        f"{_blob('PR', payload, standalone)}"
        f"{_blob('GOLD', pr_gold, standalone)}"
        f"{_blob('SRC', sources, standalone)}"
        f"{_blob('RUNCOST', (sources or {}).get('run_cost'), standalone)}"
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


def conversation_page(conversation_id: str, turns: Sequence[dict], meta: dict) -> str:
    """One conversation, as a document.

    A separate file rather than a section of the overlay page. The held-out run's PR 33149
    draws a mandatory generalist on each of its 108 work units, and its transcripts alone are
    3.9 MB; embedding them would make every page pay for the worst one, and an "embed when
    small" rule would give the same click two different behaviours.

    Assistant text is verbatim. Tool results are capped by the extractor and the true byte
    count is shown, because a truncated result that does not say it was truncated is a lie
    about what the agent saw.
    """

    head = []
    for label, value in meta.get("facts", []):
        if value not in (None, "", []):
            head.append(f'<div class="card"><em>{_esc(label)}</em>'
                        f'<b>{_esc(value)}</b></div>')

    blocks = []
    for index, turn in enumerate(turns):
        items = []
        for item in turn.get("items", []):
            kind = item.get("t")
            if kind in ("text", "think"):
                label = "" if kind == "text" else '<div class="tno">reasoning</div>'
                items.append(f"{label}<p>{_esc(item.get('v'))}</p>")
            elif kind == "use":
                items.append(
                    '<div class="tcall"><div class="th2">'
                    f'<b>{_esc(item.get("name"))}</b><span>called</span></div>'
                    f'<pre>{_esc(item.get("v"))}</pre>'
                    + _truncation_note(item)
                    + "</div>"
                )
            elif kind == "res":
                items.append(
                    '<div class="tcall res"><div class="th2">'
                    f'<b>{_esc(item.get("name"))}</b><span>returned</span></div>'
                    f'<pre>{_esc(item.get("v"))}</pre>'
                    + _truncation_note(item)
                    + "</div>"
                )
        if not items:
            continue
        stamp = (turn.get("ts") or "")[11:23]
        blocks.append(
            f'<div class="cturn"><div class="ch"><b>{_esc(turn.get("role"))}</b>'
            f'<span>turn {index + 1}</span><span>{_esc(stamp)}</span></div>'
            f'<div class="body">{"".join(items)}</div></div>'
        )

    back = meta.get("back")
    return (
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(meta.get('title') or conversation_id)}</title>"
        f"<style>{_CSS}\n{_state_css()}</style>"
        '<div class="cpage">'
        f'<div class="eyebrow">conversation · {_esc(meta.get("eyebrow") or "")}</div>'
        f"<h1>{_esc(meta.get('title') or conversation_id)}</h1>"
        + (f'<p class="sub"><a class="convlink" href="{_esc(back)}">'
           f"&larr; back to the overlay</a></p>" if back else "")
        + (f'<div class="cards">{"".join(head)}</div>' if head else "")
        + (_brief_html(meta["brief"]) if meta.get("brief") else "")
        + (f'<div class="kv onlydebug" style="display:revert">{_esc(conversation_id)}</div>')
        + "".join(blocks)
        + (f'<p class="empty">No transcript was recorded for this conversation.</p>'
           if not blocks else "")
        + "</div>"
    )


def _truncation_note(item: dict) -> str:
    shown, total = len(item.get("v") or ""), item.get("bytes")
    if not total or total <= shown:
        return ""
    return (f'<div class="trunc">showing {shown:,} of {total:,} bytes'
            f" — truncated by the extractor</div>")


def conversation_pages(bundle) -> Dict[str, str]:
    """Every conversation this PR produced, keyed by output filename."""

    lead = bundle.lead
    if not lead or not bundle.conversations:
        return {}
    jobs = {job["invocation_id"]: job for job in lead["delegations"]}
    pages: Dict[str, str] = {}
    for conversation_id, turns in bundle.conversations.items():
        job = jobs.get(conversation_id)
        if job is not None:
            facts = [
                ("arm", job["arm_id"].replace("_", " ")),
                ("disposition", job["disposition"]),
                ("tier", job.get("tier")),
                ("turns", job.get("turns")),
                ("cost", _fmt_money(job.get("cost"))),
                ("time", f"{job['execution_time']:.0f}s" if job.get("execution_time") else None),
                ("claims", job.get("candidate_count")),
            ]
            meta = {
                "title": f"{job['arm_id'].replace('_', ' ')} · PR {bundle.pr_number}",
                "eyebrow": f"PR {bundle.pr_number} · {job['work_unit_id']}",
                "facts": facts, "brief": job.get("brief"),
                "back": f"../pr-{bundle.pr_number}.html",
            }
        else:
            meta = {
                "title": f"lead · PR {bundle.pr_number}",
                "eyebrow": f"PR {bundle.pr_number} · routing",
                "facts": [
                    ("turns", lead.get("turns")),
                    ("cost", _fmt_money(lead.get("lead_cost"))),
                    ("time", f"{lead['execution_time']:.0f}s"
                     if lead.get("execution_time") else None),
                    ("delegated", len([j for j in lead["delegations"]
                                       if j["disposition"] != "pruned"])),
                ],
                "back": f"../pr-{bundle.pr_number}.html",
            }
        pages[f"{_conv_slug(conversation_id)}.html"] = conversation_page(
            conversation_id, turns, meta
        )
    return pages

def write_index(bundles: Sequence, gold: Optional[dict], sources: Optional[dict] = None) -> str:
    sources = sources or {}
    by_pr = {pr: len(ids) for pr, ids in _distinct_obligations(gold).items()}
    # Without these, finding a match meant opening every PR in turn.
    gold_cols = [
        ("obligations", by_pr),
        ("matched", {pr: len(ids)
                     for pr, ids in _obligations_where(gold, "issue_match").items()}),
        ("resolved", {pr: len(ids)
                      for pr, ids in _obligations_where(gold, "resolution_match").items()}),
    ] if gold else []
    gold_head = (
        "".join(f"<th class='n'>{name}</th>" for name, _ in gold_cols)
        if gold_cols else "<th class='n'></th>"
    )

    # `build_overlay` nulls v4's treatment and executor for a v5 run, and the arms it
    # counts candidates over are never loaded for one, so `investigations` and `candidates`
    # can only read 0 on a v5 page. The per-PR pages already drop v4's method columns; this
    # one drops their two totals rather than printing a column of zeros.
    counts = ["sites", "investigations", "candidates", "findings", "published"]
    if any(getattr(bundle, "lead", None) for bundle in bundles):
        counts = ["sites", "findings", "published"]

    rows = []
    for bundle in bundles:
        cells = "".join(f"<td class='n'>{bundle.totals[key]}</td>" for key in counts)
        # Blank rather than 0: the column is scanned for the PRs worth opening.
        cells += (
            "".join(f"<td class='n'>{seen.get(bundle.pr_number) or ''}</td>"
                    for _, seen in gold_cols)
            if gold_cols else "<td class='n'></td>"
        )
        rows.append(
            f"<tr><td><a href='pr-{bundle.pr_number}.html'>#{bundle.pr_number}</a>"
            f"<span class='t'>{_esc(bundle.title)}</span></td>{cells}</tr>"
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
        "<table><thead><tr><th>PR</th>"
        + "".join(f"<th class='n'>{key}</th>" for key in counts)
        + gold_head + "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f'<div class="src">{src}</div></div>'
    )
