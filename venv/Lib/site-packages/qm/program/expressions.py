from qm.pb.inc_qua_pb2 import QuaProgram as _Q
from qm._loc import _get_loc


def var(name):
    """
    A reference to a variable
    :param name:
    :return:
    """
    exp = _Q.VarRefExpression()
    exp.name = name
    exp.loc = _get_loc()
    return exp


def binary(left, sop, right):
    """
    A binary operation
    :param left:
    :param sop:
    :param right:
    :return:
    """
    exp = _Q.AnyScalarExpression()
    exp.binaryOperation.SetInParent()
    exp.binaryOperation.loc = _get_loc()
    exp.binaryOperation.left.CopyFrom(left)
    exp.binaryOperation.right.CopyFrom(right)

    if sop == "+":
        op = _Q.BinaryExpression.ADD
    elif sop == "-":
        op = _Q.BinaryExpression.SUB
    elif sop == ">":
        op = _Q.BinaryExpression.GT
    elif sop == "<":
        op = _Q.BinaryExpression.LT
    elif sop == "<=":
        op = _Q.BinaryExpression.LET
    elif sop == ">=":
        op = _Q.BinaryExpression.GET
    elif sop == "==":
        op = _Q.BinaryExpression.EQ
    elif sop == "*":
        op = _Q.BinaryExpression.MULT
    elif sop == "/":
        op = _Q.BinaryExpression.DIV
    elif sop == "|":
        op = _Q.BinaryExpression.OR
    elif sop == "&":
        op = _Q.BinaryExpression.AND
    elif sop == "^":
        op = _Q.BinaryExpression.XOR
    elif sop == "<<":
        op = _Q.BinaryExpression.SHL
    elif sop == ">>":
        op = _Q.BinaryExpression.SHR
    else:
        raise Exception("Unsupported operator " + sop)

    exp.binaryOperation.op = op
    return exp


def literal_int(value):
    exp = _Q.AnyScalarExpression()
    exp.literal.value = str(value)
    exp.literal.type = _Q.INT
    exp.literal.loc = _get_loc()
    return exp


def literal_bool(value):
    exp = _Q.AnyScalarExpression()
    exp.literal.value = str(value)
    exp.literal.type = _Q.BOOL
    exp.literal.loc = _get_loc()
    return exp


def literal_real(value):
    exp = _Q.AnyScalarExpression()
    exp.literal.value = str(value)
    exp.literal.type = _Q.REAL
    exp.literal.loc = _get_loc()
    return exp


def io1():
    exp = _Q.AnyScalarExpression()
    exp.variable.ioNumber = 1
    exp.variable.loc = _get_loc()
    return exp


def io2():
    exp = _Q.AnyScalarExpression()
    exp.variable.ioNumber = 2
    exp.variable.loc = _get_loc()
    return exp


def array(value, index_exp):
    if index_exp is None:
        return value
    else:
        loc = _get_loc()
        exp = _Q.AnyScalarExpression()
        exp.arrayCell.arrayVar.CopyFrom(value)
        exp.arrayCell.arrayVar.loc = loc
        exp.arrayCell.index.CopyFrom(index_exp)
        exp.arrayCell.loc = loc
        return exp


def var_ref(value, index_exp):
    exp = _Q.AnyScalarExpression()

    loc = _get_loc()
    if index_exp is None:
        exp.variable.name = value
        exp.variable.loc = loc
    else:
        array_var = _Q.ArrayVarRefExpression()
        array_var.name = value
        exp.arrayCell.arrayVar.CopyFrom(array_var)
        exp.arrayCell.arrayVar.loc = loc
        exp.arrayCell.index.CopyFrom(index_exp)
        exp.arrayCell.loc = loc

    return exp


def lib_func(lib_name, func_name, *args):
    exp = _Q.AnyScalarExpression()

    exp.libFunction.SetInParent()
    exp.libFunction.loc = _get_loc()
    exp.libFunction.functionName = func_name
    exp.libFunction.libraryName = lib_name
    for arg in args:
        if isinstance(arg, _Q.ArrayVarRefExpression):
            element = exp.libFunction.arguments.add()
            element.array.CopyFrom(arg)
        else:
            element = exp.libFunction.arguments.add()
            element.scalar.CopyFrom(arg)

    return exp
