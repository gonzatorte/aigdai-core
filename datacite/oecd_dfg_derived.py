# OECD FOS fields contained in a DFG 2014 node. Derived by us from oecd_dfg_mapping.py, not stated by its source: if the
#  crosswalk covers a field, the field is contained in the smallest DFG node that holds every DFG code mapped to it.
#  Left out: FOS areas, fields whose DFG codes span several DFG areas, fields whose covering node is a single DFG
#  subject (one or two subjects mapped, too little to infer containment) and the "Other ..." catch-all fields:
#  - 1.2: spans several DFG areas
#  - 1.3: spans several DFG areas
#  - 1.6: spans several DFG areas
#  - 2.4: spans several DFG areas
#  - 2.5: spans several DFG areas
#  - 2.6: covering node is the subject 20507
#  - 2.7: spans several DFG areas
#  - 2.11: covering node is the subject 20707
#  - 3.4: covering node is the subject 20532
#  - 3.5: covering node is the subject 20506
#  - 4.5: catch-all field, covering node 207
#  - 5: a FOS area, mapped by the wrong 111 row
#  - 5.7: spans several DFG areas
#  - 5.8: covering node is the subject 11103
#  - 5.9: covering node is the subject 11102
#  - 6.5: catch-all field, covering node 106
# Columns: OECD_notation_2007	OECD_name_2007	DFG_notation_2014	DFG_name_2014
mapping = [
    ("1.1","Mathematics","312","Mathematics"),
    ("1.4","Chemical sciences","3","Natural Sciences"),
    ("1.5","Earth and related environmental sciences","34","Geosciences (including Geography)"),
    ("2.1","Civil engineering","4","Engineering Sciences"),
    ("2.2","Electrical engineering, electronic engineering, information engineering","4","Engineering Sciences"),
    ("2.3","Mechanical engineering","4","Engineering Sciences"),
    ("2.9","Industrial biotechnology","4","Engineering Sciences"),
    ("3.1","Basic medicine","2","Life Sciences"),
    ("3.2","Clinical medicine","22","Medicine"),
    ("3.3","Health sciences","22","Medicine"),
    ("4.1","Agriculture, forestry, and fisheries","207","Agriculture, Forestry, Horticulture and Veterinary Medicine"),
    ("4.2","Animal and dairy science","207","Agriculture, Forestry, Horticulture and Veterinary Medicine"),
    ("4.3","Veterinary science","207","Agriculture, Forestry, Horticulture and Veterinary Medicine"),
    ("5.1","Psychology","110","Psychology"),
    ("5.2","Economics and business","112","Economics"),
    ("5.3","Educational sciences","12","Social and Behavioural Sciences"),
    ("5.4","Sociology","1","Humanities and Social Sciences"),
    ("5.5","Law","113","Jurisprudence"),
    ("5.6","Political science","12","Social and Behavioural Sciences"),
    ("6.1","History and archaeology","11","Humanities"),
    ("6.2","Languages and literature","11","Humanities"),
    ("6.3","Philosophy, ethics and religion","11","Humanities"),
    ("6.4","Art (arts, history of arts, performing arts, music)","103","Fine Arts, Music, Theatre and Media Studies"),
]
