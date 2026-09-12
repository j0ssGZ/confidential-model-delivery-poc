"""Deployment isolation and source selection for signed Kubernetes checks."""

import runpy
from pathlib import Path

import pytest

MODULE = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/layer2_jobs.py'))


@pytest.mark.parametrize('case', ['positive', 'tampered-bundle', 'tampered-signature', 'wrong-public', 'wrong-aes'])
def test_hub_job_requires_signature_and_preserves_isolation(case):
    job = MODULE['render'](case, 'a' * 40, None, 'repo')
    assert job['metadata']['namespace'] == 'secure-ai-layer2'
    pod = job['spec']['template']['spec']
    assert pod['automountServiceAccountToken'] is False
    assert pod['serviceAccountName'] == 'signed-consumer'
    assert not any('hostPath' in volume for volume in pod['volumes'])
    container = pod['containers'][0]
    assert container['image'] == 'cmdp-consumer:layer2'
    assert container['securityContext']['readOnlyRootFilesystem'] is True
    assert container['resources']['limits']['memory'] == '2Gi'
    compile(container['command'][2], '<job>', 'exec')


def test_fixture_mount_is_explicit_readonly():
    job = MODULE['render']('positive', None, '/tmp/cmdp-layer2-fixtures', 'repo')
    pod = job['spec']['template']['spec']
    assert pod['volumes'][-1]['hostPath']['path'] == '/tmp/cmdp-layer2-fixtures'
    assert pod['containers'][0]['volumeMounts'][-1]['readOnly'] is True


@pytest.mark.parametrize('revision,fixture', [(None, None), ('main', None), ('a'*40, '/tmp/test'), (None, '/'), (None, 'relative')])
def test_bad_source_rejected(revision, fixture):
    with pytest.raises(ValueError):
        MODULE['render']('positive', revision, fixture, 'repo')
