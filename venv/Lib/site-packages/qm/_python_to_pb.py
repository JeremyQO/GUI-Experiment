from collections import Iterable

from google.protobuf.struct_pb2 import Struct, ListValue, NULL_VALUE, Value


def python_to_pb(data):
    out = Value()
    if data is None:
        out.null_value = NULL_VALUE
    elif type(data) is str:
        out.string_value = data
    elif type(data) is int:
        out.number_value = data
    elif type(data) is float:
        out.number_value = data
    elif type(data) is dict:
        out.struct_value.SetInParent()
        for k, v in data.items():
            out.struct_value.fields.get_or_create(str(k)).CopyFrom(python_to_pb(v))
    elif isinstance(data, Iterable):
        for item in data:
            out.list_value.values.add().CopyFrom(python_to_pb(item))
    else:
        raise Exception("Unhandled type: " + str(type(data)))
    return out
