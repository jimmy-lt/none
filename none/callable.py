# none/callable.py
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
"""Callable facilities."""
import typing as ty
import functools


class hook(object):
    """A *hook* is a function or a method which when it is called, will also
    execute all other functions or methods hanging to it.

    A hook is created by using the class as a decorator.

    ::

        >>> import none
        >>> @none.callable.hook
        ... def my_hook():
        ...     print("I'm a hook.")


    Other functions can hang to the hook defined above by using the
    :class:`none.callable.catch` decorator.

    ::

        >>> @none.callable.catch(my_hook)
        ... def my_catch():
        ...     print("I'm hanging.")


    Therefore, when ``my_hook()`` is called, it will also call ``my_hanger()``
    (and other hanging functions) afterwards.

    ::

        >>> my_hook()
        I'm a hook.
        I'm hanging.


    A hook can also decorate a method. A catch within the same class context
    (including a child class) can hang to the hook by using it's name.

    ::

        >>> class Hookable(object):
        ...     @none.callable.hook
        ...     def my_hook(self):
        ...          print("I'm a hook in a class.")
        ...     @none.callable.catch("my_hook")
        ...     def my_catch(self)
        ...         print("I'm catching in a class.")
        ...
        >>> h = Hookable()
        >>> h.my_hook()
        I'm a hook in a class.
        I'm catching in a class.


    :param fn: The function or method which must serve as a hook.
    :type fn: ~typing.Optional[~typing.Callable]

    """

    def __init__(self, fn: ty.Optional[ty.Callable]):
        """Constructor for :class:`none.callable.hook`."""
        self.fn = fn
        self.hanging = set()
        self._owner: ty.Optional[ty.Type] = None

        if fn is not None:
            functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):
        """Execute the hook function along with its hanging functions."""
        self.hangup()
        self.fn(*(self._args + args), **kwargs)
        for fn in self.hanging:
            fn(*args, **kwargs)

    def __get__(self, instance: ty.Any, owner: ty.Optional[ty.Type] = None) -> "hook":
        """Allow the hook to serve has a method in a class context.


        :param instance: An instance of the owning class.
        :type instance: ~typing.Any

        :param owner: The owner class when the method is accessed has a class
                      method.
        :type owner: ~typing.Optional[~typing.Type]


        :returns: The callable to be used by the owning class, in this instance,
                  the hook itself.
        :rtype: ~none.callable.hook

        """
        self._owner = instance or owner
        return self

    @property
    def _args(self):
        """Quick facility to provide the owning class as first argument within
        a class context.

        """
        if self._owner is not None:
            return (self._owner,)
        return ()

    def hangup(self):
        """When the decorator is used within a class context, look for catching
        methods and hang them to the hook.

        """
        if self._owner is None:
            # The hook has not been accessed from a class context.
            return

        for name in dir(self._owner):
            # NOTE: By using ``getattr``, we force all catchers in the class to
            # already setup their owning class via ``__get__``.
            member = getattr(self._owner, name, None)
            if isinstance(member, catch) and member.hook == getattr(
                self, "__name__", None
            ):
                member._owner = self._owner
                self.hanging.add(member)


class catch(hook):
    """The ``catch`` decorator allow a function to notify a hook that it needs
    to be executed when the hook is called. A *catch* is also a hook, therefore
    allowing a chain of reaction when the primary hook is called.

    In order to define a catching function, a hook must already be available.

    ::

        >>> import none
        >>> @none.callable.hook
        ... def my_hook():
        ...     print("I'm a hook.")


    Then any function can catch an existing hook.

    ::

        >>> @none.callable.catch(my_hook)
        ... def my_catch():
        ...     print("I'm hanging.")


    By calling the hook, all functions hanging to it will also be called.

    ::

        >>> my_hook()
        I'm a hook.
        I'm hanging.


    It is also possible to catch a hook within the same class context by
    using its name.

    ::

        >>> class Hookable(object):
        ...     @none.callable.hook
        ...     def my_hook(self):
        ...          print("I'm a hook in a class.")
        ...     @none.callable.catch("my_hook")
        ...     def my_catch(self)
        ...         print("I'm catching in a class.")
        ...
        >>> h = Hookable()
        >>> h.my_hook()
        I'm a hook in a class.
        I'm catching in a class.


    :param target: The hook or the name of the hook to catch.
    :type target: ~typing.Union[~none.callable.hook, str]

    """

    def __init__(self, target: ty.Union[hook, str]):
        """Constructor for :class:`none.callable.hook`."""
        super(catch, self).__init__(None)
        self.hook = target

    def __call__(self, *args, **kwargs):
        """Execute the hook function along with its hanging functions."""
        if self.fn is None:
            # Decorator mode, we need to setup the decorated function.
            self._register(args[0])
            return self
        else:
            # Run mode.
            return super(catch, self).__call__(*args, **kwargs)

    def _register(self, fn: ty.Callable):
        """Utility the register the decorated function with its hook.


        :param fn: The callable being decorated.
        :type fn: ~typing.Callable

        """
        self.fn = fn
        functools.update_wrapper(self, self.fn)
        if isinstance(self.hook, hook):
            self.hook.hanging.add(self)
