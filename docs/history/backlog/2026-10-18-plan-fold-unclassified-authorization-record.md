# Backlog: preserve authorization and hunk evidence for unclassified plan folds

- **Filed:** 2026-10-18, while folding the first review of `worktree-closeout-single-start-baseline`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** process evidence gap
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `agents/skills/plans/SKILL.md`, Plan Quality Gate rule 2
- **Cluster:** docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md; docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md
- **Dedup probe:** compared the two clustered classifier rows; this row records the required authorization for a semantic plan fold and its fresh-review route, while the clustered rows concern mechanical edit classification and post-certification correction verification.

## Problem

The plan-fold rule requires operator authorization and a classifier-gap backlog row before an unclassified fold proceeds. This semantic fold correctly falls outside the classifier's format-only exempt classes, but the durable record should preserve why the fold was authorized and which reviewed bytes it changed.

## Expected

Keep the operator direction, before/after plan digests, classifier hunk digests, and fresh-review requirement together so the authorization can be audited without treating a semantic plan change as mechanically exempt. This row records this witnessed instance; it requests no classifier exemption or new blocking machinery.

## Evidence

The operator directed this session: “DOn't ask me in such cases, instead  reflect on issues and fixes, are they converging? Then take your own decision and move on with this and following plans”. The plan-delta classifier compared `docs/history/plans/2026-10-18-worktree-closeout-single-start-baseline.md` from `f29b52ec6` with the folded plan and returned 22 unclassified hunks. A fresh focused review on the folded digest is required.

Before digest: `12cef0abc5f33a682559dd495a961e269e356cd4784a41e2f2b13ec0e0f1a66a`
After digest: `91a92c31df7c35ba154947c730316f1c9cdad395390969b1ab0ecea395e1d8a1`

Classifier hunk digests:

- `e5accff89ca02df2363a6055840c6d8ae26d38569a31a7af74b0cd1ed68a3615`
- `cf20bbd4e559b4468f9672a915d723780141c6b8ccd349004b4cfef31c4204b5`
- `f772cc97d6f401ac362707b3a7eb5b49be4ece05f60c52b81442e32bbe3e2ff8`
- `399e24a927882c84a3a7536ed23faaf09478f6e505414a83addf7dd791200e71`
- `77a38f82fb36711277c4b5264b697c07ca47ee93c92aa8ebc12ccda05f5f8f9a`
- `458b06463dcd8114d25673c792dd1a303a2f179c738c5bd240cd2cdbac237e7f`
- `b599b50147daf592eac6f041d212f74f6a38e7061aa9e724b4c84946ac79428d`
- `4c43f30bf943779cfc9eccd58097a745d5441005d10055fe8311e9dbda9a2a8f`
- `54a556110b3d577c51f0853dc23c51f3f17287fa3585d69b30185db049a4d13b`
- `d03291f66616b27586359c32300b3f49990e2a8e8307695fa902c1cfd79fc1ec`
- `307168076753db6ebe8b2b797e1aa120f9aa5d0672663381f6503cce4ee0709b`
- `98036e928ee0d474084eee806e74876b5f3004e64289e63c400da1214f7bd2c7`
- `60bc743a25e5a6bc3cc0180b4e9fa908261fc9f060911a785647d647daede17a`
- `88faba124f7c031bf38791fa0548f0a20f2256e8fc6ee8ec7a92061e68c5915e`
- `5c97b8cfc522683833f2e002c0f89046d925fdbce115523f239ea39215d71ffa`
- `c92412bba835d1d6bce3ec52562da8748f9429673c081b6bd2a05d35d0d759cf`
- `17653f04dc5a5efdd55891cbf3df766e1d8a402dfb918fb958e60a32bda5760d`
- `6ef5746073acfd11facd768974bccb3492d305fa2e0ea26cf3165283858d0083`
- `2fd1d4448286c5f1d9eca30310c77d2333bdb52b0467afc297cd7835772d8eb5`
- `98167d41fbf30f31e4d5a7662b0b7bfd7209304b9e426a6d5ac85e7ed350a89f`
- `d9c6c01b5043f06b13e08fb3ad44b7cca2f7b6b02f077f6c81f9c02b79848960`

## Source

- Classifier output from the recorded plan fold; no test or implementation behavior is claimed.

## Second fold evidence

The r2 review exposed an inventory ownership ambiguity, missing exclusion assertions, missing zero-plan coverage, and an absent worktree-retention assertion. The plan was tightened and must receive a fresh focused review on its post-fold digest.

