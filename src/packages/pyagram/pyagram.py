import io
import sys

from . import constants
from . import encode
from . import exception
from . import interruption_data
from . import postprocess
from . import preprocess
from . import pyagram_state
from . import trace

class Pyagram:
    """
    """

    def __init__(self, code, *, debug):
        initial_stdout = sys.stdout
        interrupt_data = interruption_data.InterruptionData()
        while True:
            new_stdout = io.StringIO()
            try:
                try:
                    preprocessor = preprocess.Preprocessor(code, interrupt_data=interrupt_data)
                    preprocessor.preprocess()
                except SyntaxError as exc:
                    self.encoding = 'error'
                    self.data = encode.encode_pyagram_error(exc)
                else:
                    state = pyagram_state.State(
                        preprocessor.summary,
                        new_stdout,
                        interrupt_data=interrupt_data,
                    )
                    tracer = trace.Tracer(state)
                    bindings = {}
                    sys.stdout = new_stdout
                    terminal_ex = False
                    try:
                        tracer.run(
                            preprocessor.ast,
                            globals=bindings,
                            locals=bindings,
                        )
                    except exception.PyagramError as exc:
                        raise exc
                    except exception.CallWrapperInterruption as exc:
                        interrupt_data.exempt_fn_locs.add(exc.location)
                        continue
                    except exception.UnsupportedOperatorException as exc:
                        state.step()
                        state.program_state.caught_exc_info = (
                            type(exc),
                            exc.message,
                            state.program_state.curr_line_no,
                        )
                        state.step()
                    except Exception as exc:
                        terminal_ex = True
                        assert state.program_state.curr_element.is_global_frame
                        # TODO: You won't need terminal_ex if you don't take extraneous snapshots.
                    else:
                        assert state.program_state.curr_element.is_global_frame
                    postprocessor = postprocess.Postprocessor(state, terminal_ex)
                    postprocessor.postprocess()
                    self.encoding = 'result'
                    self.data = encode.encode_pyagram_result(state, postprocessor)
            except exception.PyagramError as exc:
                self.encoding = 'error'
                self.data = encode.encode_pyagram_error(exc)
            except Exception as exc:
                sys.stdout = initial_stdout
                if debug:
                    print(new_stdout.getvalue())
                    raise exc
                pyagram_error = exception.PyagramError(constants.GENERIC_ERROR_MSG)
                self.encoding = 'error'
                self.data = encode.encode_pyagram_error(pyagram_error)
            else:
                sys.stdout = initial_stdout
            break

    def serialize(self):
        """
        """
        return {
            'encoding': self.encoding,
            'data': self.data,
        }
