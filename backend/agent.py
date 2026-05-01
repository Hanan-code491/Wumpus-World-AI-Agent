from world import World
from kb import KnowledgeBase
from typing import Dict, Any, Optional, Tuple
import random

class WumpusAgent:
    def __init__(self, world: World):
        self.world = world
        self.kb = KnowledgeBase()
        self.pos = (0, 0)
        self.visited = set()
        self.visited.add(self.pos)
        self.safe_cells = set()
        self.safe_cells.add(self.pos)
        self.safe_unvisited = set()
        self.known_unsafe = set()
        self.unvisited_fringe = set()   # cells seen but not yet classified
        
        self.kb.tell_safe(self.pos)
        
        self.total_inference_steps = 0
        self.decisions_made = []
        self.game_over = False
        self.status = "Playing"
        self.has_gold = False

    def _classify_fringe(self):
        """Re-evaluate every fringe cell with current KB knowledge."""
        newly_safe = set()
        newly_unsafe = set()

        for n in list(self.unvisited_fringe):
            if n in self.safe_cells or n in self.known_unsafe:
                # already classified — remove from fringe
                newly_safe.add(n) if n in self.safe_cells else newly_unsafe.add(n)
                continue

            is_safe, steps = self.kb.ask_is_safe(n)
            self.total_inference_steps += steps

            if is_safe:
                self.safe_cells.add(n)
                self.safe_unvisited.add(n)
                newly_safe.add(n)
                self.decisions_made.append(f"Cell {n} is SAFE because it's entailed by KB.")
            else:
                is_unsafe, steps_u = self.kb.ask_is_unsafe(n)
                self.total_inference_steps += steps_u
                if is_unsafe:
                    self.known_unsafe.add(n)
                    newly_unsafe.add(n)
                    self.decisions_made.append(f"Cell {n} is UNSAFE (Pit/Wumpus).")
                else:
                    self.decisions_made.append(f"Cell {n} is UNKNOWN.")

        # Remove classified cells from fringe
        self.unvisited_fringe -= newly_safe
        self.unvisited_fringe -= newly_unsafe

    def process_percepts(self):
        percepts = self.world.get_percepts(self.pos)
        neighbors = self.world.get_neighbors(self.pos[0], self.pos[1])

        self.kb.tell_percepts(percepts['breeze'], percepts['stench'], neighbors)

        # Check for gold via glitter percept
        if percepts.get('glitter'):
            self.has_gold = True
            self.decisions_made.append(f"GLITTER DETECTED — GOLD PICKED UP at {self.pos}! Heading back to (0,0).")

        # Add new unclassified neighbors to the fringe
        for n in neighbors:
            if n not in self.visited and n not in self.safe_cells and n not in self.known_unsafe:
                self.unvisited_fringe.add(n)

        # Re-classify the whole fringe with updated KB
        self._classify_fringe()

        return percepts

    def _find_path_to(self, target: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """BFS over *visited safe* cells to find the next step toward target."""
        if self.pos == target:
            return None
        from collections import deque
        queue = deque([(self.pos, [])])
        seen = {self.pos}
        while queue:
            cur, path = queue.popleft()
            for nb in self.world.get_neighbors(cur[0], cur[1]):
                if nb in seen:
                    continue
                # Only traverse already-visited or confirmed-safe cells
                if nb not in self.safe_cells:
                    continue
                seen.add(nb)
                new_path = path + [nb]
                if nb == target:
                    return new_path[0] if new_path else None
                queue.append((nb, new_path))
        return None

    def move(self) -> Dict[str, Any]:
        if self.game_over:
            return self.get_agent_state()

        percepts = self.process_percepts()

        # Death check on entry
        if self.pos in self.world.pits or self.pos == self.world.wumpus:
            self.game_over = True
            self.status = "Dead"
            self.decisions_made.append("Agent died!")
            return self.get_agent_state()

        # ── Win condition: picked up gold, now navigate back to (0,0) ──
        if self.has_gold:
            if self.pos == (0, 0):
                self.game_over = True
                self.status = "Won"
                self.decisions_made.append("Agent climbed out with the gold! YOU WIN!")
                return self.get_agent_state()
            # Navigate back via BFS over safe visited cells
            next_step = self._find_path_to((0, 0))
            if next_step:
                self.pos = next_step
                self.visited.add(next_step)
                self.world.agent_pos = self.pos
                self.decisions_made.append(f"Carrying gold, heading home via {next_step}.")
                return self.get_agent_state()

        # ── Normal exploration ──
        if self.safe_unvisited:
            next_pos = self.safe_unvisited.pop()
            self.pos = next_pos
            self.visited.add(next_pos)
            self.world.agent_pos = self.pos
            self.decisions_made.append(f"Moved to safe cell {next_pos}.")
        elif self.unvisited_fringe:
            # All remaining fringe cells are UNKNOWN — must gamble; pick one at random
            next_pos = random.choice(list(self.unvisited_fringe))
            self.unvisited_fringe.discard(next_pos)
            self.pos = next_pos
            self.visited.add(next_pos)
            self.world.agent_pos = self.pos
            self.decisions_made.append(f"No safe cell known. Moved to {next_pos} randomly.")
        else:
            self.decisions_made.append("No logical move exists. Stuck — agent explored all reachable safe cells.")
            self.game_over = True
            self.status = "Finished"

        # Death check after moving
        if not self.game_over:
            if self.pos in self.world.pits or self.pos == self.world.wumpus:
                self.game_over = True
                self.status = "Dead"
                self.decisions_made.append("Agent died!")

        return self.get_agent_state()

    def get_agent_state(self) -> Dict[str, Any]:
        return {
            "pos": {"x": self.pos[0], "y": self.pos[1]},
            "percepts": self.world.get_percepts(self.pos),
            "inference_steps": self.total_inference_steps,
            "decisions": self.decisions_made,
            "visited": [{"x": p[0], "y": p[1]} for p in self.visited],
            "safe_cells": [{"x": p[0], "y": p[1]} for p in self.safe_cells],
            "game_over": self.game_over,
            "status": self.status,
            "has_gold": self.has_gold
        }
