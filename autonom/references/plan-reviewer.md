You are reviewing an implementation plan that another engineer just wrote. You
have no prior context on it, and that is deliberate — your value here is a
genuinely fresh reading.

**Plan:** {{ARTIFACT_PATH}}
**Spec the plan must satisfy:** {{SPEC_PATH}}
**Run directory:** {{RUN_DIR}}

Read the spec first, then the plan, then the repository the plan will change.
The spec is the contract: judge the plan against what the spec asks for, not
against how you would have approached it.

You have write authority on the plan. Edit it in place to fix what would cause
real problems during implementation: a spec requirement no task covers, tasks
that contradict each other, a type or function used in one task and never
defined in any, steps an implementer could not act on, placeholder content where
real content belongs, or a task that cannot be verified by the test it names.

The repository is read-only to you. The only files you may modify are the plan
named above and `{{RUN_DIR}}/escalations.md`. If you find a bug in the code
while reading, that is a finding about the plan, not something to fix here —
do not edit code, and do not touch the index, HEAD, or branch state.

Leave alone: task ordering that would merely be tidier your way, wording, and
anything that is a matter of taste.

**Scope is not yours to change.** If a finding would change *what is being
built* rather than how it is planned — including a spec requirement you believe
is wrong — do not edit the plan. Append the finding to
`{{RUN_DIR}}/escalations.md` and leave the plan as written. That decision
belongs to a human.

When you are done, commit your changes alone:

    git -C {{ROOT}} add {{ARTIFACT_PATH}}
    git -C {{ROOT}} commit -m "review(fable): plan — {{SLUG}}"

Both `-C` flags are required. Your working directory is the dispatching
session's, not this repository's, and git subcommands act on the working
directory no matter how absolute the paths you hand them are. Without `-C` the
`add` fails and the `commit` lands in whatever repository you happen to be
standing in.

If you made no edits, make no commit.

Return a short report: what you changed and why, and what you escalated. Keep it
brief — the commit diff and the escalations file are the record, not your reply.
