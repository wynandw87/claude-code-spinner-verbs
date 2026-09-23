# Contributing

New verbs and new categories are welcome. Everything lives in `README.md`, so a contribution is an edit to that one file, sent as a pull request.

Please open a pull request rather than pasting verbs into an issue. A PR puts your name on the commit and gets merged faster. If you have never opened one, GitHub's pencil icon on `README.md` forks the repo and starts the PR for you.

## Add verbs to an existing category

1. Find the category in `README.md` and add one table row per verb:

   ```markdown
   | Loaf-forming |
   ```

2. Run `python3 scripts/check_counts.py --fix`. It updates the category count, the table-of-contents entry, the totals in the intro, and the category's **Copy as list** block.

## Add a new category

1. Add a section in alphabetical order among the existing ones. The count in the heading can be `(0)`; the script corrects it. Keep `| Verb |` as the table header.

   ```markdown
   ### Cat Behavior (0)

   | Verb |
   |------|
   | Keyboard-occupying |
   | Box-assessing |
   ```

   An optional one-line description can go between the heading and the table. Leave out the **Copy as list** block; the script writes it.

2. Run `python3 scripts/check_counts.py --fix`. It corrects the counts, writes the **Copy as list** block under the table, and adds the table-of-contents entry in alphabetical order. Categories whose name ends in "Phrases" go under **Spinner Phrases**, everything else under **Spinner Verbs**. For a longer-phrase category without "Phrases" in its name, use `--fix --phrases`.

A theme that works as both short verbs and phrases gets two categories: `Cat Behavior` and `Cat Behavior Phrases`.

## What makes a good verb

- It reads naturally after "Claude is ...". Start with a verb ending in *-ing*: `Rushing the boss`, not `Boss rush`.
- Capitalise the first word only, unless a proper noun needs it.
- Aim for at least 10 entries in a new category.
- No duplicates within a category. The script reports them.
- Edit the table, never the **Copy as list** block. The script regenerates the block from the table.
- Keep it friendly. Dark humour is fine; slurs, harassment, and anything aimed at a real private person are not.
- Verbs from films, shows, and games are fine as short references. Do not paste long quotations.

## Before you open the PR

Run the check without `--fix` and make sure it prints `OK`:

```
python3 scripts/check_counts.py
```

The same check runs on every pull request. It needs Python 3 and nothing else.

## Other contributions

Fixes to the setup instructions, typo corrections, and improvements to the script are welcome too. Issues labelled [`good first issue`](https://github.com/wynandw87/claude-code-spinner-verbs/labels/good%20first%20issue) are a good place to start.
