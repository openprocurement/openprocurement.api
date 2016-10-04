.. . Kicking page rebuild 2014-10-30 17:00:08

.. index:: Question, Answer, Author
.. _question:

Question
========

Schema
------

:id:
    uid, auto-generated

:author:
    :ref:`Organization`, required

    Who is asking a question (contactPoint - person, identification - organization that person represents).

:title:
    string, required

    Title of the question.

:description:
    string

    Description of the question.

:date:
    string, :ref:`date`, auto-generated

    Date of posting.

:dateAnswered:
    string, :ref:`date`, auto-generated

    Date of answer.

:answer:
    string

    Answer for the question asked.

:questionOf:
    string

    Possible values are:

    * `tender`
    * `item`
    * `lot`

:relatedItem:
    string

    Id of related :ref:`lot` or :ref:`item`.
