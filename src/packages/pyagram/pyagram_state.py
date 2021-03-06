import gc
import inspect

from . import constants
from . import encode
from . import enum
from . import pyagram_element
from . import pyagram_wrapped_object
from . import utils

class State:
    """
    """

    def __init__(self, preprocessor_summary, stdout, *, interrupt_data):
        self.program_state = None
        self.memory_state = MemoryState(self)
        self.print_output = stdout
        self.encoder = encode.Encoder(self, preprocessor_summary)
        self.interrupt_data = interrupt_data
        self.snapshots = []

    def step(self, *args):
        """
        """
        if 0 == len(args):
            self.take_snapshot = True
        else:
            self.take_snapshot = False
            if self.program_state is None:
                frame, *_ = args
                self.program_state = ProgramState(self, frame)
            self.program_state.process_trace_event(*args)
        self.program_state.step()
        self.memory_state.step()
        # ------------------------------------------------------------------------------------------
        # TODO: Only take a snapshot when appropriate!
        # (*) Delete the next line.
        # (*) Set `self.take_snapshot = True` elsewhere in this file (and maybe others).
        # (*) PS: Right now it takes an eternity to run, since you're taking a million snapshots and then filtering out duplicates in postprocess.py.
        # (*) Don't take the last snapshot where curr_elem is None.
        self.take_snapshot = True
        # TODO: Before working on this bit, comment out kill_static_snapshots in postprocess.py.
        # ------------------------------------------------------------------------------------------
        if self.take_snapshot:
            self.snapshot()

    def snapshot(self):
        """
        """
        snapshot = {
            'memory_state': self.memory_state.snapshot(),
            'print_output': self.print_output.getvalue(),
            **self.program_state.snapshot(),
        }
        self.snapshots.append(snapshot)

