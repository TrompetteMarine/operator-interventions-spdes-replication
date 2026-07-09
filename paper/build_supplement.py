#!/usr/bin/env python3
"""Consolidate WP1-WP8 theorem archives into one citable supplement.

Transforms per file: extract preamble macros (group-local re-definitions),
strip document scaffolding, inline the v2 proof closures over the sketch
proofs, demote sections, namespace labels/refs with wpN:, capture bibitems.
Output: supplement_parts.tex + supplement_bib.tex (merged, deduped).
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "wp_src"
CLO = ROOT / "closures"

PARTS = [
    ("wp1", "wp1_operator_intervention_semantics_theorems.tex",
     "Intervention semantics and Galerkin limits"),
    ("wp2", "wp2_target_identification_theorems.tex",
     "Target identification"),
    ("wp3", "wp3_lan_efficiency_theorems.tex",
     "Exact likelihood, mixed-rate LAN, and efficient estimation"),
    ("wp4", "wp4_counterfactual_process_theorems.tex",
     "Uniform post-intervention target processes"),
    ("wp5", "wp5_multiplier_bootstrap_theorems.tex",
     "Multiplier bootstrap and simultaneous inference"),
    ("wp6", "wp6_operator_sensitivity_theorems.tex",
     "Operator sensitivity and response derivatives"),
    ("wp7", "wp7_total_error_theorems.tex",
     "Total statistical--numerical error"),
    ("wp8", "wp8_nonidentification_theorems.tex",
     "Non-identification boundary"),
]

# (wp, old, new) — proto-submittability patches: precise citations plus
# hypothesis verification at points where external results were invoked
# by name only. Applied before closure inlining and namespacing.
CITATION_PATCHES = [
    ("wp1",
     "The stochastic-convolution factorisation identity gives",
     "The stochastic-convolution factorisation identity "
     "(\\citealp[Section~5.3]{DPZ2014}; going back to \\citealp{DPKZ1987}) "
     "gives"),
    ("wp1",
     "The required stochastic Fubini interchange is justified by the "
     "preceding square-integrability estimate.",
     "The required stochastic Fubini interchange is justified by the "
     "preceding square-integrability estimate, which is exactly the "
     "integrability hypothesis of the stochastic Fubini theorem "
     "\\citep[Theorem~4.33]{DPZ2014}."),  # CHECK theorem number (2nd ed.)
    ("wp4",
     "Tightness therefore follows by the functional delta method and "
     "compact-index continuity.",
     "Tightness therefore follows by the functional delta method "
     "\\citep[Theorem~3.9.4]{vdVW1996} --- its hypotheses hold here: the "
     "target map is uniformly Fr\\'echet, hence Hadamard, differentiable by "
     "Theorem~\\ref{thm:Frechet}, the domain is a finite-dimensional "
     "parameter neighbourhood, and the normalised estimator converges "
     "weakly by Work Package~3 --- and compact-index continuity."),
    ("wp6",
     "The bounded perturbation theorem and the Dyson--Phillips estimate "
     "give",
     "The bounded perturbation theorem \\citep[Theorem~III.1.3]"
     "{EngelNagel2000} and the Dyson--Phillips series estimate "
     "\\citep[Chapter~3]{Pazy1983} give"),
    ("wp6",
     "Use \\eqref{eq:epsilon}.",
     "Use \\eqref{eq:epsilon}. (The hypotheses of the perturbation theorem "
     "hold: $A$ generates a $C_0$-semigroup with "
     "$\\norm{S(t)}\\le Me^{-\\omega t}$ by "
     "Assumption~\\ref{ass:semigroup}, and $\\varepsilon B$ is a bounded "
     "operator with $\\norm{\\varepsilon B}\\le\\varepsilon_0R$.)"),
    ("wp7",
     "the optimal coupling of two non-degenerate one-dimensional Gaussian "
     "laws contains",
     "the optimal coupling of two non-degenerate one-dimensional Gaussian "
     "laws (for which $W_2^2=(m_1-m_2)^2+(\\sqrt{v_1}-\\sqrt{v_2})^2$; "
     "see, e.g., \\citealp[Chapter~6]{Villani2009}) contains"),
]

# Merged-document deduplication: WP statements that (re)state a main-text
# result get an "establishes \Cref{...}" mark in the environment title
# (benchmark pattern: equivalence flagged in the title). Merged variant only —
# main-text labels do not exist in the standalone supplement.
DEDUP = {
    "wp1:thm:exact": "prop:exact-scm",
    "wp1:thm:semantics": "thm:semantics",
    "wp2:prop:gaussian-target": "prop:gaussian-law",
    "wp2:thm:fibre": "thm:fibre",
    "wp2:thm:exact-id": "thm:exact-id",
    "wp2:thm:operator-kernel": "prop:partial",
    "wp3:thm:LAN": "thm:lan",
    "wp3:thm:MLE-CLT": "thm:lan",
    "wp3:thm:efficiency": "thm:lan",
    "wp3:thm:moment-convergence": "thm:lan",
    "wp4:thm:fast-cf": "thm:processes",
    "wp4:thm:slow-fact": "thm:processes",
    "wp4:thm:quantile": "thm:quantile-tail",
    "wp5:thm:raw-band": "thm:bands",
    "wp5:thm:st-band": "thm:bands",
    "wp6:thm:mild-derivative": "thm:sensitivity",
    "wp6:thm:CDF-derivative": "thm:sensitivity",
    "wp6:thm:W2": "thm:sensitivity",
    "wp7:thm:total": "thm:total-error",
    "wp8:thm:gauge": "thm:gauge-main",
    "wp8:thm:not-descend": "thm:gauge-main",
    "wp8:thm:assembly": "thm:nonid-assembly",
}

# (wp, anchor label, closure file) — closure replaces the first
# "Proof structure/sketch" environment following the anchor label.
CLOSURES = [
    ("wp3", "lem:score-clt", "closure_wp3_score_clt.tex"),
    ("wp3", "lem:remainder", "closure_wp3_remainder.tex"),
    ("wp3", "lem:KL", "closure_wp3_KL.tex"),
    ("wp3", "thm:consistency", "closure_wp3_consistency.tex"),
    ("wp3", "thm:PLDI", "closure_wp3_PLDI.tex"),
    ("wp4", "thm:contact", "closure_wp4_contact.tex"),
    ("wp5", "lem:block", "closure_wp5_block.tex"),
    ("wp5", "thm:st-band", "closure_wp5_stband.tex"),
    ("wp5", "thm:contact", "closure_wp5_contact.tex"),
    ("wp7", "thm:target-derivative", "closure_wp7_target_derivative.tex"),
]

MACRO_RE = re.compile(r"^\\(?:re)?newcommand\{(\\[^}]+)\}", re.M)
PROOF_RE = re.compile(
    r"\\begin\{proof\}\[Proof (?:structure|sketch)\].*?\\end\{proof\}",
    re.S)
REF_RE = re.compile(r"\\(label|ref|eqref|cref|Cref|autoref)\{([^}]*)\}")
BIB_RE = re.compile(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                    re.S)
BIBITEM_RE = re.compile(r"(\\bibitem\{([^}]+)\}.*?)(?=\\bibitem\{|\Z)", re.S)


def extract_macros(preamble: str) -> str:
    out = []
    for line in preamble.splitlines():
        ls = line.strip()
        if ls.startswith("\\newcommand") or ls.startswith("\\renewcommand"):
            m = MACRO_RE.match(ls)
            if m:
                name = m.group(1)
                body = re.sub(r"^\\(?:re)?newcommand", r"\\renewcommand", ls)
                out.append(f"\\providecommand{{{name}}}{{}}{body}")
    return "\n".join(out)


def inline_closures(body: str, wp: str) -> str:
    for w, anchor, fname in CLOSURES:
        if w != wp:
            continue
        pos = body.find(f"\\label{{{anchor}}}")
        if pos < 0:
            print(f"  !! anchor {anchor} not found in {wp}")
            continue
        m = PROOF_RE.search(body, pos)
        if not m:
            print(f"  !! sketch proof after {anchor} not found in {wp}")
            continue
        closure = (CLO / fname).read_text()
        # strip leading comment lines of the closure file
        closure = "\n".join(l for l in closure.splitlines()
                            if not l.lstrip().startswith("% Closure")
                            and not l.lstrip().startswith("% NOTE:")
                            and not l.lstrip().startswith("% Route:")
                            and not l.lstrip().startswith("% Engine:")
                            and not l.lstrip().startswith("% (i")
                            and not l.lstrip().startswith("% the ")
                            and not l.lstrip().startswith("% pointwise")
                            and not l.lstrip().startswith("% bound")
                            and not l.lstrip().startswith("% argument")
                            and not l.lstrip().startswith("% requires")
                            and not l.lstrip().startswith("% sigma exactly")
                            and not l.lstrip().startswith("% growth"))
        body = body[:m.start()] + closure + body[m.end():]
        print(f"  closed {anchor} <- {fname}")
    return body


PREFIXED = re.compile(r"^(wp\d|part):")


def namespace(body: str, wp: str) -> str:
    def sub(m):
        cmd, keys = m.group(1), m.group(2)
        new = ",".join(
            k if (not k.strip() or PREFIXED.match(k.strip()))
            else f"{wp}:{k.strip()}"
            for k in keys.split(","))
        return f"\\{cmd}{{{new}}}"
    return REF_RE.sub(sub, body)


def dedup_marks(body: str, wp: str) -> str:
    """Merged variant: flag WP statements equivalent to main-text results."""
    for nslbl, main in DEDUP.items():
        if not nslbl.startswith(wp + ":"):
            continue
        pat = re.compile(
            r"(\\begin\{(?:theorem|proposition|lemma)\}\[)([^\]]*)"
            r"(\]\s*\\label\{" + re.escape(nslbl) + r"\})")
        body, n = pat.subn(
            lambda m: m.group(1) + m.group(2)
            + f"; establishes \\Cref{{{main}}}" + m.group(3), body)
        if n != 1:
            print(f"  !! dedup mark {nslbl}: matched {n}")
    return body


def demote_once_more(body: str) -> str:
    """Merged variant: parts become subsections of the proofs section."""
    body = body.replace("\\subsubsection", "\\paragraph")
    body = body.replace("\\subsection", "\\subsubsection")
    body = body.replace("\\section", "\\subsection")
    return body


# Merged manuscript: internal meta-sections of the archives that a stand-alone
# reader does not need (validation, completion statements, positioning).
# NB: applied AFTER the standard transform, so sections are \subsection and
# the abstract has become the \paragraph*{Overview.} block.
DROP_SECTIONS = re.compile(
    r"\\subsection\{(?:[^}]*[Cc]ompletion statement[^}]*|Monte Carlo[^}]*"
    r"|Numerical validation|Finite-dimensional validation"
    r"|Position and objective|Heat-equation corollary"
    r"|Location in the research programme[^}]*"
    r"|Causal response geometry"
    r"|Root-information inference and Decision Gate[^}]*"
    r"|Interface with[^}]*)\}(?:\\label\{[^}]*\})?")

FIGENV_RE = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.S)
OVERVIEW_RE = re.compile(r"\\paragraph\*\{Overview\.\}.*?(?=\\subsection\{)",
                         re.S)

WP_LANG = [
    (re.compile(r"Work Package[~ ]9|WP9"), "the replication package"),
    (re.compile(r"[Tt]he present work package"), "The present part"),
    (re.compile(r"work[- ]package(s)?"), r"part\1"),
    (re.compile(r"research programme"), "paper"),
    (re.compile(r"Work Package[~ ]([1-8])"), r"Part S\1"),
    (re.compile(r"WP([1-8])"), r"Part S\1"),
]


REMARK_RE = re.compile(r"\\begin\{remark\}(?:\[[^\]]*\])?\s*"
                       r"(?:\\label\{([^}]*)\})?.*?\\end\{remark\}",
                       re.S)
EXAMPLE_RE = re.compile(r"\\begin\{example\}(?:\[[^\]]*\])?\s*"
                        r"(?:\\label\{([^}]*)\})?.*?\\end\{example\}",
                        re.S)

MERGED_TEXT_PATCHES = [
    ("For constant-in-time weights this is the rate verified in "
     "Section~\\ref{sec:numerical}.",
     "For constant-in-time weights this is the rate verified numerically in "
     "the validation section of the paper."),
    ("\\section{Programme interface and model}",
     "\\section{Standing assumptions and target class}"),
    ("\\subsection{Programme interface and model}",
     "\\subsection{Standing assumptions and target class}"),
]


def drop_unreferenced_remarks(body: str) -> str:
    """Remove commentary remarks inside proof parts: unlabeled remarks, and
    labeled ones whose label is never referenced within the part."""
    def repl(m):
        lbl = m.group(1)
        if lbl and re.search(r"\\(?:ref|eqref|cref|Cref)\{" + re.escape(lbl)
                             + r"\}", body):
            return m.group(0)
        return ""
    return EXAMPLE_RE.sub(repl, REMARK_RE.sub(repl, body))


# duplicates whose statement body carries no internal labels: collapse the
# body to a pointer (the full statement is in the main text).
COLLAPSE = {
    "wp2:thm:exact-id": "thm:exact-id",
    "wp3:thm:efficiency": "thm:lan",
    "wp5:thm:st-band": "thm:bands",
    "wp8:thm:gauge": "thm:gauge-main",
    "wp8:thm:not-descend": "thm:gauge-main",
    "wp8:thm:assembly": "thm:nonid-assembly",
}


def collapse_duplicates(body: str) -> str:
    for lbl, main in COLLAPSE.items():
        i = body.find("\\label{" + lbl + "}")
        if i < 0:
            continue
        for env in ("theorem", "proposition"):
            j = body.find("\\end{" + env + "}", i)
            if j >= 0:
                break
        start = i + len("\\label{" + lbl + "}")
        body = (body[:start]
                + f"\nAs stated in \\Cref{{{main}}} of the main text.\n"
                + body[j:])
    return body


def strip_for_manuscript(body: str) -> str:
    """Merged variant: remove archive meta-material and programme language."""
    body = collapse_duplicates(body)
    for old, new in MERGED_TEXT_PATCHES:
        body = body.replace(old.replace("\\\\", "\\"), new.replace("\\\\", "\\"))
    body = OVERVIEW_RE.sub("", body, count=1)
    while True:
        m = DROP_SECTIONS.search(body)
        if not m:
            break
        nxt = body.find("\\subsection{", m.end())
        body = body[:m.start()] + (body[nxt:] if nxt >= 0 else "")
    body = FIGENV_RE.sub("", body)
    body = drop_unreferenced_remarks(body)
    for pat, rep in WP_LANG:
        body = pat.sub(rep, body)
    return body


def main():
    parts_out, parts_merged, bibitems, seen = [], [], [], set()
    for wp, fname, title in PARTS:
        print(f"[{wp}] {fname}")
        text = (SRC / fname).read_text()
        pre, rest = text.split("\\begin{document}", 1)
        body = rest.split("\\end{document}")[0]

        macros = extract_macros(pre)
        body = body.replace("\\maketitle", "").replace("\\tableofcontents", "")
        body = body.replace("\\begin{abstract}",
                            "\\paragraph*{Overview.}").replace(
                            "\\end{abstract}", "")
        # capture + strip bibliography
        for bm in BIB_RE.finditer(body):
            inner = re.sub(r"\\(begin|end)\{thebibliography\}(\{[^}]*\})?",
                           "", bm.group(0))
            for im in BIBITEM_RE.finditer(inner):
                key = im.group(2)
                if key not in seen:
                    seen.add(key)
                    bibitems.append(im.group(1).rstrip())
        body = BIB_RE.sub("", body)

        for w, old, new in CITATION_PATCHES:
            if w == wp:
                if body.count(old) != 1:
                    print(f"  !! citation-patch anchor miss ({wp}): "
                          f"{old[:50]!r} count={body.count(old)}")
                else:
                    body = body.replace(old, new)
                    print(f"  cited: {old[:44]!r}")

        body = inline_closures(body, wp)
        # demote sectioning (order matters)
        body = body.replace("\\subsection", "\\subsubsection")
        body = body.replace("\\section", "\\subsection")
        body = namespace(body, wp)

        k = wp[2:]
        parts_out.append(
            f"\\clearpage\n\\section{{Part S{k}: {title} (consolidated from "
            f"{wp.upper()})}}\\label{{part:{wp}}}\n"
            f"\\begingroup\n{macros}\n{body}\n\\endgroup\n")

        mbody = demote_once_more(strip_for_manuscript(dedup_marks(body, wp)))
        parts_merged.append(
            f"\\subsection{{Part S{k}: {title}}}"
            f"\\label{{mpart:{wp}}}\n"
            f"\\begingroup\n{macros}\n{mbody}\n\\endgroup\n")

    (ROOT / "supplement_parts.tex").write_text("\n".join(parts_out))
    (ROOT / "supplement_parts_merged.tex").write_text(
        "\n".join(parts_merged))

    # merged variant of the imports part (section -> subsection)
    imp = (ROOT / "supplement_imports.tex").read_text()
    imp = imp.replace("\\clearpage\n", "").replace(
        "\\section{Imported results}\\label{part:s0}",
        "\\subsection{Part S0: Imported results}\\label{mpart:s0}")
    (ROOT / "supplement_imports_merged.tex").write_text(imp)

    extra = [
        ("HallHeyde1980", "Hall and Heyde(1980)",
         "P.~Hall and C.~C. Heyde, \\emph{Martingale Limit Theory and Its "
         "Application}, Academic Press, New York, 1980."),
        ("RudelsonVershynin2013", "Rudelson and Vershynin(2013)",
         "M.~Rudelson and R.~Vershynin, ``Hanson--Wright inequality and "
         "sub-Gaussian concentration'', \\emph{Electronic Communications in "
         "Probability} \\textbf{18} (2013), no.~82, 1--9."),
    ]
    for key, opt, entry in extra:
        if key not in seen:
            bibitems.append(f"\\bibitem[{opt}]{{{key}}}\n{entry}")
    bib = ("\\begin{thebibliography}{99}\n"
           + "\n\n".join(bibitems)
           + "\n\\end{thebibliography}\n")
    (ROOT / "supplement_bib.tex").write_text(bib)

    # ---- references_merged.bib: v2 entries + auto-converted WP bibitems ----
    v2 = (ROOT / "references_v2.bib").read_text()
    v2keys = set(re.findall(r"@\w+\{([^,]+),", v2))
    converted = []
    for item in bibitems:
        m = re.match(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}\s*(.*)",
                     item, re.S)
        if not m:
            continue
        key, text = m.group(1), " ".join(m.group(2).split())
        if key in v2keys:
            continue
        text = text.replace("{", "\\{").replace("}", "\\}") \
            if text.count("{") != text.count("}") else text
        converted.append(
            f"@misc{{{key},\n  howpublished = {{{text}}}\n}}")
    merged_bib = (v2
                  + "\n% ---- auto-converted from WP bibitems (normalise "
                  "fields at submission) ----\n"
                  + "\n\n".join(converted) + "\n")
    (ROOT / "references_merged.bib").write_text(merged_bib)
    print(f"parts: {len(parts_out)}, bibitems: {len(bibitems)}, "
          f"converted-to-bibtex: {len(converted)}")


if __name__ == "__main__":
    main()
