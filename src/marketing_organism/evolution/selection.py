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

    def calculate_diversity_score(self, target_genome: StrategyGenome) -> float:
        """Calculates how unique a genome is compared to the rest of the population."""
        if len(self.population) <= 1:
            return 1.0

        diversity_sum = 0.0
        for genome_id, other_genome in self.population.items():
            if genome_id == target_genome.genome_id:
                continue

            # Simple Euclidean distance equivalent for objective_weights to represent structural diversity
            target_weights = target_genome.genes.get("objective_weights", [])
            other_weights = other_genome.genes.get("objective_weights", [])

            if len(target_weights) == len(other_weights) and len(target_weights) > 0:
                dist = sum((a - b) ** 2 for a, b in zip(target_weights, other_weights)) ** 0.5
                diversity_sum += dist

        return diversity_sum / (len(self.population) - 1)

    def reallocate_resources(self, min_threshold: float = 0.3, diversity_weight: float = 0.2):
        """Eliminates low-performing strategies, retaining those that preserve diversity."""
        def combined_score(genome):
            fitness = genome.current_fitness
            diversity = self.calculate_diversity_score(genome)
            return (fitness * (1 - diversity_weight)) + (diversity * diversity_weight)

        ranked_genomes = sorted(
            self.population.items(),
            key=lambda x: combined_score(x[1]),
            reverse=True
        )

        underperforming = [g_id for g_id, genome in ranked_genomes if combined_score(genome) < min_threshold and len(genome.fitness_history) >= 5]

        for g_id in underperforming:
            # Terminate and remove
            del self.population[g_id]
            if g_id in self.performance_metrics:
                del self.performance_metrics[g_id]

        # In a full system, you would proportionally map the remaining genomes to available resources

    def spawn_generation(self, mutation_rate: float = 0.1, crossover_prob: float = 0.3, diversity_weight: float = 0.2):
        """Create a new generation from top performers via mutation and crossover."""
        if not self.population:
            return

        def combined_score(genome):
            fitness = genome.current_fitness
            diversity = self.calculate_diversity_score(genome)
            return (fitness * (1 - diversity_weight)) + (diversity * diversity_weight)

        ranked_genomes = sorted(
            self.population.values(),
            key=lambda g: combined_score(g),
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
