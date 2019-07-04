from pycarol.pipeline.tools import *
from pycarol.pipeline.tools.pipeline_example import T1,T2,T3


def test_create_pipe():
    params = {}
    pipe = Pipe([T3],params)
    assert pipe.dag

def test_run_pipe():
    params = {}
    pipe = Pipe([T3],params)
    pipe.remove_all()
    pipe.run()
    assert T1(**params).output().exists()
    assert T2(**params).output().exists()
    assert T3(**params).output().exists()

def test_remove_all():
    params = {}
    pipe = Pipe([T3],params)
    pipe.remove_all()
    pipe.run()
    assert T1(**params).output().exists()
    assert T2(**params).output().exists()
    assert T3(**params).output().exists()
    pipe.remove_all()
    assert not T1(**params).output().exists()
    assert not T2(**params).output().exists()
    assert not T3(**params).output().exists()

def test_remove_upstream():
    params = {}
    pipe = Pipe([T3],params)
    pipe.remove_all()
    pipe.run()
    assert T1(**params).output().exists()
    assert T2(**params).output().exists()
    assert T3(**params).output().exists()
    pipe.remove_upstream([T2(**params)])
    assert T1(**params).output().exists()
    assert not T2(**params).output().exists()
    assert not T3(**params).output().exists()

def test_remove_orphans():
    params = {}
    pipe = Pipe([T3],params)
    pipe.remove_all()
    pipe.run()
    assert T1(**params).output().exists()
    assert T2(**params).output().exists()
    assert T3(**params).output().exists()
    T1(**params).remove()
    pipe.remove_orphans()
    assert not T1(**params).output().exists()
    assert T2(**params).output().exists()
    assert not T3(**params).output().exists()

def test_get_task_by_id():
    params = {}
    pipe = Pipe([T3],params)
    t3_id = T3(**params).task_id
    assert pipe.get_task_by_id(t3_id) == T3(**params)

def test_get_task_by_id_raises():
    params = {}
    pipe = Pipe([T3],params)
    try:
        pipe.get_task_by_id("wrog_name")
    except KeyError:
        return # success
    raise Exception("Key error waas not triggered")

def test_import_bokeh_plot():
    import pycarol.pipeline.viewer.bokeh_plot


# def test_remove_obsolete():
#     # need to implement metadata in targets
# test hard to automate

