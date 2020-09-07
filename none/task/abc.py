# none/task/abc.py
# ================
#
# Copying
# -------
#
# Copyright (c) 2020 none authors and contributors.
#
# This file is part of the *none* project.
#
# None is a free software project. You can redistribute it and/or
# modify it following the terms of the MIT License.
#
# This software project is distributed *as is*, WITHOUT WARRANTY OF ANY
# KIND; including but not limited to the WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE and NONINFRINGEMENT.
#
# You should have received a copy of the MIT License along with
# *none*. If not, see <http://opensource.org/licenses/MIT>.
#
"""Definitions of Abstract Base Classes."""
import typing as ty
import logging

from abc import ABC, abstractmethod

from none.callable import hook


log = logging.getLogger(__name__)


class Task(ABC):
    """An abstract callable class to implement a task.

    A task is a piece of code which must run in a controlled fashion. The
    task execution is controlled by using a number of events which are triggered
    at different stages within the task execution process.

    The code to be executed by the task is defined in its
    :meth:`~none.task.abc.Task.__call__` method.


    :param ignore_exc: The task execution will be considered a success even if
                       any of the exception listed here is raised.
    :type ignore_exc: ~typing.Optional[~typing.Iterable[Exception]]

    :param raise_exc: Should the exception raised during the task execution be
                      propagated to higher levels in case of failure?
    :type raise_exc: bool


    **Task failure scenarios:**

    +-----------------+-------------+------------------------+-----------------------+
    | *ignore_exc*    | *raise_exc* | No exception / Raised? | Exception / Raised?   |
    +=================+=============+========================+=======================+
    | *None* or empty | *False*     | Success / No           | **Failure** / No      |
    +-----------------+-------------+------------------------+-----------------------+
    | *None* or empty | *True*      | Success / No           | **Failure** / **Yes** |
    +-----------------+-------------+------------------------+-----------------------+
    | **Exception**   | *False*     | Success / No           | Success / No          |
    +-----------------+-------------+------------------------+-----------------------+
    | **Exception**   | *True*      | Success / No           | Success / No          |
    +-----------------+-------------+------------------------+-----------------------+

    """

    __slots__ = ("ignore_exc", "raise_exc")

    def __init__(
        self,
        ignore_exc: ty.Optional[ty.Iterable[Exception]] = None,
        raise_exc: bool = True,
    ):
        """Constructor for :class:`none.task.abc.Task`."""
        super(Task, self).__init__()
        self.ignore_exc = ignore_exc or ()
        self.raise_exc = raise_exc

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """Main execution loop of the task."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Provide a short description of the task.


        :type: str

        """
        try:
            return self.__doc__.splitlines()[0]
        except AttributeError:
            return ""

    @property
    def name(self) -> str:
        """The name attached to this task.


        :type: python:str

        """
        return self.__class__.__name__.lower()

    def run(self, *args, **kwargs):
        """Run the task in a controlled way with different events triggered at
        various stages in the task execution. All provided arguments are passed
        to the task's main loop.

        **Task execution flow:**

        .. graphviz:: /_lib/graphs/none.task.abc.Task.run.dot

        """
        log.info(f"Task {self.name}: Running.")
        exc = []
        try:
            log.debug(f"Task {self.name}: Trigger on_call() event.")
            self.on_call()
            try:
                self(*args, **kwargs)
            except Exception as e:
                log.warning(
                    f"Task {self.name}: An exception was raised during execution."
                )

                exc.append(e)
                if not isinstance(e, self.ignore_exc):
                    raise
            finally:
                log.info(f"Task {self.name}: Done.")
                log.debug(f"Task {self.name}: Trigger on_done() event.")
                self.on_done()
        except Exception as e:
            log.exception(f"Task {self.name}: An error has occurred during execution.")
            if e is not exc[-1]:
                exc.append(e)

            log.debug(f"Task {self.name}: Trigger on_failure() event.")
            self.on_failure(*exc)
            if self.raise_exc:
                raise
        else:
            log.info(f"Task {self.name}: Completed successfully.")
            log.debug(f"Task {self.name}: Trigger on_success() event.")
            self.on_success(*exc)
            if exc and self.raise_exc:
                raise exc[-1]
        finally:
            log.info(f"Task {self.name}: Exiting.")
            log.debug(f"Task {self.name}: Trigger on_exit() event.")
            self.on_exit()

    @hook
    def on_call(self):
        """This method is called right before the task is executed."""

    @hook
    def on_done(self):
        """This method is called right after the task has executed whether an
        error as occurred or not.

        This event can cause the task to fail independently from
        :attr:`~none.task.abc.Task.ignore_exc` if it raises an exception.

        """

    @hook
    def on_exit(self):
        """This method is called when the task is about to exit."""

    @hook
    def on_failure(self, *exc: Exception):
        """This method is called when the task has failed to run.

        All exceptions raised, was it during the task execution or by the
        :meth:`~none.task.abc.Task.on_done` event, are passed to the event in
        order.

        """

    @hook
    def on_success(self, *exc: Exception):
        """This method is called when the task has run successfully.

        If any exception listed in :attr:`~none.task.abc.Task.ignore_exc` was
        raised, it is provided to the event.

        """
