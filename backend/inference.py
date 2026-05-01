from typing import Set, Tuple, List, FrozenSet

Literal = Tuple[str, Tuple[int, int], bool]
Clause = FrozenSet[Literal]

def resolve(ci: Clause, cj: Clause) -> Set[Clause]:
    resolvents = set()
    for l1 in ci:
        l2 = (l1[0], l1[1], not l1[2])
        if l2 in cj:
            new_clause = set(ci).union(set(cj))
            new_clause.remove(l1)
            new_clause.remove(l2)
            # if a clause contains a literal and its negation, it's a tautology, ignore it
            is_tautology = False
            for lit in new_clause:
                if (lit[0], lit[1], not lit[2]) in new_clause:
                    is_tautology = True
                    break
            if not is_tautology:
                resolvents.add(frozenset(new_clause))
    return resolvents

def pl_resolution(kb_clauses: Set[Clause], alpha_clauses: Set[Clause]) -> Tuple[bool, int]:
    """
    Returns (is_entailed, number_of_steps)
    """
    clauses = set(kb_clauses).union(set(alpha_clauses))
    new = set()
    steps = 0
    
    while True:
        steps += 1
        clauses_list = list(clauses)
        n = len(clauses_list)
        
        # pairs to resolve
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((clauses_list[i], clauses_list[j]))
        
        for ci, cj in pairs:
            resolvents = resolve(ci, cj)
            if frozenset() in resolvents:
                return True, steps
            new = new.union(resolvents)
            
        if new.issubset(clauses):
            return False, steps
            
        clauses = clauses.union(new)
        # to prevent infinite explosion in larger grids, let's limit steps
        if steps > 500:
            return False, steps
