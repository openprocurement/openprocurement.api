.. _options:

Options
=========

In addition to providing fields and their values in a request, you may also
specify options to control how your request is interpreted and how the
response is generated.  For GET requests, options are specified as URL
parameters prefixed with `opt_`.  For POST or PUT requests, options are
specified in the body, inside the top-level options object (a sibling of the
data object).

These options can be used in combination in a single request, though some of
them may conflict in their impact on the response.
