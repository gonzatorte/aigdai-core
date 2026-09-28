# OpenAIRE

Survey of the [OpenAIRE Graph](https://api.openaire.eu/graph/v1/) organizations API: the query
parameters, how to look an organization up by its ROR and a sample response. It is all in the
comments of `__init__.py`.

**This module is not in use and does not run as written.** Nothing imports it, it has no entry
point, and `fetch_single_org_page` raises `TypeError` on the first call. It is kept on purpose as
the starting point for integrating and reconciling data with OpenAIRE, which is described in
[`tech-debt.md`](../tech-debt.md), section 3.
