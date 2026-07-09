# Publishing this repository to GitHub

The repository content lives in this folder; the git history is delivered
as `../operator-interventions-spdes.bundle` (a fully verified single-commit
bundle) because this folder was assembled on a filesystem that git cannot
lock. If a `.git_disabled/` directory is present here, delete or ignore it.

## Recommended: clone the bundle, then push

```bash
cd github_repo
git clone operator-interventions-spdes.bundle oisp-git
cd oisp-git
# Option A - GitHub CLI
gh auth login
gh repo create operator-interventions-spdes --public \
  --source=. --remote=origin --push \
  --description "Causal-statistical theory for operator interventions in linear SPDEs: paper + seeded replication package"
# Option B - plain git: create an empty repo on github.com first, then
git remote add origin git@github.com:<YOUR-USER>/operator-interventions-spdes.git
git push -u origin main
```

## Alternative: fresh init from the browsable tree

```bash
cd github_repo/operator-interventions-spdes
rm -rf .git_disabled
git init -b main && git add -A && git commit -m "initial import"
# then create the remote and push as above
```

## After publishing
1. Enable Actions (CI runs the tests and builds the paper on every push).
2. Cut a release (v1.0-wp) and archive on Zenodo to mint a DOI; add it to
   CITATION.cff and the paper's Data availability paragraph.
3. Add the arXiv link once posted.
