# Tutorial: an example project, phase by phase

This tutorial follows one small example project, **`shortlink`** (a tiny URL
shortener library in Python), through two changes:

1. **`add-short-links`**: a new behaviour, through every phase, including
   failing checks, a review finding and a second build cycle.
2. **`add-link-expiry`**: a change to a capability that already has a living
   spec (`MODIFIED` requirements).

Every page has the same parts: what the skill is for, its steps with the
command each step runs, the **real output** of those commands, the artifacts
written, and boxes like this one:

```{admonition} How the output feeds the skill
:class: tip feeds

What the skill reads in the output, and what it decides from it.
```

```{note}
All command output is real: it was captured by running specworks on the
project. Only the absolute workspace path is shortened to `/work/shortlink`.
The finished project, with its living docs and archived changes, is in the
repository at
[`docs/example/shortlink/`](https://github.com/lcmonteiro/specworks/tree/main/docs/example/shortlink).
In practice you type `/specworks-specify`, `/specworks-design`, … and the agent
runs these commands; they are shown so you can see what each step checks.
```

```{toctree}
:maxdepth: 1
:caption: Change 1, add-short-links

setup
refine
specify
design
test
code
review
build-cycle
validate
close
```

```{toctree}
:maxdepth: 1
:caption: Change 2, add-link-expiry

modify
```

```{toctree}
:maxdepth: 1
:caption: More

lifecycle
```
