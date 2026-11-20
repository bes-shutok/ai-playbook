# Backlog: plan-delta classifier gap at the review-fold terminal fold (unclassified content fold)

Observed: 2026-11-12, session sess_2b51c910-597e-4972-9924-7f5eb673bd0f, the review-fold-output-prevalidation authoring lane at its cap-closure terminal fold.

- Refusal: `scripts/plan_delta_classifier.py --plan docs/history/plans/2026-11-10-review-fold-output-prevalidation.md --since 493acefa6eb92efe963f554d61a893449bf1c1be` refuses with hunks not exempt (OUTCOME: fail); the terminal fold rewrites the plan's own prescribed texts per the r5 review round's accepted findings, so every changed hunk is content-bearing and outside the exempt classes.
- Why the workflow would have stopped without a workaround: the lane is at the plans Plan Quality Gate total-round cap (5 of 5), so the re-review default (a fresh round) has no round to launch; rule 6's cap-closure terminal shape exits on the post-correction digest when the delta is carried by a verified corrections chain.
- Evidence-backed cause: the classifier's vocabulary is binary (exempt classes or unclassified) and this fold's hunks are content edits by construction: 16 refused hunks, before digest `b8ba5ff8774ebc98132fea185f8aaf39b6414c905401bd7c06a350e3158ba118`, after digest `b46e19c634976e3ab3fa2d154ff3e219f5ea340011f8d3827ba6993eaba7ea3b`.
- Smallest proposed correction (carried): the operator-acked plan-family route the same rules define - the classifier CLI records this row with the authoring session's `author_session_id`, a distinct interactive session appends the matching `correction_authorizations` entry into the primary checkout's scheduler state on the recorded explicit operator direction, and the verified chain (exact row digest, distinct writer session, fixed-selector receipt, seal, linkage legs) bypasses only the classification leg.
- **Cluster:** docs/history/plans/completed/2026-11-13-corrections-writer-distinct-session-dispatch-gap.md (covered twin; the row landed through that plan: the plan minted the distinct-writer spawn route, this row owns the classifier vocabulary gap that forced the route)

Refused hunk digests (quoted for the receipt's gap-row leg):

- `2fe3fc65140c7ebf82b45d9b45528f41a2119de6309b0a4a8875c2040dfe5831` (@@ -13,1 +13,1 @@)
- `40662f5270374c253d06fd75172e732a79ce9870b3e1860a587536cd7f6a96bd` (@@ -41,1 +41,1 @@)
- `f8ea5f4a27e319c3c4ba84aaf6e26a226906f020b7beca875ad02a2579e52c39` (@@ -44,1 +44,1 @@)
- `73cf1d96c0ace2b8b75ce4bf3cd301a7c77001ab64c587fa90e2e0ec7deea4bf` (@@ -50,1 +50,1 @@)
- `07e6caab1fd353f22f6d74fdb7cb6abb1cf4fcae3b42ce483f3b52002a263898` (@@ -61,1 +61,1 @@)
- `32c2a514650367977a62dac3bcf703466f582b1394e6fcf19457b2a60c060e45` (@@ -109,1 +109,1 @@)
- `3e61d525dd204a9e1e71a94c294ed0d165ccc0c6fb4827fb999535a6c4e06a95` (@@ -112,3 +112,3 @@)
- `70ab10a044192087026880cd40a1aadccc1d7499c355c5ec379018ee630531e3` (@@ -126,1 +126,1 @@)
- `1e5d23f7e54cfed0ec3d4f232f3fa9dfc77b7bb3a9cdca8b15971b816118ef22` (@@ -128,2 +128,2 @@)
- `7e4f5ff48e1df4ea03f99ae63bec3ea82783d72a6df8a5288f81fc4e5bda739f` (@@ -135,1 +135,1 @@)
- `d57730600b43bad2fd3d81d3bb90e07b2e53ed9481c8876007c771273f2a1e0b` (@@ -142,1 +142,1 @@)
- `eb1dedd889d534141d745b8dab49cccb00397242d57c97e0a1df7c790e52db05` (@@ -154,1 +154,1 @@)
- `2e84e9d66421518f804cd68733bfe7579a8275f6193c73f9f8bb8bc05a7acd11` (@@ -156,3 +156,3 @@)
- `84547c54549b74efaf25cfe34c942ec6afa135552210aff00e240dab717bdcda` (@@ -160,1 +160,1 @@)
- `562f6ad0f0f4e8d28d7eefbd3b157bc49d6b9b17cb2918610ff7d8a3b7cfd87a` (@@ -163,1 +163,1 @@)
- `ad189cb6b5879b4e9cd0d96aa433338827e6fd89d9ecb2099ac159c596be2ee6` (@@ -167,2 +167,2 @@)

Directive of record: use self-heal to complete
