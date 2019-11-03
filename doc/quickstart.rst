Test Toolbox Quickstart
=======================

This page documents how to quickly utilize one or more of the components packaged in the test toolbox library
to enhance your Python tests.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


"test_toolbox.bdd"
------------------

This module contains the "behavior driven development" helper object, appropriately named "BDD". This
module is inspired by the ScalaTest implementation of BDD primitives; more on the ScalaTest and BDD
may be found here_.

.. _here: http://www.scalatest.org/user_guide/tests_as_specifications

To get started with this library, import the BDD class from the `test_toolbox.bdd` module,

.. code:: python

  from test_toolbox.bdd import BDD

This BDD object should work with all major Python testing frameworks, included the standard library unittest and
the popular pytest framework. An example of how to use the the BDD object is given below, in a sample unittest.

.. code:: python

   from unittest import TestCase
   import os

   class MyTestCase(TestCase):
       def test_foo(self):
           with BDD.scenario("I have some pipes and want to send data") as bdd:
               bdd.given("I create a new unix pipe)
               read_fd, write_fd = os.pipe()
               test_data = b"foobar"

               bdd.and("I write some data to the write file descriptor")
               os.write(write_fd, test_data)

               bdd.then("I should be able to read the data back from the read file descriptor")
               assert os.read(read_fd, 512) == test_data

Additionally, each of the clauses may also be used as a with statement, allowing sub-clauses as follows:

.. code:: python

   from unittest import TestCase
   import os

   class MyTestCase(TestCase):
       def test_foo(self):
           with BDD.scenario("I have some pipes and want to send data") as bdd:
               with bdd.given("I create a new unix pipe) as clause:
                   read_fd, write_fd = os.pipe()
                   test_data = b"foobar"

                   clause.and("I close the read fd")
                   os.close(read_fd)

               bdd.then("who knows what happens when I write data")
               os.write(write_fd, test_data)


`with` statements may be used with any of the clauses, even if new BDD sub-clauses are not created, for the purpose
of enhancing test readability. The valid BDD "words" you may use to form clauses are:

* `given`
* `when`
* `then`
* `also`
* `and_`
* `but`

More words may be added (please open a pull request) if sensible and desired.

"test_toolbox.helpers"
----------------------

TODO

"test_toolbox.output"
---------------------

TODO

"test_toolbox.spy"
------------------

TODO

"test_toolbox.unittest.testflow"
--------------------------------

TODO