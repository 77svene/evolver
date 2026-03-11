import random
from typing import Dict, List
from .genome import StrategyGenome

class EvolutionarySelector:
    def __init__(self):
        self.population: Dict[str, StrategyGenome] = {}
        self.performance_metrics: Dict[str, float] = {}
        self.generation: int = 0

    def add_genome(self, genome: StrategyGenome):
        self.population[genome.genome_id] = genome

    def evaluate_fitness(self, genome_id: str, metric: float):
        """Update fitness score for a specific genome based on its recent performance."""
        if genome_id in self.population:
            genome = self.population[genome_id]
            genome.update_fitness(metric)
            self.performance_metrics[genome_id] = genome.current_fitness

    def reallocate_resources(self, min_threshold: float = 0.3):
        """Eliminates low-performing strategies and reallocates resources to high performers."""
        ranked_genomes = sorted(
            self.population.items(),
            key=lambda x: x[1].current_fitness,
            reverse=True
        )

        underperforming = [g_id for g_id, genome in ranked_genomes if genome.current_fitness < min_threshold and len(genome.fitness_history) >= 5]

        for g_id in underperforming:
            # Terminate and remove
            del self.population[g_id]
            if g_id in self.performance_metrics:
                del self.performance_metrics[g_id]

        # In a full system, you would proportionally map the remaining genomes to available resources

    def spawn_generation(self, mutation_rate: float = 0.1, crossover_prob: float = 0.3):
        """Create a new generation from top performers via mutation and crossover."""
        if not self.population:
            return

        ranked_genomes = sorted(
            self.population.values(),
            key=lambda g: g.current_fitness,
            reverse=True
        )

        # Retain top 50%
        parents = ranked_genomes[:max(1, len(ranked_genomes) // 2)]

        new_offspring = []
        for _ in range(len(self.population) - len(parents)):
            parent1 = parents[0]  # simplified selection (e.g., top parent)
            if len(parents) > 1 and random.random() < crossover_prob:
                parent2 = random.choice(parents[1:])
                child = parent1.crossover(parent2)
            else:
                child = parent1.mutate(mutation_rate)
            new_offspring.append(child)

        for child in new_offspring:
            self.add_genome(child)

        self.generation += 1
