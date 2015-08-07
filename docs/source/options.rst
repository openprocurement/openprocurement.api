.. _options:

Options
=========

In addition to providing fields and their values in a request, you may also
specify options to control how your request is interpreted and how the
response is generated.  For GET requests, options are specified as URL
parameters prefixed with `opt_`.  For POST or PUT requests, options are
specified in the body, inside the top-level options object (a sibling of the
data object).  The option specified in the body overrides the `opt_` one
from URL parameter.

These options can be used in different combinations in a single request, though some of
them may conflict in their impact on the response.

:pretty:
  `?opt_pretty`

  `options: { pretty: true }` 

  Provides the response in "pretty" output.  In case of JSON this means
  doing proper line breaking and indentation to make it readable.  This will
  take extra time and increase the response size so it is advisable to use
  this only during debugging.
:jsonp:
  `?opt_jsonp=myCallback`

  Returns the output in JSON-P format instead of plain JSON. This allows
  requests to come from within browsers and work around the "same origin
  policy." The function named as the value of the `opt_jsonp` parameter will
  be called with a single argument, a JavaScript object representing the
  response.

:fields:
  `?opt_fields=comma,separated,field,list`

  List of extra fields to include in response.