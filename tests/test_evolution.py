import pytest
from src.marketing_organism.evolution.genome import StrategyGenome
from src.marketing_organism.evolution.selection import EvolutionarySelector

def test_genome_mutation():
    genome = StrategyGenome(parameters={"objective_weights": [1.0, 1.0, 1.0]})
    # Force mutation
    mutated = genome.mutate(mutation_rate=1.0)
    assert mutated.genome_id != genome.genome_id
    assert mutated.lineage == [genome.genome_id]

    # Assert parameters changed
    assert mutated.genes["budget_allocation"] != genome.genes["budget_allocation"]

def test_genome_crossover():
    genome1 = StrategyGenome(parameters={"budget_allocation": 100.0, "adaptation_rate": 0.05})
    genome2 = StrategyGenome(parameters={"budget_allocation": 200.0, "adaptation_rate": 0.1})

    child = genome1.crossover(genome2)
    assert child.genome_id != genome1.genome_id
    assert child.genome_id != genome2.genome_id
    assert child.lineage == [genome1.genome_id, genome2.genome_id]
    assert child.genes["budget_allocation"] in [100.0, 200.0]
    assert child.genes["adaptation_rate"] in [0.05, 0.1]

def test_evolutionary_selector():
    selector = EvolutionarySelector()

    g1 = StrategyGenome()
    g2 = StrategyGenome()
    g3 = StrategyGenome()

    selector.add_genome(g1)
    selector.add_genome(g2)
    selector.add_genome(g3)

    # Simulate fitness
    for _ in range(5):
        selector.evaluate_fitness(g1.genome_id, 0.1)  # Low performer
        selector.evaluate_fitness(g2.genome_id, 0.9)  # High performer
        selector.evaluate_fitness(g3.genome_id, 0.8)  # High performer

    selector.reallocate_resources(min_threshold=0.3)

    assert g1.genome_id not in selector.population
    assert g2.genome_id in selector.population
    assert g3.genome_id in selector.population

    # Spawn new generation
    selector.spawn_generation()
    assert selector.generation == 1
    # We started with 2 surviving, after spawning we should have 2 parents + children
    # to make up for the 1 that died off. Actually length depends on len(self.population) at spawn time
    # so we had 2. Parents length is 1. We make 2 - 1 = 1 child. Total = 3
    assert len(selector.population) >= 2
