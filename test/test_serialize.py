import logging
import unittest
from pymacaron_async.serialization import model_to_task_arg
from pymacaron_async.serialization import task_arg_to_model
from pymacaron_core.swagger.api import API


log = logging.getLogger(__name__)


yaml = """
swagger: '2.0'
info:
  version: '0.0.1'
host: some.server.com
schemes:
  - http
produces:
  - application/json
definitions:
  Foo:
    type: object
    properties:
      foo:
        type: string
      bars:
        type: array
        items:
          $ref: '#/definitions/Bar'

  Bar:
    type: object
    properties:
      baz:
        type: number

"""


class Test(unittest.TestCase):


    def test__model_to_task_arg(self):
        api = API('somename', yaml_str=yaml)
        for o in (1, 's', [1, 2], {'a': 4}):
            self.assertEqual(model_to_task_arg(o), o)

        Foo = api.model.Foo(
            foo='blabla',
            bars=[
                api.model.Bar(baz=2),
                api.model.Bar(baz=3),
            ]
        )

        j = model_to_task_arg(Foo)
        self.assertEqual(
            j,
            {
                '__pymacaron_model_name': 'Foo',
                'bars': [{'baz': 2}, {'baz': 3}],
                'foo': 'blabla',
            }
        )


    def test__task_arg_to_model(self):
        for o in (1, 's', [1, 2], {'a': 4}):
            self.assertEqual(task_arg_to_model(o), o)

        o = task_arg_to_model(
            {
                '__pymacaron_model_name': 'Foo',
                'bars': [{'baz': 2}, {'baz': 3}],
                'foo': 'blabla',
            }
        )

        j = o.to_json()
        self.assertEqual(
            j,
            {
                'bars': [{'baz': 2}, {'baz': 3}],
                'foo': 'blabla',
            }
        )
