.. Kicking page rebuild 2014-10-30 17:00:08
.. _complaints:


..
    contents:: Table of Contents
   :depth: 2
   :local:

Complaint Workflow
==================

For more detailed information read `Complaints <http://openprocurement.org/en/complaints.html>`_.

Tender Conditions Claims/Complaints
-----------------------------------

.. toctree::
    :maxdepth: 1

    complaints-tender

Tender Award Claims/Complaints
------------------------------

.. toctree::
    :maxdepth: 1

    complaints-award


Workflow
--------

.. graphviz::

    digraph G {
        claim -> answered;
        edge[style=dashed];
        draft -> claim; 
        answered -> resolved;
        {draft,claim,answered} -> cancelled; 
        edge[label="3d" style=dotted];
        answered -> {resolved, invalid, declined};
        edge[label="complete" style=dotted];
        claim -> ignored;
        edge[label="auto" style=dotted];
        pending -> ignored;
        pending -> {resolved, invalid, declined};
    }


Roles
-----

:Complainant:
    dashed

:Procuring entity:
    plain

:Chronograph:
    dotted

Statuses
--------

:draft:
    Initial status

    Complainant can submit claim, upload documents, cancel claim, and re-submit it.

:claim:
    Procuring entity can upload documents and answer to claim.

    Complainant can cancel claim.

:answered:
    Complainant can cancel claim, upload documents, agree or disagree with decision.

:pending:
    Reviewer can upload documents and review complaint.

    Complainant can cancel claim.

:invalid:
    Terminal status

    Claim recognized as invalid.

:declined:
    Terminal status

    Claim recognized as declined.

:resolved:
    Terminal status

    Claim recognized as resolved.

:cancelled:
    Terminal status

    Claim cancelled by complainant.

:ignored:
    Terminal status

    Claim ignored by procuring entity.
