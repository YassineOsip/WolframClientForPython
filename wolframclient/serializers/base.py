# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from wolframclient.serializers.normalizer import Normalizer
from wolframclient.utils import six
from wolframclient.utils.encoding import force_text
from wolframclient.utils.functional import first

import inspect
import re

class FormatSerializer(Normalizer):

    def dump(self, data, stream):
        raise NotImplementedError

    def export(self, data, stream = None):
        if stream:
            if isinstance(stream, six.string_types):
                with open(stream, 'wb') as file:
                    self.dump(data, file)
                    return stream

            self.dump(data, stream)
            return stream

        stream = six.BytesIO()
        stream = self.dump(data, stream)
        stream.seek(0)
        return stream.read()

    #implementation of several methods

    def serialize_function(self, head, args):
        raise NotImplementedError

    def serialize_symbol(self, symbol):
        raise NotImplementedError

    def serialize_string(self, obj):
        raise NotImplementedError

    def serialize_bytes(self, obj):
        raise NotImplementedError

    def serialize_float(self, obj):
        raise NotImplementedError

    def serialize_decimal(self, obj):
        raise NotImplementedError

    def serialize_integer(self, obj):
        raise NotImplementedError

    def serialize_iterable(self, iterable):
        return self.serialize_function(
            self.serialize_symbol(b'List'),
            iterable
        )

    def serialize_mapping(self, mappable):
        return self.serialize_function(
            self.serialize_symbol(b'Association'), (
                self.serialize_rule(key, value)
                for key, value in mappable
            )
        )

    def serialize_fraction(self, o):
        return self.serialize_function(
            self.serialize_symbol(b'Rational'), (
                self.serialize_integer(o.numerator),
                self.serialize_integer(o.denominator)
            )
        )

    def serialize_complex(self, o):
        return self.serialize_function(
            self.serialize_symbol(b'Complex'), (
                self.serialize_float(o.real),
                self.serialize_float(o.imag),
            )
        )

    def serialize_rule(self, lhs, rhs):
        return self.serialize_function(
            self.serialize_symbol(b'Rule'), (
                lhs,
                rhs
            )
        )

    def serialize_rule_delayed(self, lhs, rhs):
        return self.serialize_function(
            self.serialize_symbol(b'RuleDelayed'), (
                lhs,
                rhs
            )
        )

    def serialize_tzinfo(self, date, name_match = re.compile('^[A-Za-z]+(/[A-Za-z]+)?$')):

        if date.tzinfo is None:
            return self.serialize_symbol(b"$TimeZone")

        name = date.tzinfo.tzname(None)

        if name and name_match.match(name):
            return self.serialize_string(name)

        return self.serialize_float(date.utcoffset().total_seconds() / 3600)

    def _serialize_external_object(self, o):

        yield "Type",       "PythonFunction"
        yield "Name",       force_text(o.__name__)
        yield "BuiltIn",    inspect.isbuiltin(o),

        is_module = inspect.ismodule(o)

        yield "IsModule", is_module

        if not is_module:
            module = inspect.getmodule(o)
            if module:
                yield "Module", force_text(module.__name__)

        yield "IsClass",    inspect.isclass(o),
        yield "IsFunction", inspect.isfunction(o),
        yield "IsMethod",   inspect.ismethod(o),
        yield "Callable",   callable(o)

        if callable(o):
            yield "Arguments", first(inspect.getargspec(o))

    def serialize_external_object(self, obj):
        return self.serialize_function(
            self.serialize_symbol(b'ExternalObject'), (
                self.serialize_mapping(
                    (self.normalize(key), self.normalize(value))
                    for key, value in self._serialize_external_object(obj)
                ),
            )
        )