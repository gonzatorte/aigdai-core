import typing
import httpx
import rdflib
from config import JENA_BASE_PATH

# from rdflib.plugins.sparql import prepareUpdate

NodeT = rdflib.term.URIRef | rdflib.term.Literal

def node_to_string(aa: NodeT):
    # return aa.n3() if isinstance(aa, rdflib.term.URIRef) else '"%s"' % aa.value
    return aa.n3()

class JenaClient:
    def __init__(self, dataset: str, init_ns):
        self.http_client = httpx.AsyncClient()
        self.dataset = dataset
        self.initNs = init_ns

    async def __aenter__(self):
        await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def insert_many(self, items: typing.List[typing.Tuple[NodeT, rdflib.term.URIRef, NodeT]]):
        dd = ["%s %s %s ." % (node_to_string(a[0]), node_to_string(a[1]), node_to_string(a[2])) for a in items]
# PREFIX ns:   <http://www.example.org/ns#>
# PREFIX owl:  <http://www.w3.org/2002/07/owl#>
# PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# INSERT DATA {
#    GRAPH <http://example/shelf_A> {
#        <http://example/author> dcterms:name "author" .
#    }
# }
        qq = """
INSERT DATA {
%s
}
""" % ('\n'.join(dd), )
        # qqp = prepareUpdate(
        #     updateString=qq,
        #     initNs=self.initNs,
        # )
        # qqt = quote(qq)
        endpoint = "%s%s" % (JENA_BASE_PATH, self.dataset,)
        response = await self.http_client.post(
            endpoint,
            timeout=20,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain,*/*;q=0.9',
            },
            # data={'update': qqt},
            data = {'update': qq},
        )
        if response.status_code != 200:
            raise Exception()
