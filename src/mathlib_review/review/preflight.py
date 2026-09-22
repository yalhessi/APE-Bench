"""Every ambient thing a v5 run depends on, declared in one place and checked before spend.

A v5 run reaches outside itself four times: it resolves paths relative to the repository
root, it shells out to `lake`, it calls a model with a credential from the environment, and
it mounts prebuilt Lean workspaces. None of those are arguments — they are properties of the
machine the run happens to start on, and until this module existed each was discovered
separately, late, and in three cases silently.

The cost of "silently" is not hypothetical. One held-out run failed **225 of 225**
verifications with `return_code 127` and `stdbuf: failed to run command 'lake': No such file
or directory`, because the launching shell had never exported the elan bin directory. Every
specialist in that run built an edit, asked for a compile warrant, got nothing back, and
correctly abstained. The run completed, wrote a manifest, cost real money, and read as *the
agents found nothing* — a statement about the model, drawn from a fact about `PATH`.

So the rules here are deliberate:

* **Declare, never guess.** An earlier version of this check searched `~/.elan/bin` and
  friends and patched `PATH` from whatever it found. It did not even locate *this* machine's
  toolchain, which lives outside `$HOME` — and had it succeeded it would have been worse,
  because a run that silently repairs its own environment cannot tell you which toolchain
  compiled its evidence. `lake` comes from `PATH`, or from a path the operator wrote down.
* **Fail before the first token, not after the last.** These checks cost milliseconds; the
  run they guard costs tens of dollars and hours.
* **Report every failure at once.** A machine that is missing two prerequisites should take
  one round trip to fix, not two.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.analysis.runs import unbuilt_base_commits

from src.mathlib_review.paths import assert_repo_root


class PreflightError(RuntimeError):
    """A run refused to start because the machine does not meet a declared prerequisite."""


@dataclass(frozen=True)
class Unmet:
    """One prerequisite that is not satisfied, and what to do about it.

    `consequence` is not decoration. Each of these failures has a characteristic way of
    being misread downstream, and naming it is what stops the next person from spending an
    afternoon attributing an environment fault to the agent.
    """

    name: str
    consequence: str
    remedy: str

    def render(self) -> str:
        return f"  [{self.name}]\n    {self.consequence}\n    fix: {self.remedy}"


def _check_repo_root() -> Optional[Unmet]:
    try:
        assert_repo_root()
    except RuntimeError as error:
        return Unmet(
            name="repository root",
            consequence=str(error).replace("\n", " "),
            remedy="cd to the repository root and re-run.",
        )
    return None


def _check_toolchain(scaffold: Any, logger: Any) -> Optional[Unmet]:
    """Resolve `lake` from `PATH`, or from an explicitly configured directory.

    When the operator has declared `lean_toolchain_bin`, it is prepended to this process's
    `PATH` **once, here**, so that every orchestrator, task and subprocess below inherits it
    from one visible decision. That is a different thing from the per-invocation repair this
    replaced: it happens at a single point, it comes from config rather than from a search,
    and the resolved binary is logged into the run.
    """

    configured = getattr(
        getattr(getattr(scaffold, "tools_config", None), "lean_verify", None),
        "lean_toolchain_bin", None)
    if configured:
        declared = Path(configured).expanduser()
        if not (declared / "lake").is_file():
            return Unmet(
                name="lean toolchain",
                consequence=(
                    f"tools_config.lean_verify.lean_toolchain_bin is {declared}, but there "
                    "is no `lake` in it. A declaration that does not resolve is worse than "
                    "none, because it reads as though the toolchain were pinned."
                ),
                remedy="point lean_toolchain_bin at the directory that holds `lake`.",
            )
        os.environ["PATH"] = f"{declared}{os.pathsep}{os.environ.get('PATH', '')}"
        logger.info("lean toolchain (declared in config): %s", declared / "lake")
        return None

    found = shutil.which("lake")
    if not found:
        return Unmet(
            name="lean toolchain",
            consequence=(
                "`lake` is not on PATH. Every verification would exit 127 with no Lean "
                "diagnostics, every specialist claim would be dropped for lacking a compile "
                "warrant, and the run would report that the agents found nothing."
            ),
            remedy=(
                "export PATH=\"$ELAN_HOME/bin:$PATH\" in the launching shell, or write the "
                "directory down in tools_config.lean_verify.lean_toolchain_bin so it "
                "survives a new shell."
            ),
        )
    logger.info("lean toolchain: %s", found)
    return None


def _check_model_credential(scaffold: Any) -> Optional[Unmet]:
    """A credential is required for every mode that calls a model.

    `LLMConfig.model_post_init` already resolves the provider's environment variable into
    `api_key`, so this reads the resolved value and stays provider-agnostic.
    """

    llm = getattr(scaffold, "llm_config", None)
    if llm is None or getattr(llm, "model_name", None) is None:
        return None
    if getattr(llm, "api_key", None):
        return _check_credential_survives_worker(llm)
    provider = getattr(getattr(llm, "provider_type", None), "value", "the provider")
    return Unmet(
        name="model credential",
        consequence=(
            f"no API key resolved for {provider} (model {llm.model_name}). Every task would "
            "fail on its first call, after the plan is sealed and the run directory written."
        ),
        remedy=(
            f"export the provider's key in the launching shell ({_key_env_var_hint(llm)}), or "
            "set llm_config.api_key in the config."
        ),
    )


def _key_env_var_hint(llm: Any) -> str:
    """The environment variable this provider reads, named so the remedy is actionable."""

    from ape.llm_clients.config import PROVIDER_KEY_ENV_VARS

    names = PROVIDER_KEY_ENV_VARS.get(getattr(llm, "provider_type", None))
    return " or ".join(names) if names else "the provider's key variable"


def _check_credential_survives_worker(llm: Any) -> Optional[Unmet]:
    """A key that came from YAML rather than the environment dies at the process boundary.

    `LLMConfig.api_key` is `exclude=True`, so it is absent from the `model_dump` that carries
    the scaffold config to a worker process -- deliberately, because that same dump is the
    on-disk run snapshot, the container runtime's argv and the `scaffold_config_sha256` input.
    A worker rebuilds the key by re-resolving the environment variable, which works for every
    key that came from the environment in the first place and for no other.

    So the YAML case fails in the worker, on the first call, after the plan is sealed. It is
    cheap to refuse here instead, and the remedy is one line.
    """

    from ape.llm_clients.config import LLMConfig

    if LLMConfig._resolve_api_key_from_environment(getattr(llm, "provider_type", None)):
        return None
    return Unmet(
        name="model credential source",
        consequence=(
            f"llm_config.api_key is set in the config but {_key_env_var_hint(llm)} is not "
            "exported. The key is deliberately not serialized, so it would not reach the "
            "worker processes and every task would fail on its first call."
        ),
        remedy=f"export {_key_env_var_hint(llm)} in the launching shell instead.",
    )


def assert_ready(scaffold: Any, logger: Any, *, enforce: bool = True) -> None:
    """Check every machine-level prerequisite, and raise once naming all that are unmet.

    `enforce=False` reports the same findings as warnings instead of raising. That is the
    dry-run posture: a dry run calls no model and compiles nothing, so a machine that cannot
    execute the run can still legitimately validate its config — and being told, in advance,
    exactly what would stop the real run is the entire point of the command. It stays loud
    because it spends nothing.
    """

    unmet = [item for item in (
        _check_repo_root(),
        _check_toolchain(scaffold, logger),
        _check_model_credential(scaffold),
    ) if item is not None]
    if not unmet:
        return
    report = (
        f"{len(unmet)} prerequisite(s) are not met on this machine"
        f"{', so the run has not started' if enforce else ''}:\n\n"
        + "\n\n".join(item.render() for item in unmet) + "\n\n"
        "These are properties of the environment, not of the config or the data. A run that "
        "starts without them produces artifacts that look like results."
    )
    if not enforce:
        logger.warning("preflight (not enforced on a dry run):\n%s", report)
        return
    raise PreflightError(report)


def assert_toolchain(scaffold: Any, logger: Any) -> None:
    """The toolchain check alone, for a caller that compiles Lean and calls no model.

    The reviewed-workspace prebuild is such a caller: it needs `lake`, and it needs the same
    `lean_toolchain_bin` decision the run will make, so that the workspace it builds and the
    verification that later runs in it come from one toolchain. It does not need a model
    credential, and refusing it for lacking one would be a refusal for a reason that does not
    apply.
    """

    unmet = [item for item in (_check_repo_root(), _check_toolchain(scaffold, logger)) if item]
    if unmet:
        raise PreflightError("\n\n".join(f"{u.name}: {u.consequence}\n  -> {u.remedy}" for u in unmet))


async def reviewed_workspace_keys(episodes: Iterable[Any]) -> Dict[str, Any]:
    """`key -> episode` for every episode that carries a diff. Computed from the episodes, not
    the task data: a solo run has one task per episode and an arm run has hundreds per PR, and
    the reviewed workspace is a property of the episode either way."""

    from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

    keys: Dict[str, Any] = {}
    for episode in episodes:
        diff = getattr(episode, "diff", "") or ""
        base = getattr(episode, "base_sha", "") or ""
        if base and diff.strip():
            keys[reviewed_workspace_key(base, diff)] = episode
    return keys


async def unbuilt_reviewed_workspaces(episodes: Iterable[Any]) -> Dict[str, Any]:
    """The episodes whose reviewed workspace is not built, keyed by the workspace they need."""

    keys = await reviewed_workspace_keys(episodes)
    missing = set(await unbuilt_base_commits(keys))
    return {key: episode for key, episode in keys.items() if key in missing}


async def assert_reviewed_workspaces_prebuilt(
    episodes: Iterable[Any], *, required: bool, logger=None
) -> Dict[str, Any]:
    """Refuse a run whose episodes would be verified against the base commit's build products.

    A reviewed workspace is the base snapshot plus the PR's diff plus its changed modules
    rebuilt. Without it, every compile resolves imports through the base `.olean`s, and a
    declaration the PR adds or renames in a sibling file is `Unknown constant` in every other
    file -- 41 of 321 arm sessions on the held-out run, 16 findings asserting a build failure on
    PRs that all build. That is a property of the run's environment, decided before the first
    model call, so it is refused here rather than discovered in the findings.

    Always reports what is missing, so `plan` can say it. Refuses only when `required`, so a
    run can be configured to accept the degraded environment knowingly -- the task then logs
    the fallback at WARNING per attempt and the attribution note names the artifact.
    """

    missing = await unbuilt_reviewed_workspaces(episodes)
    if missing and logger:
        prs = sorted({getattr(ep, "pr_number", "?") for ep in missing.values()})
        logger.warning(
            "%d episode(s) have no reviewed workspace (PRs %s); verification would resolve "
            "imports against the base commit's build products",
            len(missing), prs)
    if missing and required:
        prs = sorted({getattr(ep, "pr_number", "?") for ep in missing.values()})
        raise PreflightError(
            f"{len(missing)} reviewed workspace(s) are not prebuilt (PRs {prs}). A run against "
            "the base commit's build products reads the PR's own renames as unknown constants. "
            "Build them first:\n  ./ape/bin/python -m src.mathlib_review.release.prebuild "
            "--reviewed --config <this run config>\n"
            "or set `dataset.require_reviewed_workspaces: false` to accept that environment."
        )
    return missing


async def assert_workspaces_prebuilt(
    data: Iterable[Dict[str, Any]], *, required: bool = True
) -> None:
    """The one prerequisite that cannot be checked at startup, because it depends on the data.

    Kept in this module anyway: the point of a preflight is that the full set of things a run
    assumes about its machine is readable in one file.
    """

    if not required:
        return
    missing = await unbuilt_base_commits(
        item["target_workspace"]["commit_hash"] for item in data
    )
    if missing:
        raise PreflightError(
            f"{len(missing)} base workspace(s) are not prebuilt: {missing}. Run "
            "`./ape/bin/python -m src.mathlib_review.release.prebuild --config "
            "<a v4 config for this release>`, then the printed lean build command."
        )
