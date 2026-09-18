import * as lodash from 'lodash';

const BASE_API_URL = process.env.SPARQL_API_URL!;
// const BASE_API_URL = 'http://localhost:3030/allservice/';
// const BASE_ONTO_URL = 'http://aigdai-tbox.owl/';
// const BASE_SCHEMA_URL = `${BASE_ONTO_URL}#/`;
export const BASE_ONTO_PREFIX_RE = 'http://aigdai.';
const BASE_ONTO_URL = 'http://aigdai.tbox.owl/';
const BASE_CRITERIA_ONTO_URL = 'http://aigdai.criterios.owl/';
const BASE_SCHEMA_URL = BASE_ONTO_URL;

function shortenUri(uri: string) {
  return uri.replace(BASE_ONTO_URL, '').replace(BASE_CRITERIA_ONTO_URL, '');
}

function shortenSchemaUri(uri: string) {
  console.log(uri);
  return uri.replace(BASE_SCHEMA_URL, '').replace(BASE_CRITERIA_ONTO_URL, '');
}

async function apiAlter(query: string): Promise<void> {
  const rr = await fetch(BASE_API_URL, {
    headers: {
      accept: 'application/sparql-results+json,*/*;q=0.9',
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: `query=${encodeURIComponent(`PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dai: <${BASE_ONTO_URL}>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
${query}`)}`,
    method: 'POST',
  });
  if (rr.status !== 200) {
    throw new Error('Failed to fetch data');
  }
}

export const COMMON_PREFIXES = `
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dai: <${BASE_ONTO_URL}>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
`;

async function apiQuery<T = any>(query: string): Promise<T[]> {
  const rr = await fetch(BASE_API_URL, {
    headers: {
      accept: 'application/sparql-results+json,*/*;q=0.9',
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: `query=${encodeURIComponent(`${COMMON_PREFIXES}${query}`)}`,
    method: 'POST',
  });
  if (rr.status !== 200) {
    throw new Error('Failed to fetch data');
  }
  const data = await rr.json();
  return data.results.bindings;
}

type BindingValue = { value: string };

export async function getLinksHierarqy() {
  const data = await apiQuery<{ p: BindingValue; h: BindingValue }>(`
SELECT * WHERE
{
{
SELECT ?p ?h
WHERE {
  ?h rdfs:subPropertyOf ?p .
  ?p rdf:type+ owl:ObjectProperty .
  FILTER (?h != ?p) .
  FILTER regex(STR(?h), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
#  FILTER NOT EXISTS {
#    ?h rdf:type+ owl:DatatypeProperty
#  }
} ORDER BY ASC(?h) ASC(?p)
}
UNION
{
SELECT ?p ?h
WHERE {
  ?h rdf:type owl:ObjectProperty .
  FILTER NOT EXISTS {
    ?h rdfs:subPropertyOf ?hh .
    FILTER (?h != ?hh) .
  }
  FILTER regex(STR(?h), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  BIND(owl:ObjectProperty AS ?p) .
} ORDER BY ASC(?h) ASC(?p)
}
}
`);
  const aa = data.map(({ p, h }) => ({
    p:
      p.value === 'http://www.w3.org/2002/07/owl#ObjectProperty'
        ? null
        : shortenSchemaUri(p.value),
    h: shortenSchemaUri(h.value),
  }));
  return aa;
}

export async function getDataProps() {
  const data = await apiQuery<{
    d: BindingValue;
    rr: BindingValue;
    domain: BindingValue;
  }>(`
SELECT *
{
{
SELECT ?d ?rr ?domain
WHERE {
  ?d rdf:type+ owl:DatatypeProperty .
  ?d rdfs:domain ?domain .
  ?d rdfs:range ?rr .
  FILTER regex(STR(?domain), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  FILTER regex(STR(?rr), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
} ORDER BY ASC(?d) ASC(?domain)
}
UNION
{
SELECT ?d ?rr ?domain
WHERE {
  ?d rdf:type+ owl:DatatypeProperty .
  ?d rdfs:domain ?domain .
  ?d rdfs:range ?rr .
  FILTER regex(STR(?domain), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  FILTER regex(STR(?rr), "^http://www.w3.org/2001/XMLSchema#+", "i") .
} ORDER BY ASC(?d) ASC(?domain)
}
}
`);
  const aa = data.map(({ d, domain }) => ({
    d: shortenSchemaUri(d.value),
    domain: shortenSchemaUri(domain.value),
  }));
  return aa;
}

export async function getObjectProps() {
  const data = await apiQuery<{
    pp: BindingValue;
    dd: BindingValue;
    rr: BindingValue;
  }>(`
  SELECT ?pp ?dd ?rr
  WHERE {
    ?pp rdf:type+ owl:ObjectProperty .
    ?pp rdfs:domain ?dd .
    ?pp rdfs:range ?rr .
    FILTER regex(STR(?dd), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
    FILTER regex(STR(?rr), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  }
  `);
  const aa = data.map(({ pp, dd, rr }) => ({
    pp: shortenSchemaUri(pp.value),
    dd: shortenSchemaUri(dd.value),
    rr: shortenSchemaUri(rr.value),
  }));
  return aa;
}

export async function getNodesHierarqy() {
  // ?h rdfs:subClassOf ?p .
  // ?p rdfs:subClassOf* owl:Thing .
  // FILTER regex(STR(?h), "^${BASE_SCHEMA_URL}.+", "i") .
  const data = await apiQuery<{ p: BindingValue; h: BindingValue }>(`
SELECT * WHERE
{
{
SELECT ?p ?h
WHERE {
  ?h rdfs:subClassOf ?p .
  FILTER (?h != ?p) .
  FILTER regex(STR(?h), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
} ORDER BY ASC(?h) ASC(?p)
}
UNION
{
SELECT ?p ?h
WHERE {
  ?h rdfs:subClassOf owl:Thing .
  FILTER NOT EXISTS {
    ?h rdfs:subClassOf ?hh .
    FILTER regex(STR(?hh), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
    FILTER (?h != ?hh) .
  }
  FILTER regex(STR(?h), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  BIND(owl:Thing AS ?p) .
} ORDER BY ASC(?h) ASC(?p)
}
}
`);
  const aa = data.map(({ p, h }) => ({
    p:
      p.value === 'http://www.w3.org/2002/07/owl#Thing'
        ? null
        : shortenSchemaUri(p.value),
    h: shortenSchemaUri(h.value),
  }));
  return aa;
}

export async function searchEntity(
  className: string,
  nameType: string,
  term: string,
  nextTo?: string
) {
  const data = await apiQuery<{ o: BindingValue; n: BindingValue }>(`
SELECT ?o ?n
WHERE {
  ?o rdf:type+ dai:${className} .
  ?o dai:${nameType} ?n .
  ${term ? `FILTER regex(?n, "${term}", "i") .` : ''}
  ${nextTo ? `FILTER (STR(?o) > "${BASE_ONTO_URL}${nextTo}") .` : ''}
} ORDER BY ASC(?o) LIMIT 10`);
  const aa = Object.entries(
    lodash.groupBy(
      data.map(({ o, ...more }) => ({
        idd: shortenUri(o.value),
        ...more,
      })),
      ({ idd }) => idd
    )
  );
  return aa.map(([idd, oo]) => ({
    idd,
    name: oo.map(({ n }) => n.value).join(','),
  }));
}

export async function getNeighbors(source: string) {
  const qRelations = `
  SELECT ?p ?o
  WHERE {
    <${BASE_ONTO_URL}${source}> ?p ?o .
    FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  }`;
  const qInverseRelations = `
  SELECT ?p ?s
  WHERE {
    ?s ?p <${BASE_ONTO_URL}${source}> .
    ?p rdf:type+ owl:ObjectProperty .
    FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  }`;
  const qTypes = `
  SELECT ?type
  WHERE {
    <${BASE_ONTO_URL}${source}> rdf:type ?type .
    FILTER regex(STR(?type), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  }`;
  const [types, relations, inverseRelations] = await Promise.all([
    apiQuery<{ type: BindingValue }>(qTypes),
    apiQuery<{ p: BindingValue; o: BindingValue }>(qRelations),
    apiQuery<{ p: BindingValue; s: BindingValue }>(qInverseRelations),
  ]);
  return {
    types: types.map(({ type }) => shortenUri(type.value)),
    relations: relations.map(({ p, o }) => ({
      p: shortenUri(p.value),
      o: shortenUri(o.value),
    })),
    inverseRelations: inverseRelations.map(({ p, s }) => ({
      p: shortenUri(p.value),
      s: shortenUri(s.value),
    })),
  };
}

export async function getExistingRelations(objects: string[]) {
  const data = await apiQuery<{
    s: BindingValue;
    p: BindingValue;
    o: BindingValue;
  }>(`
SELECT * WHERE
{
{
SELECT ?s ?p ?o
WHERE {
  ?s ?p ?o .
#  ?p rdf:type+ owl:ObjectProperty .
  FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  VALUES ?s { ${objects.map((o) => `<${BASE_ONTO_URL}${o}>`).join(' ')} }
}
}
UNION
{
SELECT ?s ?p ?o
WHERE {
  ?s ?p ?o .
#  ?p rdf:type+ owl:ObjectProperty .
  FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
  VALUES ?o { ${objects.map((o) => `<${BASE_ONTO_URL}${o}>`).join(' ')} }
}
}
}
`);
  return data.map(({ s, p, o }) => ({
    o: shortenUri(o.value),
    s: shortenUri(s.value),
    p: shortenUri(p.value),
  }));
}

export async function deleteLinks(
  _links: { source: string; target: string; kind: string[] }[]
) {
  await apiAlter(`
    DELETE DATA {
      ?s ?p ?o .
    } WHERE {
      ?s ?p ?o .
    }
  `);
}

export async function deleteNodes(_nodes: { id: string; kind: string[] }[]) {
  // ToDo: Remove all links and nodes of those nodes
  await apiAlter(`
    DELETE DATA {
      ?s ?p ?o .
    } WHERE {
      ?s ?p ?o .
    }
  `);
}

export async function createNode(node: {
  id: string;
  kind: string[];
  dataProps: { name: string; value: string }[];
}) {
  await apiAlter(`
    INSERT DATA {
      ?s ?p ?o .
    }
  `);
}

export async function createLink(link: {
  id: string;
  kind: string[];
  source: string;
  target: string;
}) {
  await apiAlter(`
    INSERT DATA {
      ?s ?p ?o .
    }
  `);
}

export async function executeRawSparqlQuery(query: string) {
  const data = await apiQuery<{
    s: BindingValue;
    p: BindingValue;
    o: BindingValue;
  }>(`${COMMON_PREFIXES} SELECT ?s ?p ?o WHERE {
${query}
FILTER regex(STR(?s), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
FILTER regex(STR(?o), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
    }`);
  const instances = data.map(({ s, p, o }) => ({
    s: s.value,
    p: p.value,
    o: o.value,
  }));
  const objects = Array.from(
    new Set([...instances.map(({ s }) => s), ...instances.map(({ o }) => o)])
  );
  const qTypes = `
  SELECT ?s ?type
  WHERE {
    ?s rdf:type ?type .
    FILTER regex(STR(?type), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
    VALUES ?s { ${objects.map((o) => `<${o}>`).join(' ')} }
  }`;
  const typesByEntity = await apiQuery<{ s: BindingValue; type: BindingValue }>(
    qTypes
  );
  const typesByEntityMap = new Map(
    Object.entries(
      lodash.groupBy(
        typesByEntity.map(({ s, type }) => ({
          s: shortenSchemaUri(s.value),
          type: shortenSchemaUri(type.value),
        })),
        ({ s }) => s
      )
    ).map(([s, types]) => [s, types.map(({ type }) => type)])
  );
  return instances
    .map(({ s, p, o }) => ({
      s: shortenUri(s),
      p: shortenUri(p),
      o: shortenUri(o),
    }))
    .map(({ s, p, o }) => ({
      s: {
        value: s,
        types: typesByEntityMap.get(s) || [],
      },
      p,
      o: {
        value: o,
        types: typesByEntityMap.get(o) || [],
      },
    }));
}
