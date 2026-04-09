import pytest
from src.marketing_organism.evolution.genome import StrategyGenome
from src.marketing_organism.evolution.selection import EvolutionarySelector

def test_genome_mutation():
    genome = StrategyGenome(parameters={"objective_weights": [1.0, 1.0, 1.0]})
    # Force mutation
    mutated = genome.mutate(mutation_rate=1.0)
    assert mutated.genome_id != genome.genome_id
    assert mutated.lineage == [genome.cryptographic_hash]

    # Assert parameters changed
    assert mutated.genes["budget_allocation"] != genome.genes["budget_allocation"]

def test_genome_crossover():
    genome1 = StrategyGenome(parameters={"budget_allocation": 100.0, "adaptation_rate": 0.05})
    genome2 = StrategyGenome(parameters={"budget_allocation": 200.0, "adaptation_rate": 0.1})

    child = genome1.crossover(genome2)
    assert child.genome_id != genome1.genome_id
    assert child.genome_id != genome2.genome_id
    assert child.lineage == [genome1.cryptographic_hash, genome2.cryptographic_hash]
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
    assert len(selector.population) >= 2

def test_evolutionary_diversity():
    selector = EvolutionarySelector()

    # 3 identical genomes, 1 distinct genome
    g1 = StrategyGenome(parameters={"objective_weights": [1.0, 1.0, 1.0]})
    g2 = StrategyGenome(parameters={"objective_weights": [1.0, 1.0, 1.0]})
    g3 = StrategyGenome(parameters={"objective_weights": [1.0, 1.0, 1.0]})

    # This one is very structurally different
    g4_distinct = StrategyGenome(parameters={"objective_weights": [10.0, 10.0, 10.0]})

    selector.add_genome(g1)
    selector.add_genome(g2)
    selector.add_genome(g3)
    selector.add_genome(g4_distinct)

    div_1 = selector.calculate_diversity_score(g1)
    div_4 = selector.calculate_diversity_score(g4_distinct)

    # Distinct genome should have a much higher diversity score
    assert div_4 > div_1