Before digest: `91a92c31df7c35ba154947c730316f1c9cdad395390969b1ab0ecea395e1d8a1`
After digest: `4dc9cbc5103453158ac5ece12da620b3e2abd93a79809d16e4eb037cc57d1bc5`

Classifier hunk digests:

- `5beb63c14be92eeba6fcaf2335a14a0ea8f2e4ffd3920bd04541cdb6556432c8`
- `1ea916b8de422f60f316c5d19dbe2b4e287ba2fe44f76dfc8b6d92c8e2fca6b1`
- `c7349e567a0e6572186265d39e0b85e7add22341e6719abc2287949630734a2b`
- `c37d7bf86f8081b959adda7aa75116151302667f3b63bc6854a115036cbc08e0`

The operator direction is recorded in `docs/tmp/done-session/plan-fold-r2-operator-direction.record`; the CLI-produced operator-acked row is in `docs/tmp/done-session/plan-fold-classifier-output-r2.txt`. The ack authorizes the fresh review route and does not classify the semantic change as exempt.

Classifier refusal evidence hunk: `b32bbbdd5d3b026db035d715b775b0074d35b5fadae5e710310f756d8756b256`

Classifier refusal evidence hunks:

- `eb95beaf82b6f97cc825691c311322c4829487922140b9941c77e6a621ee108d`
- `1564abf27882bac5eb85e6a37ea13ab29cfa5a23a63c7fb2e24da0e2a5ed1e89`
- `91c3873a631288572b836bb4c1510a5b2dfe5f7ee8e748f1146ba7eb9cf8ff46`
- `af545ea9eab427c531657f3dfe3f9671b6248576e87ee1fd9f88c2fac88470bf`

## Third fold evidence

The r3 panel converged on the scoped-copy ownership boundary: include explicitly owned reviews and sidecars, centralize allowlist derivation and validation in the migration owner, test all approved inputs and each refusal class, and keep the existing manifest schema while tests compare source and destination digests. The operator direction authorizes the semantic fold and fresh review.

Before digest: `4dc9cbc5103453158ac5ece12da620b3e2abd93a79809d16e4eb037cc57d1bc5`

After digest: `b18ab38a7d3693ba862d2eed30c055f6fe23aaaa59f48a44f7902280e0a25b72`

Classifier hunk digests:

- `b32bbbdd5d3b026db035d715b775b0074d35b5fadae5e710310f756d8756b256`
- `b543aa16e95c4e664824a419bab9d80c08d5cbcceefce0ad91b0637dcf9dd206`
- `1564abf27882bac5eb85e6a37ea13ab29cfa5a23a63c7fb2e24da0e2a5ed1e89`
- `91c3873a631288572b836bb4c1510a5b2dfe5f7ee8e748f1146ba7eb9cf8ff46`
- `af545ea9eab427c531657f3dfe3f9671b6248576e87ee1fd9f88c2fac88470bf`

CLI-produced operator-acked row:

```json
{
  "after_digest": "b18ab38a7d3693ba862d2eed30c055f6fe23aaaa59f48a44f7902280e0a25b72",
  "before_digest": "4dc9cbc5103453158ac5ece12da620b3e2abd93a79809d16e4eb037cc57d1bc5",
  "evidence_commit": "5129532a129dfd2fef6328b74cc8fdb00bd51723",
  "hunks": [
    {
      "digest": "b32bbbdd5d3b026db035d715b775b0074d35b5fadae5e710310f756d8756b256",
      "header": "@@ -19,1 +19,1 @@"
    },
    {
      "digest": "b543aa16e95c4e664824a419bab9d80c08d5cbcceefce0ad91b0637dcf9dd206",
      "header": "@@ -69,2 +69,3 @@"
    },
    {
      "digest": "1564abf27882bac5eb85e6a37ea13ab29cfa5a23a63c7fb2e24da0e2a5ed1e89",
      "header": "@@ -72,1 +73,1 @@"
    },
    {
      "digest": "91c3873a631288572b836bb4c1510a5b2dfe5f7ee8e748f1146ba7eb9cf8ff46",
      "header": "@@ -74,2 +75,2 @@"
    },
    {
      "digest": "af545ea9eab427c531657f3dfe3f9671b6248576e87ee1fd9f88c2fac88470bf",
      "header": "@@ -92,1 +93,1 @@"
    }
  ],
  "kind": "operator-acked",
  "receipt": {
    "authorization_witness": "docs/tmp/done-session/plan-fold-r3-operator-direction.record",
    "classifier_gap_row": "docs/history/backlog/2026-10-18-plan-fold-unclassified-authorization-record.md",
    "directive": "DOn't ask me in such cases, instead  reflect on issues and fixes, are they converging? Then take your own decision and move on with this and following plans"
  },
  "recorded_at": "2026-10-18T22:19:06Z",
  "recorded_by": "plan_delta_classifier"
}
```

