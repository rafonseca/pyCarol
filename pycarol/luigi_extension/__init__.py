import warnings
warnings.warn("Using luigi_extension is deprecated. It is now called 'pipeline'", DeprecationWarning,
              stacklevel=2)

from .task import(
    Task,
    WrapperTask,
    inherit_list,
    inherit_dict
)

from .targets import (
    CDSTarget,
    PickleTarget,
    KerasTarget,
    DummyTarget,
    JsonTarget,
    FeatherTarget,
    PytorchTarget,
    PickleTarget,
    PytorchTarget,
    KerasTarget,
    LocalTarget,
    DummyTarget,
)
from pycarol.luigi_extension.targets.deprecated_targets import PicklePyCarolTarget, PytorchPyCarolTarget, \
    KerasPyCarolTarget, PickleLocalTarget, KerasLocalTarget, PytorchLocalTarget, JsonLocalTarget, FeatherLocalTarget


from pycarol.luigi_extension.viewer.task_visualization import (
    Visualization
)
