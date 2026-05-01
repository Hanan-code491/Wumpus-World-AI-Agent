import random
from typing import List, Tuple, Dict, Any

class World:
    def __init__(self, width: int, height: int, num_pits: int = None):
        self.width = width
        self.height = height
        self.pits = set()
        self.wumpus = None
        self.gold = None
        self.agent_pos = (0, 0)
        
        if num_pits is None:
            # roughly 20% pits
            num_pits = int(0.2 * width * height)
            
        self._generate_hazards(num_pits)

    def _generate_hazards(self, num_pits: int):
        all_cells = [(x, y) for x in range(self.width) for y in range(self.height)]
        # (0, 0) is always safe — agent starts here.
        safe_cells = {(0, 0)}
        available_cells = [c for c in all_cells if c not in safe_cells]
        
        # Place Wumpus
        if available_cells:
            self.wumpus = random.choice(available_cells)
            available_cells.remove(self.wumpus)
        
        # Place Pits
        for _ in range(min(num_pits, len(available_cells))):
            pit = random.choice(available_cells)
            self.pits.add(pit)
            available_cells.remove(pit)

        # Place Gold — must be on a cell that is reachable (not Wumpus/Pit) and not (0,0)
        # Choose from cells not occupied by hazards
        safe_for_gold = [c for c in available_cells if c not in self.pits and c != self.wumpus]
        if safe_for_gold:
            self.gold = random.choice(safe_for_gold)
        elif available_cells:
            # fallback: any remaining cell
            self.gold = random.choice(available_cells)

    def get_percepts(self, pos: Tuple[int, int]) -> Dict[str, bool]:
        breeze = False
        stench = False
        glitter = False
        
        x, y = pos
        neighbors = self.get_neighbors(x, y)
        
        for nx, ny in neighbors:
            if (nx, ny) in self.pits:
                breeze = True
            if (nx, ny) == self.wumpus:
                stench = True

        # Glitter at the cell itself (not neighbours)
        if pos == self.gold:
            glitter = True
                
        return {"breeze": breeze, "stench": stench, "glitter": glitter}

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        neighbors = []
        if x > 0: neighbors.append((x - 1, y))
        if x < self.width - 1: neighbors.append((x + 1, y))
        if y > 0: neighbors.append((x, y - 1))
        if y < self.height - 1: neighbors.append((x, y + 1))
        return neighbors

    def get_state(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "pits": [{"x": p[0], "y": p[1]} for p in self.pits],
            "wumpus": {"x": self.wumpus[0], "y": self.wumpus[1]} if self.wumpus else None,
            "gold": {"x": self.gold[0], "y": self.gold[1]} if self.gold else None,
            "agent_pos": {"x": self.agent_pos[0], "y": self.agent_pos[1]}
        }
