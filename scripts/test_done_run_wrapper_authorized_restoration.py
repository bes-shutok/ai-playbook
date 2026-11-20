"""Bounded discovery entrypoint for authorized-restoration wrapper tests."""
from test_done_run_wrapper import _load_wrapper_test_shard


def load_tests(loader, standard_tests, pattern):
    return _load_wrapper_test_shard(loader, "DoneRunAuthorizedRestorationTest")
