Status: covered (docs/history/plans/completed/2026-10-18-review-runtime-sibling-module-deployment.md)

Priority: high

Class: fix-class

Origin class: consumer-feedback (company)

Driving force: maintainability

# Review runtime deployment omits a required sibling module

## Observed versus expected

Observed: invoking the deployed review staging validator fails during import because `review_plan_identity.py`, a sibling module imported by `validate_review_staging.py`, is absent from the deployed script directory. The same dependency failure also prevents `review_record_selection.py` from starting. The current workaround is to add the source scripts directory to `PYTHONPATH` when invoking the deployed helper.

Expected: runtime deployment installs the validator and every required sibling module together, or packages the scripts so their import dependencies resolve without a consumer-specific environment workaround.

## Reproduction

Run the deployed `validate_review_staging.py --preflight <record>` in a consumer repository where the source scripts directory is not on `PYTHONPATH`. Import fails with `ModuleNotFoundError` for `review_plan_identity` before record validation begins. Setting `PYTHONPATH` to the playbook source `scripts/` directory allows the same command to proceed.

## Environment

Consumer feedback from a company project, 2026-10-18. The runtime validator and selector were deployed without their imported sibling module.

## Suspected root area

The runtime-helper deployment roster or packaging boundary does not capture Python sibling-module dependencies for review staging tools. Make the deployment unit include the import closure and add a deployment verification that imports or runs each deployed entrypoint without source-tree `PYTHONPATH` help.

## Why not fixed now

The current review and contract-test change does not own shared runtime deployment. The workaround let the focused staging validator complete, so the toolchain defect is recorded for a separate fix.
