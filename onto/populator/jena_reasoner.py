"""Materialization of the graph with the Jena OWL reasoner, outside Fuseki.

It uses the rules of the reasoner that the allservice endpoint of Fuseki uses (OWLFBRuleReasoner, etc/owl-fb.rules of
the same Jena version, reasoner/jena), minus the equality rules, run once per population in the JVM of the populator
(see onto/populator/owlapi.py) with REASONER_HEAP of heap.

Why without equality: with the owl:sameAs between repositories, the backward rules of equality (sameAs6/7, equality1,
the functional properties) make the closure explode. On the whole graph (731,242 triples) the full rule set did not
finish in 30 minutes, while without them the closure takes about 30 s (27 s with 4 GB of heap, 37 s with 16 GB). The
equality is settled before Jena anyway (reconcile_repositories, or HermiT with --dl-reasoner), and not propagating
it keeps each catalog's values on its own record, which is what the provenance needs. The result (asserted plus inferred triples) is loaded into a dataset without reasoner, like
with_data, so queries do not pay for the reasoning and there is no deduction cache in Fuseki that becomes stale when
the data changes.

The graph goes in with the schema: the rules read the TBox from the same graph.
"""
import logging
import os
import time

from rdflib import Graph

from onto.populator.owlapi import start_jvm

logger = logging.getLogger('populate')


def materialize(graph: Graph, staging: str) -> str:
    """Writes to staging/closure.nt the asserted plus inferred triples of the graph, and returns that path."""
    start_jvm()
    from java.io import BufferedOutputStream, FileOutputStream
    from org.apache.jena.rdf.model import ModelFactory
    from org.apache.jena.riot import Lang, RDFDataMgr

    graph_path = os.path.join(staging, 'graph.nt')
    closure_path = os.path.join(staging, 'closure.nt')
    graph.serialize(destination=graph_path, format='nt', encoding='utf-8')

    started = time.perf_counter()
    model = RDFDataMgr.loadModel(graph_path)
    inferred = ModelFactory.createInfModel(owl_reasoner_without_equality(), model)
    inferred.prepare()
    logger.info('jena reasoner (owl-fb rules without equality): %s triples in, prepared in %.1f s', model.size(), time.perf_counter() - started)

    started = time.perf_counter()
    out = BufferedOutputStream(FileOutputStream(closure_path))
    try:
        RDFDataMgr.write(out, inferred, Lang.NTRIPLES)
    finally:
        out.close()
    count, dropped = drop_blank_predicates(closure_path)
    logger.info('jena reasoner: %s triples out (%s inferred), %s with a blank node as predicate dropped, written in %.1f s',
                count, count - model.size(), dropped, time.perf_counter() - started)
    return closure_path


# Rules of etc/owl-fb.rules that reason with equality: owl:sameAs (symmetry, transitivity, reflexivity, copying the
# values of equal individuals), functional and inverse functional properties, and the owl:differentFrom of disjoint
# classes and owl:AllDifferent (distinctMembers expanded to one inequality per pair).
EQUALITY_RULES = {'sameAs1', 'sameAs2', 'sameAs6', 'sameAs7', 'equality1', 'equality2', 'equality3', 'fp1', 'ifp1',
                  'fpEarlyProp', 'ifpEarlyProp', 'distinct1', 'distinct2'}


def owl_reasoner_without_equality():
    """GenericRuleReasoner with the rules of OWLFBRuleReasoner minus EQUALITY_RULES, configured like it (hybrid mode,
    OWL translation hooks and cached transitive closure of the class and property hierarchies)."""
    start_jvm()
    from java.util import ArrayList
    from org.apache.jena.reasoner.rulesys import GenericRuleReasoner, Rule
    rules = ArrayList()
    for rule in Rule.rulesFromURL('etc/owl-fb.rules'):
        if rule.getName() not in EQUALITY_RULES:
            rules.add(rule)
    reasoner = GenericRuleReasoner(rules)
    reasoner.setMode(GenericRuleReasoner.HYBRID)
    reasoner.setOWLTranslation(True)
    reasoner.setTransitiveClosureCaching(True)
    return reasoner


def drop_blank_predicates(path: str) -> tuple[int, int]:
    """Removes from an N-Triples file the triples whose predicate is a blank node. Returns (kept, dropped).

    RDF does not allow them and tdb2.tdbloader rejects them, but the Jena rules produce them: the anonymous inverse
    properties of the TBox (ObjectInverseOf, in the property chains and the HasKey) are blank nodes with
    owl:inverseOf, and rule inverseOf2 gives them values. They are the values of the named property reversed, so
    nothing is lost.
    """
    kept = dropped = 0
    filtered_path = path + '.filtered'
    with open(path, encoding='utf-8') as source, open(filtered_path, 'w', encoding='utf-8') as target:
        for line in source:
            # Jena writes one triple per line, with its terms separated by a single space: the second is the predicate
            parts = line.split(' ', 2)
            if len(parts) > 1 and parts[1].startswith('_:'):
                dropped += 1
            else:
                kept += 1
                target.write(line)
    os.replace(filtered_path, path)
    return kept, dropped
