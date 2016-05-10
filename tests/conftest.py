# -*- coding: utf-8 -*-

import pytest

@pytest.fixture(scope='session')
def tmpdir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('data')
    return tmpdir