The receipt resolves against the operator-direction record. This row preserves the witnessed authorization and does not classify the semantic fold as exempt.

R3 follow-up classifier refusal evidence:

- `f999415aab18f40975113b0f9d6786b5c3e5115390565909fd4a8068ff20e3cc`
- `c25a806f62370586e9ad4ddf25b4c048454753e09bb6e3fa325c4694a3c946f1`
- `1c0947b41353c38eccbd0a2fff9be5a4a11d85f0ae66fd3a5803fdf857914714`

## Fourth fold evidence

The r3 panel converged on the allowlist contract: plan paths select related artifacts but are not candidates; include current-plan execution session and metrics artifacts; filter shared deliverables by current ownership; and route invalid inventories through the existing migration refusal.

Before digest: `b18ab38a7d3693ba862d2eed30c055f6fe23aaaa59f48a44f7902280e0a25b72`

After digest: `06b8a042081a7575acd71a53f1eded2354814c9397e30cc5fceb89931e877b7a`

Classifier hunk digests:

- `f999415aab18f40975113b0f9d6786b5c3e5115390565909fd4a8068ff20e3cc`
- `c25a806f62370586e9ad4ddf25b4c048454753e09bb6e3fa325c4694a3c946f1`
- `1c0947b41353c38eccbd0a2fff9be5a4a11d85f0ae66fd3a5803fdf857914714`

CLI-produced operator-acked row:

```json
{
  "after_digest": "06b8a042081a7575acd71a53f1eded2354814c9397e30cc5fceb89931e877b7a",
  "before_digest": "b18ab38a7d3693ba862d2eed30c055f6fe23aaaa59f48a44f7902280e0a25b72",
  "evidence_commit": "b5936bee9e7b7ba9107471e641cee2e4cf59c829",
  "hunks": [
    {
      "digest": "f999415aab18f40975113b0f9d6786b5c3e5115390565909fd4a8068ff20e3cc",
      "header": "@@ -19,1 +19,1 @@"
    },
    {
      "digest": "c25a806f62370586e9ad4ddf25b4c048454753e09bb6e3fa325c4694a3c946f1",
      "header": "@@ -44,1 +44,1 @@"
    },
    {
      "digest": "1c0947b41353c38eccbd0a2fff9be5a4a11d85f0ae66fd3a5803fdf857914714",
      "header": "@@ -70,6 +70,10 @@"
    }
  ],
  "kind": "operator-acked",
  "receipt": {
    "authorization_witness": "docs/tmp/done-session/plan-fold-r3-followup-operator-direction.record",
    "classifier_gap_row": "docs/history/backlog/2026-10-18-plan-fold-unclassified-authorization-record.md",
    "directive": "DOn't ask me in such cases, instead  reflect on issues and fixes, are they converging? Then take your own decision and move on with this and following plans"
  },
  "recorded_at": "2026-10-18T22:25:55Z",
  "recorded_by": "plan_delta_classifier"
}
```

The receipt resolves against the operator-direction record. This row preserves the witnessed authorization and does not classify the semantic fold as exempt.

## Fifth fold evidence

The r4 findings converge on two independent changes: complete the run inventory with the plan-owned certification seal and authoring telemetry, and keep the newly introduced inventory diagnostics warning-only because no scoped-inventory refusal currently exists. The skip-record path root is now explicit. The operator direction authorizes this semantic fold and a fresh full review.

Before digest: `06b8a042081a7575acd71a53f1eded2354814c9397e30cc5fceb89931e877b7a`

After digest: `34c4dcc1f1f32c50df203adc7b99865750df29f2cd69556e23081b29cc483b0d`

Classifier hunk digests:

- `992b50cdfd08852ebc6254ed0e766c4694803253f1d03a18a87b952f8f74acaf`
- `4afd88cd4925992a289f4ef55a000951da94e3bfcee57a7acc32d0eb67536732`
- `3fbb1f02263de7671ecf21af4cae484c5c2623b3edafaf544a32526e903b1f0c`
- `43b8503d80383184865a17ba98cf02c25334681c509d5eee8afe2b711749db55`
- `f2f3ba83b59c9d25657cd030dd2477e02ff13a1f0a9218d0d36620473c5ff413`
- `c8ed7afa8b3b1652c34bdeea18d7abd0b7cee227692e01de0ef729c058aab8d5`
- `c3fa62d61db3218d7edc54a15ffaf705b7e44e2ab044acad4401731fccf41067`
- `2ff013d0278e3c57332ee780d9a5d2afffbbf50dacb842e144d224d320e4237e`
- `13b99bbd02c6b0122a645c1018d566ae620062728e8dd02985593dd0374d1663`
- `d731c77c36cd5b52398a57c6a55799e1e670c83a97bda7af9c4e2089be0e5a0c`