class ProgramState:
    """
    """

    def __init__(self, state, global_frame):
        self.state = state
        self.global_frame = pyagram_element.PyagramFrame(
            None,
            enum.PyagramFrameTypes.GLOBAL,
            global_frame,
            state=state,
        )
        self.curr_element = self.global_frame
        self.curr_line_no = 0
        self.curr_trace_type = None
        self.caught_exc_info = None
        self.new_banners = {}
        self.finish_prev = None
        self.frame_types = {}
        self.frame_count = 0

    @property
    def is_flag(self):
        """
        """
        return isinstance(self.curr_element, pyagram_element.PyagramFlag)

    @property
    def is_builtin_flag(self):
        """
        """
        return self.is_flag and self.curr_element.is_builtin

    @property
    def is_ongoing_flag_sans_frame(self):
        """
        """
        return self.is_flag and self.curr_element.frame is None

    @property
    def is_ongoing_flag_with_frame(self):
        """
        """
        return self.is_flag and self.curr_element.frame is not None

    @property
    def is_complete_flag(self):
        """
        """
        return self.is_flag and self.curr_element.has_returned

    @property
    def is_frame(self):
        """
        """
        return isinstance(self.curr_element, pyagram_element.PyagramFrame)

    @property
    def is_ongoing_frame(self):
        """
        """
        return self.is_frame and not self.curr_element.has_returned

    @property
    def is_complete_frame(self):
        """
        """
        return self.is_frame and self.curr_element.has_returned

    def step(self):
        """
        """
        self.global_frame.step()

    def snapshot(self):
        """
        """
        return {
            'global_frame': self.state.encoder.encode_pyagram_frame(self.global_frame),
            'curr_line_no': self.curr_line_no,
            'exception': self.state.encoder.encode_caught_exc_info(self.caught_exc_info),
        }

    def process_trace_event(self, frame, trace_type, *step_info):
        """
        """
        self.curr_trace_type = trace_type
        if self.finish_prev is not None:
            self.finish_prev()
            self.finish_prev = None
        line_no, step_code, _ = utils.decode_lineno(
            frame.f_lineno,
            max_lineno=self.state.encoder.num_lines,
        )
        self.curr_line_no = line_no
        if frame not in self.frame_types:
            self.frame_types[frame] = enum.FrameTypes.identify_frame_type(step_code)
        frame_type = self.frame_types[frame]
        if trace_type is enum.TraceTypes.USER_CALL:
            self.process_frame_open(frame, frame_type)
        elif trace_type is enum.TraceTypes.USER_LINE:
            pass
        elif trace_type is enum.TraceTypes.USER_RETURN:
            return_value, = step_info
            self.process_frame_close(frame, frame_type, return_value)
        elif trace_type is enum.TraceTypes.USER_EXCEPTION:
            caught_exc_info, = step_info
            self.process_exception(frame, frame_type, caught_exc_info)
        else:
            raise enum.TraceTypes.illegal_enum(trace_type)

    def process_frame_open(self, frame, frame_type):
        """
        """
        if frame_type is enum.FrameTypes.SRC_CALL:
            if self.is_builtin_flag:
                self.open_pyagram_frame(enum.PyagramFrameTypes.BUILTIN, frame)
            # TODO: Should all this go at the beginning of open_pyagram_frame?
            is_implicit = self.is_ongoing_frame or (
                self.is_ongoing_flag_sans_frame
                and not self.curr_element.banner_is_complete
            )
            function = utils.get_function(frame)
            generator = utils.get_generator(frame)
            if is_implicit:
                self.open_pyagram_flag(enum.PyagramFlagTypes.CALL, None)
                if function is None:
                    self.curr_element.hide_from(0)
                else:
                    self.curr_element.fix_implicit_banner(function, frame.f_locals)
            self.open_pyagram_frame(
                None,
                frame,
                is_implicit=is_implicit,
                function=function,
                generator=generator,
            )
        elif frame_type is enum.FrameTypes.CALL_BANNER:
            pass
        elif frame_type is enum.FrameTypes.COMP_BANNER:
            pass
        elif frame_type is enum.FrameTypes.FN_WRAPPER:
            pass
        elif frame_type is enum.FrameTypes.RG_WRAPPER:
            pass
        elif frame_type is enum.FrameTypes.PG_WRAPPER:
            pass
        elif frame_type is enum.FrameTypes.CLASS_DEFN:
            self.open_class_frame(frame)
        elif frame_type is enum.FrameTypes.CNTNR_COMP:
            self.open_pyagram_frame(enum.PyagramFrameTypes.CNTNR_COMP, frame)
        else:
            raise enum.FrameTypes.illegal_enum(frame_type)

    def process_frame_close(self, frame, frame_type, return_value):
        """
        """
        if frame_type is enum.FrameTypes.SRC_CALL:
            self.close_pyagram_frame(return_value)
        elif frame_type is enum.FrameTypes.CALL_BANNER:
            self.open_pyagram_flag(enum.PyagramFlagTypes.CALL, return_value)
        elif frame_type is enum.FrameTypes.COMP_BANNER:
            self.open_pyagram_flag(enum.PyagramFlagTypes.COMP, return_value)
        elif frame_type is enum.FrameTypes.FN_WRAPPER:
            self.register_callable(return_value)
        elif frame_type is enum.FrameTypes.RG_WRAPPER:
            self.register_argument(return_value)
        elif frame_type is enum.FrameTypes.PG_WRAPPER:
            if self.curr_element is self.global_frame:
                self.close_pyagram_frame(return_value)
            else:
                self.close_pyagram_flag(return_value)
        elif frame_type is enum.FrameTypes.CLASS_DEFN:
            self.close_class_frame(frame)
        elif frame_type is enum.FrameTypes.CNTNR_COMP:
            self.close_pyagram_frame(return_value)
        else:
            raise enum.FrameTypes.illegal_enum(frame_type)

    def process_exception(self, frame, frame_type, caught_exc_info):
        """
        """
        _, _, traceback = caught_exc_info
        if traceback.tb_next is None:

            # This is the original exception.

            self.caught_exc_info = caught_exc_info
            self.exception_index = len(self.state.snapshots)
            is_generator_exception = self.is_frame \
                and len(self.curr_element.flags) == 1 \
                and self.curr_element.flags[0].frame is not None \
                and self.curr_element.flags[0].frame.is_generator_frame
            if is_generator_exception:
                exception_element = self.curr_element
                self.curr_element = self.curr_element.flags[0].frame
            def finish_step():
                if is_generator_exception:
                    self.curr_element = exception_element
                self.process_traceback(frame, frame_type)
                self.caught_exc_info = None
            self.defer(finish_step)
        else:
            self.process_traceback(frame, frame_type)

    def process_traceback(self, frame, frame_type):
        """
        """
        if self.is_frame:
            self.curr_element.hide_from(self.exception_index + 1)
        while self.is_flag or (self.is_frame and self.curr_element.is_builtin_frame):
            self.curr_element.hide_from(self.exception_index + 1)
            if self.is_flag:
                self.curr_element.hide_flags = True
            self.curr_element = self.curr_element.opened_by

    def open_pyagram_flag(self, pyagram_flag_type, banner_summary, **init_args):
        """
        """
        assert self.is_ongoing_flag_sans_frame or self.is_ongoing_frame
        self.curr_element = self.curr_element.add_flag(
            pyagram_flag_type,
            banner_summary,
            **init_args,
        )

    def open_pyagram_frame(self, pyagram_frame_type, frame, **init_args):
        """
        """
        assert self.is_ongoing_flag_sans_frame
        self.curr_element = self.curr_element.add_frame(
            pyagram_frame_type,
            frame,
            **init_args,
        )
        if pyagram_frame_type is enum.PyagramFrameTypes.BUILTIN:
            self.state.snapshot()

    def open_class_frame(self, frame):
        """
        """
        assert self.is_ongoing_frame
        pyagram_wrapped_object.PyagramClassFrame(frame, state=self.state)

    def close_pyagram_flag(self, return_value):
        """
        """
        if self.is_builtin_flag:
            self.open_pyagram_frame(enum.PyagramFrameTypes.BUILTIN, None)
        if self.is_frame:
            self.close_pyagram_frame(return_value)
        assert self.is_flag
        self.curr_element = self.curr_element.close()

    def close_pyagram_frame(self, return_value):
        """
        """
        assert self.is_ongoing_frame
        def finish_step():
            is_implicit = self.curr_element.is_implicit
            self.curr_element = self.curr_element.close(
                return_value,
                is_gen_exc=self.curr_trace_type is enum.TraceTypes.USER_EXCEPTION,
            )
            if is_implicit:
                self.curr_element = self.curr_element.close()
        if self.curr_element.is_global_frame:
            pass
        elif self.curr_element.is_builtin_frame:
            finish_step()
        elif self.curr_element.is_function_frame:
            finish_step()
        elif self.curr_element.is_generator_frame:
            self.defer(finish_step)
        elif self.curr_element.is_comprehension_frame:
            finish_step()
        else:
            raise enum.PyagramFrameTypes.illegal_enum(self.curr_element.frame_type)

    def close_class_frame(self, frame):
        """
        """
        assert self.is_ongoing_frame
        def finish_step():
            parent_bindings, class_name = frame.f_back.f_locals, frame.f_code.co_name
            if class_name in parent_bindings:
                self.state.memory_state.record_class_frame(frame, parent_bindings[class_name])
        self.defer(finish_step)

    def register_callable(self, callable):
        """
        """
        assert self.is_ongoing_flag_sans_frame
        self.curr_element.register_callable(callable)

    def register_argument(self, argument):
        """
        """
        assert self.is_ongoing_flag_sans_frame
        self.curr_element.register_argument(argument)

    def register_frame(self):
        """
        """
        self.frame_count += 1
        return self.frame_count

    def defer(self, function):
        """
        """
        assert self.finish_prev is None
        self.finish_prev = function

