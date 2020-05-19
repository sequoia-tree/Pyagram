import inspect

from . import constants
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

    SRC_CALL = object()
    SRC_CALL_FN_WRAPPER = object()
    SRC_CALL_RG_WRAPPER = object()
    SRC_CALL_PRECURSOR = object()
    SRC_CALL_SUCCESSOR = object()
    CLASS_DEFINITION = object()
    COMPREHENSION = object()

    @staticmethod
    def identify_frame_type(step_code):
        """
        """
        if step_code == constants.UNMODIFIED_LINENO:
            return FrameTypes.SRC_CALL
        elif step_code == constants.FN_WRAPPER_LINENO:
            return FrameTypes.SRC_CALL_FN_WRAPPER
        elif step_code == constants.RG_WRAPPER_LINENO:
            return FrameTypes.SRC_CALL_RG_WRAPPER
        elif step_code == constants.INNER_CALL_LINENO:
            return FrameTypes.SRC_CALL_PRECURSOR
        elif step_code == constants.OUTER_CALL_LINENO:
            return FrameTypes.SRC_CALL_SUCCESSOR
        elif step_code == constants.CLASS_DEFN_LINENO:
            return FrameTypes.CLASS_DEFINITION
        elif step_code == constants.CNTNR_COMP_LINENO:
            return FrameTypes.COMPREHENSION
        else:
            raise FrameTypes.illegal_enum(step_code)

class PyagramFrameTypes(Enum):
    """
    """

    GLOBAL = object()
    BUILTIN = object()
    FUNCTION = object()
    GENERATOR = object()
    PLACEHOLDER = object()

class ObjectTypes(Enum):
    """
    """

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

    UNKNOWN = object()

    @staticmethod
    def identify_object_type(object):
        """
        """
        object_type = type(object)
        if object_type in constants.PRIMITIVE_TYPES:
            return ObjectTypes.PRIMITIVE
        elif object_type in constants.FUNCTION_TYPES:
            return ObjectTypes.FUNCTION
        elif object_type in constants.BUILTIN_TYPES:
            return ObjectTypes.BUILTIN
        elif object_type in constants.ORDERED_COLLECTION_TYPES:
            return ObjectTypes.ORDERED_COLLECTION
        elif object_type in constants.UNORDERED_COLLECTION_TYPES:
            return ObjectTypes.UNORDERED_COLLECTION
        elif object_type in constants.MAPPING_TYPES:
            return ObjectTypes.MAPPING
        elif object_type in constants.ITERATOR_TYPES:
            return ObjectTypes.ITERATOR
        elif object_type in constants.GENERATOR_TYPES:
            return ObjectTypes.GENERATOR
        elif object_type is pyagram_wrapped_object.PyagramClassFrame:
            return ObjectTypes.OBJ_CLASS
        elif hasattr(object, '__dict__'):
            return ObjectTypes.OBJ_INST
        else:
            return ObjectTypes.OTHER

class UnpackingTypes(Enum):
    """
    """

    NORMAL = object()
    SINGLY_UNPACKED = object()
    DOUBLY_UNPACKED = object()

    @staticmethod
    def identify_unpacking_type(unpacking_code):
        """
        """
        if unpacking_code == constants.NORMAL_ARG:
            return UnpackingTypes.NORMAL
        elif unpacking_code == constants.SINGLY_UNPACKED_ARG:
            return UnpackingTypes.SINGLY_UNPACKED
        elif unpacking_code == constants.DOUBLY_UNPACKED_ARG:
            return UnpackingTypes.DOUBLY_UNPACKED
        else:
            raise UnpackingTypes.illegal_enum(unpacking_code)
