import luigi
from luigi import parameter, six
from luigi.task import flatten
from luigi.parameter import ParameterVisibility
from pycarol.pipeline.targets import PickleTarget
from pycarol.utils.miscellaneous import Hashabledict
import logging
import warnings

logger = logging.getLogger('luigi-interface')
logger.setLevel(logging.INFO)


class Task(luigi.Task):
    TARGET_DIR = './TARGETS/'  # this class attribute can be redefined somewhere else
    target_type = PickleTarget
    is_cloud_target = None
    requires_list = []
    requires_dict = {}
    #TODO (renan):  Remove support to requires_dict. ask me why...
    task_function = None
    task_notebook = None
    version = '0.0.0'
    metadata = {}

    def __call__(self,*args):
        """Alternative way to define pipeline"""
        return inherit_list(*args)(self.__class__)

    def buildme(self, local_scheduler=True, **kwargs):
        luigi.build([self, ], local_scheduler=local_scheduler, **kwargs)

    def _file_id(self):
        # returns the output default file identifier
        return luigi.task.task_id_str(self.get_task_family(), self.to_str_params(only_significant=True))

    def requires(self):
        if len(self.requires_list) > 0:
            result_list = []
            for t in self.requires_list:
                fixed_params = {}
                if type(t) is tuple:
                    fixed_params = t[1]
                    t = t[0]
                task_instance = self.clone(t, **fixed_params)
                result_list.append(task_instance)
            return result_list
        elif len(self.requires_dict) > 0:
            result_dict = {}
            for k, t in self.requires_dict.items():
                fixed_params = {}
                if type(t) is tuple:
                    fixed_params = t[1]
                    t = t[0]
                task_instance = self.clone(t, **fixed_params)
                result_dict.update({k: task_instance})
            return result_dict
        else:
            return []

    def output(self):
        if hasattr(self,'TARGET'):  # Check for deprecated use
            warnings.warn('TARGET is being replaced with target_type.', DeprecationWarning)
            return self.TARGET(self)

        return self.target_type(self)

    def load(self, **kwargs):
        return self.output().load(**kwargs)

    def load_metadata(self):
        return self.output().load_metadata()

    def remove(self):
        self.output().remove()
        self.output().remove_metadata()

    def save(self):
        self.output().dump(self.function_output)
        self.metadata['hash_version'] = self.hash_version()
        self.metadata['version'] = self.version
        self.metadata['params'] = self.get_execution_params(only_significant=False, only_public=True)
        self.output().dump_metadata(self.metadata)

    def run(self):

        self.function_output = self._easy_run()
        if not self.task_notebook:
            #in task_notebook mode, save is called inside the notebook
            self.save()
            del self.function_output # after dump, free memory

    def function_inputs(self):
        if isinstance(self.input(), list):
            function_inputs = [input_i.load(
                **self.load_input_params(input_i)) if self.load_input_params(
                input_i) else input_i.load() for input_i in self.input()]
        elif isinstance(self.input(), dict):
            function_inputs = {i: (input_i.load(
                **self.load_input_params(input_i)) if self.load_input_params(
                input_i) else input_i.load()) for i, input_i in
                               self.input().items()}
        return function_inputs

    def _easy_run(self):
        if not (self.easy_run or self.task_function or self.task_notebook):
            raise SyntaxError("One of [easy_run, task_function, task_notebook] "
                              "should be defined")

        if self.task_notebook:
            import papermill as pm
            pm.execute_notebook(
                self.task_notebook,
                f"executed_notebook/{self.task_notebook}",
                parameters=dict(
                    task_id=self.task_id
                )
            )
            return None
        elif self.task_function:
            inputs = self.function_inputs()
            if not isinstance(inputs,list):
                raise NotImplementedError(
                    f"In task_function mode, inputs should be list, not {type(inputs)}"
                    )
            params = self.get_execution_params(only_significant=True)
            print(params)
            if hasattr(self.task_function,'__func__'):
                f = self.task_function.__func__
            else:
                raise NotImplementedError(
                    "Should not pass here. We need unbound method"
                )
                f = self.task_function
            return f(*inputs,**params)

        else:
            inputs = self.function_inputs()
            return self.easy_run(inputs)

    def easy_run(self, inputs):
        return None

    def hash_version(self,):
        """ Returns the hash of the task considering only function, not the parameters."""
        from ..utils.hash_versioning import get_function_hash
        if not self.task_function:
            warnings.warn(
                "hash versioning only works in task_function mode. "\
                "It will return dummy hash code",SyntaxWarning
                )
            return 0
        else:
            try:
                return get_function_hash(self.task_function, ignore_not_implemented=True)
            except:
                return 0

    @classmethod
    def get_param_values(cls, params, args, kwargs):
        """
        This method was changed from the original version to allow execution of a task
        with extra parameters. the original one, raises an exception. now, we print 
        that exception in this version we do not raise neither print it.

        Get the values of the parameters from the args and kwargs.
        :param params: list of (param_name, Parameter).
        :param args: positional arguments
        :param kwargs: keyword arguments.
        :returns: list of `(name, value)` tuples, one for each parameter.
        
        """
        result = {}

        params_dict = dict(params)

        task_family = cls.get_task_family()

        # In case any exceptions are thrown, create a helpful description of how the Task was invoked
        # TODO: should we detect non-reprable arguments? These will lead to mysterious errors
        exc_desc = '%s[args=%s, kwargs=%s]' % (task_family, args, kwargs)

        # Fill in the positional arguments
        positional_params = [(n, p) for n, p in params if p.positional]
        for i, arg in enumerate(args):
            if i >= len(positional_params):
                raise parameter.UnknownParameterException(
                    '%s: takes at most %d parameters (%d given)' % (exc_desc, len(positional_params), len(args)))
            param_name, param_obj = positional_params[i]
            result[param_name] = param_obj.normalize(arg)

        # Then the keyword arguments
        for param_name, arg in six.iteritems(kwargs):
            if param_name in result:
                raise parameter.DuplicateParameterException(
                    '%s: parameter %s was already set as a positional parameter' % (exc_desc, param_name))
            if param_name not in params_dict:
                # raise parameter.UnknownParameterException('%s: unknown parameter %s' % (exc_desc, param_name))
                continue

            result[param_name] = params_dict[param_name].normalize(arg)

        # Then use the defaults for anything not filled in
        for param_name, param_obj in params:
            if param_name not in result:
                if not param_obj.has_task_value(task_family, param_name):
                    raise parameter.MissingParameterException(
                        "%s: requires the '%s' parameter to be set" % (exc_desc, param_name))
                result[param_name] = param_obj.task_value(task_family, param_name)

        def list_to_tuple(x):
            """ Make tuples out of lists and sets to allow hashing """
            if isinstance(x, list) or isinstance(x, set):
                return tuple(x)
            else:
                return x

        # Sort it by the correct order and make a list
        return [(param_name, list_to_tuple(result[param_name])) for param_name, param_obj in params]

    def get_execution_params(self, only_significant=False, only_public=True):
        """
        Get params values.


        """
        params_str = {}
        params = dict(self.get_params())
        for param_name, param_value in six.iteritems(self.param_kwargs):
            if (((not only_significant) or params[param_name].significant)
                    and ((not only_public) or params[param_name].visibility == ParameterVisibility.PUBLIC)
                    and params[param_name].visibility != ParameterVisibility.PRIVATE):

                #TODO: Should we save the :class: luigi.Parameter itself?
                params_str[param_name] = param_value

        return params_str


    def load_input_params(self, input_target):
        """
        Overwrite this if need to pass parameters when loading a requirement.

        :param input_target:
            Target that will be loaded.
        :return: `Dict`
            Return a dict with key/value parameters to be passed to Target.load()
        """
        return {}

