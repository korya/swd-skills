# source me. run <label> <cmd...>: runs cmd from the repo root, prints stdout, stderr, exit code.
O=/Users/dmitri/dev/swd-skills/evals/e2e-test/workspace/iteration-1/eval-1-cli-branch-with-spec-violations/with_skill/run-1/outputs
L=$O/tickets.jsonl
cd $O/repo
run() { local label=$1; shift; echo "== $label"; echo "\$ $*"; "$@" >| $O/.so 2>| $O/.se; local rc=$?; echo "exit=$rc"; echo "stdout: [$(cat $O/.so)]"; echo "stderr: [$(cat $O/.se)]"; }
