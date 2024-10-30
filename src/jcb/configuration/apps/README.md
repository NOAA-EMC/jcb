
# Application client directory

This directory represents the default location for the jcb application clients. If users run `jcb/jcb_init.py` the repos for the registered clients will be cloned to this directory and this will enable `jcb` to be tested with the clients.

Clients have to be registered with jcb in a few steps:

- Update `jcb/jcb_apps.yaml` at the top level of the repo to provide the Git address and the default 'ref', which could be branch, tag or commit hash. The new entry should look something like the following:

```yaml
<app>:
  git_url: <org>/<repo>  # Do not append with .git
  git_ref: develop       # Branch, tag or hash
```

- Update `jcb/.gitignore` with `src/jcb/configuration/apps/<app>/`, where `<app>` is the dictionary key used in `jcb_apps.yaml`.
- Add testing files like `<repo>/test/client_integration/<app>-<component>-templates.yaml`. These are the tests that will be run against changes to `jcb`. The more that users can provide here the better, since this protects the client against future changes to `jcb`.

A client can be registered with `jcb` using `develop` as the default ref. Of course this poses risks for `jcb` because the client could move ahead of the core repo and cause tests to begin failing. However there is a benefit to the client to keep all the testing running against recent versions of the code without the headache of updating hashes in `jcb/jcb_apps.yaml`. Some cooperation is requested as a precursor for using `develop` as the default branch.

- Add a run of the `jcb` client integration tests in the client. An example of this kind of test is shown here: https://github.com/NOAA-EMC/jcb-gdas/blob/develop/.github/workflows/run_jcb_basic_testing.yaml. That test can be copied verbatim to the other client repos since the script nowhere references the name of the client.
- Add branch protection in the client to prevent merging of anything to `develop` that does not satisfy the client testing of `jcb`.

Note that from time-to-time there will the need to sync merges between `jcb` and all the clients and nothing in the above should prevent this. The extra testing added to the client checks for matching branch names.

If a client becomes responsible for repeated test failures `jcb/jcb_apps.yaml` will be changed to use a recent hash.

**_NOTE:_**
It would clearly simplify the above if clients were added to `jcb` as submodules. However, Git submodules are not permitted. While Git submodules are quite a powerful utility they are not always appropriate, especially when users might want more control of what is cloned and where. This is especially true as code gets closer to operations and operational workflows, and `jcb` is tightly integrated with these kinds of systems.