#TODO: remove either WrapperTask or Dummy Target
class WrapperTask(Task):
    """
    Use for tasks that only wrap other tasks and that by definition are done if all their requirements exist.
    """
    def run(self):
        pass

    def complete(self):
        return all(r.complete() for r in flatten(self.requires()))

    def output(self):
        return self.input()


def set_attributes(task_to_inherit, task_that_inherits):
    fixed_params = {}

    if type(task_to_inherit) is tuple:
        fixed_params = task_to_inherit[1]
        task_to_inherit = task_to_inherit[0]

    for param_name, param_obj in task_to_inherit.get_params():
        if param_name in fixed_params:  # do not inherit fixed params
            continue

        # Check if the parameter exists in the inheriting task
        if not hasattr(task_that_inherits, param_name):
            # If not, add it to the inheriting task
            setattr(task_that_inherits, param_name, param_obj)
    return task_that_inherits


class inherit_list(object):
    # http://blog.thedigitalcatonline.com/blog/2015/04/23/python-decorators-metaprogramming-with-style/

    def __init__(self, *task_to_inherit_list):
        self.requires_list = list(task_to_inherit_list)
        # next, we use hashable dict in local task params to support pipeline viewer
        for i,v in enumerate(self.requires_list):
            if isinstance(v,tuple):
                task, params = v
                assert issubclass(task,Task)
                assert isinstance(params,dict)
                self.requires_list[i] = ( task, Hashabledict(params) )

    def __call__(self, task_that_inherits):
        task_that_inherits.requires_list = self.requires_list
        for task_to_inherit in task_that_inherits.requires_list:
            # Get all parameter objects from the underlying task
            task_that_inherits = set_attributes(task_to_inherit, task_that_inherits)

        return task_that_inherits


class inherit_dict(object):
    #TODO: hash versioning is not compatible with inherit_dict
    def __init__(self, **task_to_inherit_dict):
        self.requires_dict = task_to_inherit_dict

    def __call__(self, task_that_inherits):
        task_that_inherits.requires_dict = self.requires_dict

        for key, task_to_inherit in task_that_inherits.requires_dict.items():
            # Get all parameter objects from the underlying task
            task_that_inherits = set_attributes(task_to_inherit, task_that_inherits)
        return task_that_inherits
