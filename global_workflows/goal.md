# /goal — bounded execution

Parse only a leading `/goal`, `Goal `, or `Goal:` token.

Record the objective, Goal identity, authorization source, allowed paths,
and auto-checkpoint semantics in the Goal ledger.

Before dispatch, estimate projected context usage and report the context line.
If projected usage reaches 60%, split the Goal or checkpoint before execution.

Dispatch only tasks whose paths stay inside `allowedPaths`.
Require a `goal-task-v1` receipt from every dispatched task.
If native Goal capability is absent, execute one bounded task locally.
Never persist approval tokens, secrets, or Goal authority beyond this scope.
