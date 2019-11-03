"""
This modules contains miscellaneous helpers for various testing and stubbing scenarios.

Included are:

* modify_buffer_object() -- Modifies a Python buffer object to allow the user to replace weird and challenging
    functions/methods like socket.recv_into()
* await_condition() -- Repeated evaluates a callable at a specified poll rate for a given amount of time, and
    either returns if the callable became true quickly enough, or asserts otherwise.
"""

import ctypes
import time


def modify_buffer_object(source_buffer, dest_buffer, nbytes=None):
    """
    Modify a python object that supports the buffer interface internally.
    This is useful for testing things like socket.recv_into()

    dest_buffer must be smaller than source_buffer, or the code will assert.

    :param source_buffer: The source for the new data to be written into dest_buffer.
    :param dest_buffer: The buffer to be modified inline.
    :param nbytes: (OPTIONAL) The maximum number of bytes to write into the dest_buffer.
        If set, the number of bytes written is the minimum of nbytes and the source length.
        Default: None
    :return: The total number of bytes written into dest_buffer.
    """
    assert len(source_buffer) <= len(dest_buffer)
    copy_len = len(source_buffer) if nbytes is None else min(nbytes, source_buffer)
    buffer_ptr = (ctypes.c_byte * len(dest_buffer)).from_buffer(dest_buffer)
    new_value_ptr = (ctypes.c_byte * len(source_buffer)).from_buffer_copy(source_buffer)
    buffer_ptr[:copy_len] = new_value_ptr[:]
    return copy_len


def await_condition(description, condition_eval_callable, on_failure=lambda: True, timeout=10, poll_s=0.1):
    """
    Await a condition function to return True, otherwise raise an AssertionError if
    the condition did not return True within the alloted time.

    :param description: A string description of the condition we are awaiting.
    :type description: str
    :param condition_eval_callable: The callable of arity 0 (function, lambda, etc.) to monitor.
        This should return False when not completed, and return True when done.
    :type condition_eval_callable: -> bool
    :param on_failure: A callable of arity 0 that is called when a failure condition occurs.
        Default: NOOP
    :type on_failure: -> NoneType
    :param timeout:  The number of seconds to wait for the condition to become True.
        Default: 10 s
    :type timeout: float | int
    :param poll_s: The period of time between checking the condition.
        Default: 100 ms
    :type poll_s: float | int
    :return: None.
    :raises: AssertionError
    """
    start_time = time.time()

    def should_continue():
        return time.time() - start_time < timeout

    while not condition_eval_callable():
        if not should_continue():
            on_failure()
            raise AssertionError(
                "Awaiting condition {0} has timed out after {1} seconds".format(description, timeout)
            )
        time.sleep(poll_s)
