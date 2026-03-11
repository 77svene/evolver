import uuid
import random
import copy
import hashlib
import json
from typing import Dict, Any

class StrategyGenome:
    def __init__(self, parameters: Dict[str, Any] = None, lineage: list = None):
        self.genome_id = str(uuid.uuid4())
        self.parameters = parameters or {}
        # Core genes representation
        self.genes = {
            "objective_weights": self.parameters.get("objective_weights", [1.0, 0.5, 0.2]),
            "audience_targeting": self.parameters.get("audience_targeting", ["segment_a"]),
            "budget_allocation": self.parameters.get("budget_allocation", 100.0),
            "adaptation_rate": self.parameters.get("adaptation_rate", 0.05)
        }
        self.fitness_history = []
        self.lineage = lineage or []
        self.cryptographic_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = {
            "genome_id": self.genome_id,
            "genes": self.genes,
            "lineage": self.lineage
        }
        encoded = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def mutate(self, mutation_rate: float = 0.1):
        """Randomly alters a subset of parameters."""
        mutated_genes = copy.deepcopy(self.genes)

        # Simple point mutations
        for i in range(len(mutated_genes["objective_weights"])):
            if random.random() < mutation_rate:
                mutated_genes["objective_weights"][i] += random.uniform(-0.1, 0.1)

        if random.random() < mutation_rate:
            mutated_genes["budget_allocation"] *= random.uniform(0.9, 1.1)

        if random.random() < mutation_rate:
            mutated_genes["adaptation_rate"] = max(0.01, mutated_genes["adaptation_rate"] + random.uniform(-0.02, 0.02))

        offspring = StrategyGenome(parameters=mutated_genes, lineage=self.lineage + [self.cryptographic_hash])
        return offspring

    def crossover(self, other_genome: 'StrategyGenome') -> 'StrategyGenome':
        """Combines genes from self and another genome."""
        child_genes = {}

        # Pick traits from parent 1 or 2
        for key in self.genes:
            if random.random() < 0.5:
                child_genes[key] = copy.deepcopy(self.genes[key])
            else:
                child_genes[key] = copy.deepcopy(other_genome.genes[key])

        offspring = StrategyGenome(parameters=child_genes, lineage=[self.cryptographic_hash, other_genome.cryptographic_hash])
        return offspring

    def update_fitness(self, score: float):
        self.fitness_history.append(score)

    @property
    def current_fitness(self) -> float:
        if not self.fitness_history:
            return 0.0
        return sum(self.fitness_history[-5:]) / len(self.fitness_history[-5:])
