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
import asyncio
import logging
import argparse
import itertools

from abc import ABC, abstractmethod
from collections.abc import Iterable, AsyncIterable

from none.callable import hook, asynchook
from none.collection.a import iter as aiter, islice as aislice


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


class AsyncTask(Task, ABC):
    """An abstract callable class to implement an asynchronous task.

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

    __slots__ = ()

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        """Main execution loop of the task."""
        raise NotImplementedError

    async def run(self, *args, **kwargs):
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
            await self.on_call()
            try:
                await self(*args, **kwargs)
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
                await self.on_done()
        except Exception as e:
            log.exception(f"Task {self.name}: An error has occurred during execution.")
            if e is not exc[-1]:
                exc.append(e)

            log.debug(f"Task {self.name}: Trigger on_failure() event.")
            await self.on_failure(*exc)
            if self.raise_exc:
                raise
        else:
            log.info(f"Task {self.name}: Completed successfully.")
            log.debug(f"Task {self.name}: Trigger on_success() event.")
            await self.on_success(*exc)
            if exc and self.raise_exc:
                raise exc[-1]
        finally:
            log.info(f"Task {self.name}: Exiting.")
            log.debug(f"Task {self.name}: Trigger on_exit() event.")
            await self.on_exit()

    @asynchook
    async def on_call(self):
        """This method is called right before the task is executed."""

    @asynchook
    async def on_done(self):
        """This method is called right after the task has executed whether an
        error as occurred or not.

        This event can cause the task to fail independently from
        :attr:`~none.task.abc.Task.ignore_exc` if it raises an exception.

        """

    @asynchook
    async def on_exit(self):
        """This method is called when the task is about to exit."""

    @asynchook
    async def on_failure(self, *exc: Exception):
        """This method is called when the task has failed to run.

        All exceptions raised, was it during the task execution or by the
        :meth:`~none.task.abc.Task.on_done` event, are passed to the event in
        order.

        """

    @asynchook
    async def on_success(self, *exc: Exception):
        """This method is called when the task has run successfully.

        If any exception listed in :attr:`~none.task.abc.Task.ignore_exc` was
        raised, it is provided to the event.

        """


class ArgumentTask(Task, ABC):
    """An abstract callable class to implement a command line task.

    The task can parse arguments provided on the command using it's
    :meth:`~none.task.abc.ArgumentTask.parse_args` method which are then made
    available via the :attr:`~none.task.abc.ArgumentTask.opts` attribute.

    The command line arguments are parsed using argparse's
    :class:`~argparse.ArgumentParser`.


    :param ignore_exc: The task execution will be considered a success even if
                       any of the exception listed here is raised.
    :type ignore_exc: ~typing.Optional[~typing.Iterable[Exception]]

    :param raise_exc: Should the exception raised during the task execution be
                      propagated to higher levels in case of failure?
    :type raise_exc: bool

    """

    __slots__ = ("opts", "parser")

    def __init__(
        self,
        ignore_exc: ty.Optional[ty.Iterable[Exception]] = None,
        raise_exc: bool = True,
    ):
        """Constructor for :class:`none.task.abc.ArgumentTask`."""
        super(ArgumentTask, self).__init__(ignore_exc=ignore_exc, raise_exc=raise_exc)

        #: The parsed arguments of the task.
        self.opts: ty.Optional[ty.Union[argparse.Namespace, dict]] = None
        #: The argument parser generated by
        #: :meth:`~none.task.abc.ArgumentTask.parse_args`.
        self.parser: ty.Optional[argparse.ArgumentParser] = None

    @property
    def arguments(self) -> ty.Iterable[ty.Tuple[ty.Sequence, ty.Mapping]]:
        """Command line arguments which are available for the task.

        This property returns a list of arguments as accepted by the
        :meth:`argparse.ArgumentParser.add_argument` method. This can be
        a list composed of a tuple and a dictionary ``[((), {})]``.


        :returns: A list of arguments allowed by the task.
        :rtype: ~typing.Iterable[~typing.Tuple[~typing.Sequence, ~typing.Mapping]]

        """
        return ()

    @property
    def version(self) -> str:
        """The current version of the task as a string.


        :type: str

        """
        return ""

    def parse_args(self, args: ty.Sequence[str], as_dict: bool = False):
        """Convert the command line strings into arguments for the task to
        operate with native Python objects.

        The parsed arguments are made available via the
        :attr:`~none.task.abc.InteractiveTask.opts` attribute. By default, the
        object is a :class:`~argparse.Namespace` where each attribute holds the
        parsed value. When ``as_dict`` is set to ``True``, parsed arguments are
        made available in a dictionary.


        :param args: A list of argument strings from the command line. This
                     value is most likely extracted from :class:`sys.argv`.
        :type args: ~typing.Sequence[str]

        :param as_dict: When ``True``, parsed arguments are stored in a
                        dictionary instead of in a :class:`~argparse.Namespace`
                        object.
        :type as_dict: bool

        """
        parser = argparse.ArgumentParser(prog=self.name, description=self.description)

        version = self.version
        if version:
            parser.add_argument(
                "-V", "--version", action="version", version=f"%(prog)s {version}"
            )

        for t_args, t_kwargs in self.arguments:
            parser.add_argument(*t_args, **t_kwargs)

        opts = parser.parse_args(args)
        self.opts = vars(opts) if as_dict else opts
        self.parser = parser

        self.on_argparse()

    @hook
    def on_argparse(self):
        """This method is called after the parsing of the command line
        arguments.

        """


class AsyncArgumentTask(AsyncTask, ArgumentTask, ABC):
    """An abstract callable class to implement a command line asynchronous task.

    The task can parse arguments provided on the command using it's
    :meth:`~none.task.abc.ArgumentTask.parse_args` method which are then made
    available via the :attr:`~none.task.abc.ArgumentTask.opts` attribute.

    The command line arguments are parsed using argparse's
    :class:`~argparse.ArgumentParser`.


    :param ignore_exc: The task execution will be considered a success even if
                       any of the exception listed here is raised.
    :type ignore_exc: ~typing.Optional[~typing.Iterable[Exception]]

    :param raise_exc: Should the exception raised during the task execution be
                      propagated to higher levels in case of failure?
    :type raise_exc: bool

    """

    __slots__ = ()

    def __init__(
        self,
        ignore_exc: ty.Optional[ty.Iterable[Exception]] = None,
        raise_exc: bool = True,
    ):
        """Constructor for :class:`none.task.abc.ArgumentTask`."""
        ArgumentTask.__init__(self)
        super(AsyncArgumentTask, self).__init__(ignore_exc=ignore_exc, raise_exc=raise_exc)

    @property
    async def arguments(self) -> ty.AsyncIterable[ty.Tuple[ty.Sequence, ty.Mapping]]:
        """Command line arguments which are available for the task.

        This property returns a list of arguments as accepted by the
        :meth:`argparse.ArgumentParser.add_argument` method. This can be
        a list composed of a tuple and a dictionary ``[((), {})]``.


        :returns: A list of arguments allowed by the task.
        :rtype: ~typing.Iterable[~typing.Tuple[~typing.Sequence, ~typing.Mapping]]

        """
        while False:
            yield ()

    async def parse_args(self, args: ty.Sequence[str], as_dict: bool = False):
        """Convert the command line strings into arguments for the task to
        operate with native Python objects.

        The parsed arguments are made available via the
        :attr:`~none.task.abc.InteractiveTask.opts` attribute. By default, the
        object is a :class:`~argparse.Namespace` where each attribute holds the
        parsed value. When ``as_dict`` is set to ``True``, parsed arguments are
        made available in a dictionary.


        :param args: A list of argument strings from the command line. This
                     value is most likely extracted from :class:`sys.argv`.
        :type args: ~typing.Sequence[str]

        :param as_dict: When ``True``, parsed arguments are stored in a
                        dictionary instead of in a :class:`~argparse.Namespace`
                        object.
        :type as_dict: bool

        """
        parser = argparse.ArgumentParser(prog=self.name, description=self.description)

        version = self.version
        if version:
            parser.add_argument(
                "-V", "--version", action="version", version=f"%(prog)s {version}"
            )

        async for t_args, t_kwargs in self.arguments:
            parser.add_argument(*t_args, **t_kwargs)

        opts = parser.parse_args(args)
        self.opts = vars(opts) if as_dict else opts
        self.parser = parser

        await self.on_argparse()

    @asynchook
    async def on_argparse(self):
        """This method is called after the parsing of the command line
        arguments.

        """


class Batch(Iterable, ABC):
    """A task specialization to run on series of data. For each piece of data
    generated by the batch, a new task is executed. Data can be grouped with the
    ``batch_size`` argument.

    This mixin class is meant to be inherited in association with a
    :class:`~none.task.abc.Task` class.


    :param batch_size: The maximum number of elements which will be provided
                       to each task. By default a new task is created for each
                       piece of data one by one. When set to ``None`` all the
                       generated data is given to a unique task at once.
    :type batch_size: ~typing.Optional[int]

    :param raise_exc: Should the exception raised during a task execution be
                      propagated to higher levels in case of failure?
    :type raise_exc: bool

    """

    def __init__(
        self,
        batch_size: ty.Optional[int] = None,
        raise_exc: bool = True,
        *args,
        **kwargs,
    ):
        """Constructor for :class:`none.task.abc.Batch`."""
        super(Batch, self).__init__(raise_exc=True, *args, **kwargs)

        #: A suffix indicating the task's advancement in the batch.
        self._batch_suffix: str = ""

        #: The maximum number of elements to pass to each task.
        self.batch_size: int = batch_size
        #: Should the batch task propagated the raised exception to upper
        #: layers?
        self.batch_raise_exc: bool = raise_exc

    def __iter__(self):
        """Iterate over the generated data and group each element up to
        :attr:`~none.task.abc.Batch.batch_size`.

        """
        it = iter(self.data)
        yield from iter(lambda: list(itertools.islice(it, self.batch_size)), [])

    @property
    @abstractmethod
    def data(self):
        """A generator to feed the task with data. The generator should generate
        data element one by one.

        """
        while False:
            yield None

    @property
    def name(self) -> str:
        """The name attached to this task.


        :type: python:str

        """
        return super(Batch, self).name + self._batch_suffix

    def run(self, *args, **kwargs):
        """Run the batch in a controlled way with different events triggered at
        various stages in the execution. All provided arguments are passed to
        the underneath tasks.

        """
        log.info(f"Batch {self.name}: Running.")
        exc = []
        try:
            log.debug(f"Batch {self.name}: Trigger on_batch_call() event.")
            self.on_batch_call()
            try:
                for idx, unit in enumerate(self):
                    self._batch_suffix = f".{str(idx)}"
                    try:
                        super(Batch, self).run(
                            unit[0] if self.batch_size == 1 else unit, *args, **kwargs,
                        )
                    except Exception as e:
                        exc.append(e)
                        if not isinstance(e, self.ignore_exc):
                            raise
                    finally:
                        self._batch_suffix = ""
            finally:
                log.info(f"Batch {self.name}: Done.")
                log.debug(f"Batch {self.name}: Trigger on_batch_done() event.")
                self.on_batch_done()
        except Exception as e:
            log.exception(f"Batch {self.name}: An error has occurred during execution.")
            if not exc or e is not exc[-1]:
                exc.append(e)

            log.debug(f"Batch {self.name}: Trigger on_batch_failure() event.")
            self.on_batch_failure(*exc)
            if self.batch_raise_exc:
                raise
        else:
            log.info(f"Batch {self.name}: Completed successfully.")
            log.debug(f"Batch {self.name}: Trigger on_batch_success() event.")
            self.on_batch_success(*exc)
            if exc and self.batch_raise_exc:
                raise exc[-1]
        finally:
            log.info(f"Batch {self.name}: Exiting.")
            log.debug(f"Batch {self.name}: Trigger on_batch_exit() event.")
            self.on_batch_exit()

    @hook
    def on_batch_call(self):
        """This method is executed when the batch execution is about to start."""

    @hook
    def on_batch_done(self):
        """This method is called right after the batch has executed all of its
        tasks should it be with or without an error occurrence.

        This event can cause the batch to fail independently from
        :attr:`~none.task.abc.Task.ignore_exc` if it raises an exception.

        """

    @hook
    def on_batch_exit(self):
        """This method is executed when the batch is about to exit."""

    @hook
    def on_batch_failure(self, *exc):
        """This method is executed when execution of a batch unit has failed to
        run.

        """

    @hook
    def on_batch_success(self, *exc):
        """This method is executed when execution of all batch units completed
        successfully.

        """


class AsyncBatch(AsyncIterable, ABC):
    """An asynchronous task specialization to run on series of data. For each
    piece of data generated by the batch, a new asynchronous task is executed.
    Data can be grouped with the ``batch_size`` argument.

    This mixin class is meant to be inherited in association with a
    :class:`~none.task.abc.AsyncTask` class.


    :param batch_size: The maximum number of elements which will be provided
                       to each task. By default a new task is created for each
                       piece of data one by one. When set to ``None`` all the
                       generated data is given to a unique task at once.
    :type batch_size: ~typing.Optional[int]

    :param raise_exc: Should the exception raised during a task execution be
                      propagated to higher levels in case of failure?
    :type raise_exc: bool

    """

    def __init__(
        self,
        batch_size: ty.Optional[int] = None,
        raise_exc: bool = True,
        *args,
        **kwargs,
    ):
        """Constructor for :class:`none.task.abc.AsyncBatch`."""
        super(AsyncBatch, self).__init__(raise_exc=True, *args, **kwargs)

        #: The maximum number of elements to pass to each task.
        self.batch_size: int = batch_size
        #: Should the batch task propagated the raised exception to upper
        #: layers?
        self.batch_raise_exc: bool = raise_exc

    async def __aiter__(self):
        """Iterate asynchronously over the generated data and group each element
        up to :attr:`~none.task.abc.Batch.batch_size`.

        """

        class _alist(object):
            __slots__ = ("_batch_size", "_it")

            def __init__(self, iterable: ty.AsyncIterator, batch_size):
                self._batch_size = batch_size
                self._it = aiter(iterable)

            async def __call__(self) -> ty.List:
                return [x async for x in aislice(self._it, self._batch_size)]

        async for x in aiter(_alist(self.data, self.batch_size), []):
            yield x

    @property
    @abstractmethod
    async def data(self):
        """A generator to feed the task with data. The generator should generate
        data element one by one.

        """
        while False:
            yield None

    async def run(self, *args, **kwargs):
        """Run the batch in a controlled way with different events triggered at
        various stages in the execution. All provided arguments are passed to
        the underneath tasks.

        """
        log.info(f"Batch {self.name}: Running.")
        tasks = [
            asyncio.ensure_future(
                super(AsyncBatch, self).run(
                    unit[0] if self.batch_size == 1 else unit, *args, **kwargs,
                )
            )
            async for unit in self
        ]

        exc = []
        try:
            log.debug(f"Batch {self.name}: Trigger on_batch_call() event.")
            await self.on_batch_call()
            try:
                for output in asyncio.as_completed(tasks):
                    try:
                        await output
                    except Exception as e:
                        exc.append(e)
                        if not isinstance(e, self.ignore_exc):
                            #  NOTE: By doing so we ignore exceptions from other
                            #        tasks.
                            raise
            finally:
                log.info(f"Batch {self.name}: Done.")
                log.debug(f"Batch {self.name}: Trigger on_batch_done() event.")
                await self.on_batch_done()
        except Exception as e:
            log.exception(f"Batch {self.name}: An error has occurred during execution.")
            if not exc or e is not exc[-1]:
                exc.append(e)

            log.debug(f"Batch {self.name}: Trigger on_batch_failure() event.")
            await self.on_batch_failure(*exc)
            if self.batch_raise_exc:
                raise
        else:
            log.info(f"Batch {self.name}: Completed successfully.")
            log.debug(f"Batch {self.name}: Trigger on_batch_success() event.")
            await self.on_batch_success(*exc)
            if exc and self.batch_raise_exc:
                raise exc[-1]
        finally:
            log.info(f"Batch {self.name}: Exiting.")
            log.debug(f"Batch {self.name}: Trigger on_batch_exit() event.")
            await self.on_batch_exit()

    @asynchook
    async def on_batch_call(self):
        """This method is executed when the batch execution is about to start."""

    @asynchook
    async def on_batch_done(self):
        """This method is called right after the batch has executed all of its
        tasks should it be with or without an error occurrence.

        This event can cause the batch to fail independently from
        :attr:`~none.task.abc.Task.ignore_exc` if it raises an exception.

        """

    @asynchook
    async def on_batch_exit(self):
        """This method is executed when the batch is about to exit."""

    @asynchook
    async def on_batch_failure(self, *exc):
        """This method is executed when execution of a batch unit has failed to
        run.

        """

    @asynchook
    async def on_batch_success(self, *exc):
        """This method is executed when execution of all batch units completed
        successfully.

        """
