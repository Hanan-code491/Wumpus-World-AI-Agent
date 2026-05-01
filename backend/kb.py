from typing import Set, Tuple, List, FrozenSet
from inference import pl_resolution, Clause, Literal

class KnowledgeBase:
    def __init__(self):
        self.clauses: Set[Clause] = set()

    def tell_safe(self, pos: Tuple[int, int]):
        self.clauses.add(frozenset([("P", pos, False)]))
        self.clauses.add(frozenset([("W", pos, False)]))

    def tell_percepts(self, breeze: bool, stench: bool, neighbors: List[Tuple[int, int]]):
        if breeze:
            self.clauses.add(frozenset([("P", n, True) for n in neighbors]))
        else:
            for n in neighbors:
                self.clauses.add(frozenset([("P", n, False)]))
                
        if stench:
            self.clauses.add(frozenset([("W", n, True) for n in neighbors]))
        else:
            for n in neighbors:
                self.clauses.add(frozenset([("W", n, False)]))

    def ask_is_safe(self, pos: Tuple[int, int]) -> Tuple[bool, int]:
        ans_P, steps_P = pl_resolution(self.clauses, {frozenset([("P", pos, True)])})
        ans_W, steps_W = pl_resolution(self.clauses, {frozenset([("W", pos, True)])})
        return (ans_P and ans_W), (steps_P + steps_W)

    def ask_is_unsafe(self, pos: Tuple[int, int]) -> Tuple[bool, int]:
        ans_P, steps_P = pl_resolution(self.clauses, {frozenset([("P", pos, False)])})
        if ans_P:
            return True, steps_P
        ans_W, steps_W = pl_resolution(self.clauses, {frozenset([("W", pos, False)])})
        return ans_W, (steps_P + steps_W)