class MemoryState:
    """
    """

    def __init__(self, state):
        self.state = state
        self.objects = []
        self.obj_ids = set()
        self.wrapped_obj_ids = {}
        self.pg_class_frames = {}
        self.pg_generator_frames = {}
        self.function_parents = {}

    def step(self):
        """
        """
        for object in self.objects:
            object_type = enum.ObjectTypes.identify_tracked_object_type(object)
            if object_type is enum.ObjectTypes.FUNCTION:
                self.record_function(object)
                referents = utils.get_defaults(object)
            elif object_type is enum.ObjectTypes.METHOD:
                function = object.__func__
                instance = object.__self__
                self.record_function(function)
                referents = [
                    function,
                    *utils.get_defaults(function),
                    instance,
                ]
            elif object_type is enum.ObjectTypes.BUILTIN:
                if hasattr(object, '__self__') and not inspect.ismodule(object.__self__):
                    referents = [object.__self__]
                else:
                    referents = []
            elif object_type is enum.ObjectTypes.ORDERED_COLLECTION:
                referents = list(object)
            elif object_type is enum.ObjectTypes.UNORDERED_COLLECTION:
                referents = list(object)
            elif object_type is enum.ObjectTypes.MAPPING:
                referents = [
                    *object.keys(),
                    *object.values(),
                ]
            elif object_type is enum.ObjectTypes.ITERATOR:
                iterable = utils.get_iterable(object)
                referents = [] if iterable is None else [iterable]
            elif object_type is enum.ObjectTypes.GENERATOR:
                referents = []
            elif object_type is enum.ObjectTypes.USER_CLASS:
                referents = object.bindings.values()
            elif object_type is enum.ObjectTypes.BLTN_CLASS:
                referents = []
            elif object_type is enum.ObjectTypes.INSTANCE:
                referents = [
                    *object.__dict__.keys(),
                    *object.__dict__.values(),
                ]
            elif object_type is enum.ObjectTypes.RANGE:
                referents = [object.start, object.stop, object.step]
            elif object_type is enum.ObjectTypes.SLICE:
                referents = filter(
                    lambda referent: referent is not None,
                    [object.start, object.stop, object.step],
                )
            elif object_type is enum.ObjectTypes.OTHER:
                referents = []
            else:
                raise enum.ObjectTypes.illegal_enum(object_type)
            for referent in referents:
                self.track(referent)

    def snapshot(self):
        """
        """
        return [
            {
                'id': id(object),
                'object': self.state.encoder.encode_object(object),
            }
            for object in self.objects
        ]

    def track(self, object):
        """
        """
        is_tracked = id(object) in self.obj_ids
        is_wrapped = id(object) in self.wrapped_obj_ids
        if not is_tracked and not is_wrapped:
            reference_type = enum.ReferenceTypes.identify_reference_type(object)
            if reference_type is enum.ReferenceTypes.OMITTED:
                pass
            elif reference_type is enum.ReferenceTypes.UNKNOWN:
                pass
            elif reference_type is enum.ReferenceTypes.DEFAULT:
                object_type = enum.ObjectTypes.identify_raw_object_type(object)
                if object_type is enum.ObjectTypes.PRIMITIVE:
                    pass
                elif object_type is enum.ObjectTypes.GENERATOR:
                    pyagram_wrapped_object.PyagramGeneratorFrame(object, state=self.state)
                else:
                    self.objects.append(object)
                    self.obj_ids.add(id(object))
            else:
                raise enum.ReferenceTypes.illegal_enum(reference_type)

    def redirect(self, from_object, to_object):
        """
        """
        self.wrapped_obj_ids[id(from_object)] = id(to_object)

    def record_function(self, function):
        """
        """
        if function not in self.function_parents:
            utils.assign_unique_code_object(function)
            parent = self.state.program_state.curr_element
            while isinstance(parent, pyagram_element.PyagramFlag):
                parent = parent.opened_by
            self.function_parents[function] = parent

    def record_generator(self, pyagram_frame, generator):
        """
        """
        self.track(generator)
        pg_generator_frame = self.pg_generator_frames[generator]
        pg_generator_frame.prev_frame = pg_generator_frame.curr_frame
        pg_generator_frame.curr_frame = pyagram_frame

    def record_class_frame(self, frame_object, class_object):
        """
        """
        pyagram_class_frame = self.pg_class_frames[frame_object]
        pyagram_class_frame.wrap_object(class_object)
        pyagram_class_frame.class_obj = class_object
        pyagram_class_frame.initial_bases = self.state.encoder.encode_class_parents(class_object)
