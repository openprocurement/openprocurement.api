��          t               �   �  �   ,   �     �  �   �  )  �  �   �  (   y     �     �     �  W  �  �  <  ,   	     5	  �   =	  )  3
  �   ]  (   �          )     7   In addition to providing fields and their values in a request, you may also specify options to control how your request is interpreted and how the response is generated.  For GET requests, options are specified as URL parameters prefixed with `opt_`.  For POST or PUT requests, options are specified in the body, inside the top-level options object (a sibling of the data object).  The option specified in the body overrides the `opt_` one from URL parameter. List of extra fields to include in response. Options Provides the response in "pretty" output.  In case of JSON this means doing proper line breaking and indentation to make it readable.  This will take extra time and increase the response size so it is advisable to use this only during debugging. Returns the output in JSON-P format instead of plain JSON. This allows requests to come from within browsers and work around the "same origin policy." The function named as the value of the `opt_jsonp` parameter will be called with a single argument, a JavaScript object representing the response. These options can be used in different combinations in a single request, though some of them may conflict in their impact on the response. `?opt_fields=comma,separated,field,list` `?opt_jsonp=myCallback` `?opt_pretty` `options: { pretty: true }` Project-Id-Version: openprocurement.api 0.1
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-11-04 09:37+0200
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.4.0
 In addition to providing fields and their values in a request, you may also specify options to control how your request is interpreted and how the response is generated.  For GET requests, options are specified as URL parameters prefixed with `opt_`.  For POST or PUT requests, options are specified in the body, inside the top-level options object (a sibling of the data object).  The option specified in the body overrides the `opt_` one from URL parameter. List of extra fields to include in response. Options Provides the response in "pretty" output.  In case of JSON this means doing proper line breaking and indentation to make it readable.  This will take extra time and increase the response size so it is advisable to use this only during debugging. Returns the output in JSON-P format instead of plain JSON. This allows requests to come from within browsers and work around the "same origin policy." The function named as the value of the `opt_jsonp` parameter will be called with a single argument, a JavaScript object representing the response. These options can be used in different combinations in a single request, though some of them may conflict in their impact on the response. `?opt_fields=comma,separated,field,list` `?opt_jsonp=myCallback` `?opt_pretty` `options: { pretty: true }` 