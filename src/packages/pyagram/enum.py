import numbers
import types

from . import configs
from . import pyagram_wrapped_object

class Enum:
    """
    """

    @staticmethod
    def illegal_enum(illegal_enum):
        return ValueError(f'not an enumeral: {illegal_enum}')

class TraceTypes(Enum):
    """
    """

    USER_CALL = object()
    USER_LINE = object()
    USER_RETURN = object()
    USER_EXCEPTION = object()

class FrameTypes(Enum):
    """
    """

    SRC_CALL_PRECURSOR = object()
    SRC_CALL = object()
    SRC_CALL_SUCCESSOR = object()
    CLASS_DEFINITION = object()

    @staticmethod
    def identify_frame_type(step_code):
        """
        """
        if step_code == configs.UNMODIFIED_LINENO:
            return FrameTypes.SRC_CALL
        elif step_code == configs.INNER_CALL_LINENO:
            return FrameTypes.SRC_CALL_PRECURSOR
        elif step_code == configs.OUTER_CALL_LINENO:
            return FrameTypes.SRC_CALL_SUCCESSOR
        elif step_code == configs.CLASS_DEFN_LINENO:
            return FrameTypes.CLASS_DEFINITION
        else:
            raise FrameTypes.illegal_enum(step_code)

class ObjectTypes(Enum):
    """

    # Primitives are values which should be compared with `==` instead of `is`.

    """

    PRIMITIVE_TYPES = (
        numbers.Number,
        str,
    )
    FUNCTION_TYPES = (
        types.FunctionType,
        types.MethodType,
    )
    BUILTIN_TYPES = (
        types.BuiltinFunctionType,
        types.BuiltinMethodType,
    )
    ORDERED_COLLECTION_TYPES = (
        list,
        tuple,
        str,
    )
    UNORDERED_COLLECTION_TYPES = (
        set,
        frozenset,
    )
    MAPPING_TYPES = (
        dict,
    )
    ITERATOR_TYPES = (
        type(iter([])),
        type(iter(())),
        type(iter('')),
        type(iter(set())),
        type(iter({}.keys())),
        type(iter({}.values())),
        type(iter({}.items())),
    )
    GENERATOR_TYPES = (
        types.GeneratorType,
    )

    PRIMITIVE = object()
    FUNCTION = object()
    BUILTIN = object()
    ORDERED_COLLECTION = object()
    UNORDERED_COLLECTION = object()
    MAPPING = object()
    ITERATOR = object()
    GENERATOR = object()
    OBJ_CLASS = object()
    OBJ_INST = object()
    OTHER = object()

    # TODO: Finish the above. Here are some ideas, but note they are not comprehensive ...
    # TODO:     odict, odict_keys, ordereddict, etc.
    # TODO:     types.MappingProxyType
    # TODO:     OrderedDict
    # TODO:     Counter
    # TODO:     What about namedtuple classes / instances?
    # TODO:     collections.*
    # TODO:     map (the output of a call to `map`)
    # TODO:     range
    # TODO:     Various built-in Exceptions

    @staticmethod
    def identify_object_type(object):
        """
        """
        if isinstance(object, ObjectTypes.PRIMITIVE_TYPES):
            return ObjectTypes.PRIMITIVE
        elif isinstance(object, ObjectTypes.FUNCTION_TYPES):
            return ObjectTypes.FUNCTION
        elif isinstance(object, ObjectTypes.BUILTIN_TYPES):
            return ObjectTypes.BUILTIN
        elif isinstance(object, ObjectTypes.ORDERED_COLLECTION_TYPES):
            return ObjectTypes.ORDERED_COLLECTION
        elif isinstance(object, ObjectTypes.UNORDERED_COLLECTION_TYPES):
            return ObjectTypes.UNORDERED_COLLECTION
        elif isinstance(object, ObjectTypes.MAPPING_TYPES):
            return ObjectTypes.MAPPING
        elif isinstance(object, ObjectTypes.ITERATOR_TYPES):
            return ObjectTypes.ITERATOR
        elif isinstance(object, ObjectTypes.GENERATOR_TYPES):
            return ObjectTypes.GENERATOR
        elif isinstance(object, pyagram_wrapped_object.PyagramClassFrame):
            return ObjectTypes.OBJ_CLASS
        elif hasattr(object, '__dict__'):
            return ObjectTypes.OBJ_INST
        else:
            return ObjectTypes.OTHER