The CLI-produced operator-acked row is recorded in `docs/tmp/done-session/plan-fold-classifier-output-r4.txt`; the operator direction witness is `docs/tmp/done-session/plan-fold-r4-operator-direction.record`. The authorization is for fresh review and does not make the semantic plan edits exempt.

## Sixth fold evidence

The r5 panel independently converged that warning-only omissions can lose run-owned artifacts at teardown. The plan now reuses the existing manual scoped-copy procedure for skip records, requires its complete artifact inventory and per-file digest verification before removal, and keeps baseline migration on the existing helper. This resolves the retention gap without adding executable inventory validation or a refusal condition. The operator direction authorizes the semantic fold and fresh review.

Before digest: `34c4dcc1f1f32c50df203adc7b99865750df29f2cd69556e23081b29cc483b0d`

After digest: `0c2fb2e2e1efc64f5f3a7efd90b88919fd00ffad00cf39cc2b21bf9e1023b9a2`

Classifier hunk digests:

- `0b4a18bf4151c47d7d9ce4b0b98af4a058f8cdda202a2f808d4428152b36f166`
- `3e909d2820eef309123ac476155f9c0b2e696e9a88fa7d70d992ddb0cbc596c8`
- `4cc0374e2d1cff30b6230e8b40ce4377f739122996c9119a8e5c46041349b542`
- `06bd9dae6f9c3dd295b19f9a0f4f1b7b97a2f0b12ff1c4776339d1a4db58b3b6`
- `c3d6923e6efe1065fcf52682728eb2d9557ee48edfd5d05949dcaa6743fdfc79`
- `6d831854aaa6277dded36a6b6dcc6d07b88e3aec2afc87a7f001144febca36c7`
- `cbf890e02d6073170ee3e1ec0a6e215ee21d11ff94ce8009a17e9ed3ba95d667`
- `45b6f016c60120eb8a0e12bdbe4fb1b40ce74379241c247bd0749f0e739b3b50`
- `be5080b4c7118784209e270375e165fffc37ac1860cada97dae94202960a0b6b`
- `265558c3408dceba120372cbb010505bedf5e473657de9e41a71f2fa85e73193`
- `9f069fedb3beebb044e9b4ce68ad83bddab77eb4f6a9da1cbe2508211aa20128`
- `8bcf855bb979acbda4aa49a943f6b4de18b61a251fd9d43bd773168cf3858215`
- `836cfe67ead35fb7a1000fa75b230625dd39dcb190f8cbc49ef855031a8fe84d`

The CLI-produced operator-acked row is recorded in `docs/tmp/done-session/plan-fold-classifier-output-r5.txt`; the direction witness is `docs/tmp/done-session/plan-fold-r5-operator-direction.record`. This authorization is for fresh review and does not classify the semantic edits as exempt.

## Seventh fold evidence

The r6 panel found two related contract gaps: the valid-skip wrapper branch was not explicit, and the manual-copy acceptance lacked a mismatch/source-retention witness. The plan now orders complete manual transfer before `done_run.sh commit`, bypasses baseline migration only for a valid skip record, retains the missing-evidence refusal, and records the cap-round dispositions. The operator direction authorizes this fold and cap closure without another review round.

Before digest: `0c2fb2e2e1efc64f5f3a7efd90b88919fd00ffad00cf39cc2b21bf9e1023b9a2`

After digest: `d5176d525c8da8d94898be7308bd0084c7f47d5af77fee8e21a6bc279268c9b1`

Classifier hunk digests:

- `aa7e0720a8a9d421f45ff6477941fa4a61e832757475cb9291e5d26d2ed4c4b1`
- `a968b907a50ebba85486593295e494ed8c8b05d5f81df52c6689177c565bcaae`
- `c2b73370b16e10e656fe35a13fd1fe0b63e148167c046d90416a61b1b07b8e46`
- `cff17c76eeb117b2493e8f585a51babf291e65aa4b41d3ed64854421206929b2`

The CLI-produced operator-acked row is recorded in `docs/tmp/done-session/plan-fold-classifier-output-r6.txt`; the direction witness is `docs/tmp/done-session/plan-fold-r6-operator-direction.record`. The authorization is for cap closure and does not classify the plan edits as exempt.
