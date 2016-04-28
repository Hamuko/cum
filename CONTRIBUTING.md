Asking Questions
================

If you have questions regarding how to use the software, please ask them on IRC.

The channel #cu can be found on irc.rizon.net.

Contributing Patches
====================

Code Style
----------

The coding style is based on the [Pocoo Style Guide](http://www.pocoo.org/internal/styleguide/)
with a 79 character limit.

Imports and symbol definitions (such as functions, or class methods) should be
listed in alphabetical order.

Currently, cum supports Python versions >= 3.3. Please do not break backwards
compatibility with older Python versions unless you have a good reason to.

Tests
-----

Before submitting a pull request, please run the unit tests to confirm that you
didn't break anything by accident. The following environment variables are read
by the unit tests for login data:

    MADOKAMI_USERNAME
    MADOKAMI_PASSWORD
    BATOTO_USERNAME
    BATOTO_PASSWORD

If you are lazy and have [jq](https://stedolan.github.io/jq/) installed,
`source` [this script](https://gist.github.com/CounterPillow/9e6ea93bd0e9b94b8de84326db46fee4)
before running tests to have the environment variables set to what you use in
your cum config.

When adding new code paths, please also add tests to cover them.

Code Reviews
------------

Your submitted patches are most likely going to undergo a review. This is to
ensure that trend in code quality is one that goes upwards, rather than the
opposite.

Please address concerns raised by the reviewer, and try to answer questions
regarding design decisions to the best of your ability.

Don't worry, the reviewer likely doesn't hate you as a person, they just hate
your code! Please do not engage in personally motivated arguments over design
decisions; keep the discussion as technical as possible.

Commit Messages
---------------

The first line in a commit message should be a summary of the changes, in 65
characters or less. The summary line should be written in imperative mode, as in
"Fix" instead of "Fixed".

This should be followed by a blank line, and then a 72 character wrapped
explanation of the changes a commit makes.

If you submit a pull request, please make your changes in a new branch, and not
the master branch. This makes it easier to re-base your changes and allows you
to work on several improvements at once all based on a "clean" master.

Upon submitting a pull-request, you may be asked to make additional fixes before
the pull-request is merged. In this case, please squash simple commits together;
re-writing the commit history of your remote branch is a necessary evil when it
comes to keeping a clean commit history. To squash your commits, do the
following steps:

1. Execute `git rebase -i HEAD~$NUMBER_OF_COMMITS`, e.g. `git rebase -i HEAD~2`.

2. An editor should open. Replace `pick` with `squash` or `s` on the commits
that you want to have squashed.

3. Proceed and adjust your commit messages as needed.

4. Do a force-push to your remote branch with `git push -f yourremote
yourbranch`.

Independent changes should be submitted as independent commits, and if
necessary, independent pull requests.
