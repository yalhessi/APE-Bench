module

public import Mathlib
import Fold

open Lean Meta Elab Command in
#eval show CommandElabM Unit from do
  let env ← getEnv
  let target := `Pi.single_apply
  let m1 := env.constants.map₁
  let inM1 := m1.contains target
  let mut nMod := 0; let mut inMod := false; let mut nThmMod := 0
  for mod in env.header.moduleData do
    nMod := nMod + mod.constants.size
    for ci in mod.constants do
      if ci.name == target then inMod := true
      if ci matches .thmInfo _ then nThmMod := nThmMod + 1
  let kenv := env.toKernelEnv
  let km1 := kenv.constants.map₁
  let inK := km1.contains target
  let mut nThmK := 0
  for (_, ci) in km1.toList do
    if ci matches .thmInfo _ then nThmK := nThmK + 1
  let found := (env.find? target).isSome
  logInfo m!"constants.map₁ size {m1.size}, has target {inM1}; moduleData consts {nMod} (theorems {nThmMod}), has target {inMod}; kernel map₁ size {km1.size} (theorems {nThmK}), has target {inK}; find? {found}; modules {env.header.moduleData.size}"
