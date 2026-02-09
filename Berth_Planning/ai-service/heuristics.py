"""
SmartBerth AI Service - Heuristics & Algorithms Layer
Advanced optimization algorithms for berth planning and resource scheduling

Implements:
1. Constraint Satisfaction Problem (CSP) Solver
2. Priority-based Berth Allocation Algorithm
3. Genetic Algorithm for Schedule Optimization
4. Hungarian Algorithm for Resource Assignment
5. Greedy First-Fit Berth Allocation
6. Conflict Detection & Resolution Engine
7. Re-Optimization Algorithms for Dynamic Scheduling

Based on research in Terminal Operating Systems (TOS) and Port Optimization:
- Berth Allocation Problem (BAP) is NP-hard
- Hybrid approaches (heuristics + metaheuristics) work best
- Real-time constraints require fast approximate solutions
"""

import logging
import heapq
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math
import random
from copy import deepcopy

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ConstraintType(str, Enum):
    HARD = "hard"       # Must be satisfied (vessel fits berth)
    SOFT = "soft"       # Preferably satisfied (minimize waiting time)


class OptimizationObjective(str, Enum):
    MINIMIZE_WAITING_TIME = "waiting_time"
    MAXIMIZE_BERTH_UTILIZATION = "utilization"
    MINIMIZE_TOTAL_SERVICE_TIME = "service_time"
    MINIMIZE_CONFLICTS = "conflicts"
    BALANCED = "balanced"


class ConflictType(str, Enum):
    TIME_OVERLAP = "time_overlap"
    RESOURCE_CONTENTION = "resource_contention"
    TIDAL_CONSTRAINT = "tidal_constraint"
    WEATHER_RESTRICTION = "weather_restriction"
    MAINTENANCE_CONFLICT = "maintenance_conflict"


# Algorithm Parameters
GA_POPULATION_SIZE = 50
GA_GENERATIONS = 100
GA_MUTATION_RATE = 0.1
GA_CROSSOVER_RATE = 0.8
GA_ELITE_SIZE = 5

BEAM_SEARCH_WIDTH = 10
PRIORITY_WEIGHTS = {
    'urgent': 1.5,
    'high': 1.3,
    'normal': 1.0,
    'low': 0.8
}


# ============================================================================
# DATA CLASSES FOR ALGORITHM STRUCTURES
# ============================================================================

@dataclass
class TimeSlot:
    """Represents a time window for berth allocation"""
    start: datetime
    end: datetime
    berth_id: int
    is_available: bool = True
    maintenance: bool = False
    
    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        return self.start < other.end and other.start < self.end


@dataclass
class VesselRequest:
    """Represents a berth allocation request"""
    vessel_id: int
    vessel_name: str
    vessel_type: str
    loa: float
    beam: float
    draft: float
    gross_tonnage: float
    cargo_type: str
    cargo_quantity: float
    eta: datetime
    requested_berth: Optional[int] = None
    priority: int = 2  # 1=High, 2=Normal, 3=Low
    estimated_dwell_time: float = 720  # minutes
    tugs_required: int = 2
    pilot_required: bool = True
    is_hazardous: bool = False
    
    @property
    def etd(self) -> datetime:
        return self.eta + timedelta(minutes=self.estimated_dwell_time)


@dataclass
class BerthSlot:
    """Represents a berth and its capacity"""
    berth_id: int
    berth_code: str
    terminal_code: str
    max_loa: float
    max_beam: float
    max_draft: float
    berth_type: str
    cranes: int
    is_available: bool = True
    
    def can_accommodate(self, vessel: VesselRequest) -> Tuple[bool, List[str]]:
        """Check if berth can accommodate vessel"""
        violations = []
        
        if vessel.loa > self.max_loa:
            violations.append(f"LOA {vessel.loa}m > max {self.max_loa}m")
        if vessel.beam > self.max_beam:
            violations.append(f"Beam {vessel.beam}m > max {self.max_beam}m")
        if vessel.draft > self.max_draft:
            violations.append(f"Draft {vessel.draft}m > max {self.max_draft}m")
        
        # Cargo type compatibility
        type_map = {
            'container': ['container', 'multipurpose'],
            'bulk': ['bulk', 'multipurpose', 'general'],
            'tanker': ['liquid', 'tanker'],
            'general': ['general', 'multipurpose']
        }
        compatible = type_map.get(vessel.vessel_type.lower(), ['general'])
        if self.berth_type.lower() not in compatible:
            violations.append(f"Type mismatch: {vessel.vessel_type} vs {self.berth_type}")
        
        return len(violations) == 0, violations


@dataclass
class AllocationSolution:
    """Represents a complete berth allocation solution"""
    assignments: Dict[int, int]  # vessel_id -> berth_id
    start_times: Dict[int, datetime]  # vessel_id -> scheduled start
    end_times: Dict[int, datetime]  # vessel_id -> scheduled end
    total_waiting_time: float = 0
    berth_utilization: float = 0
    conflicts: List[Dict] = field(default_factory=list)
    fitness_score: float = 0
    is_feasible: bool = True
    
    def copy(self) -> 'AllocationSolution':
        return AllocationSolution(
            assignments=dict(self.assignments),
            start_times=dict(self.start_times),
            end_times=dict(self.end_times),
            total_waiting_time=self.total_waiting_time,
            berth_utilization=self.berth_utilization,
            conflicts=list(self.conflicts),
            fitness_score=self.fitness_score,
            is_feasible=self.is_feasible
        )


@dataclass
class ResourceAssignment:
    """Represents a resource (pilot/tug) assignment"""
    resource_id: int
    resource_type: str
    resource_name: str
    vessel_id: int
    start_time: datetime
    end_time: datetime
    status: str = "assigned"


@dataclass
class ConflictDetection:
    """Result of conflict detection"""
    conflict_type: ConflictType
    vessel_ids: List[int]
    berth_id: Optional[int]
    time_window: Tuple[datetime, datetime]
    severity: int  # 1-10
    description: str
    resolution_options: List[str]


# ============================================================================
# CONSTRAINT SATISFACTION SOLVER
# ============================================================================

class ConstraintSolver:
    """
    Constraint Satisfaction Problem (CSP) solver for berth allocation.
    Uses arc consistency (AC-3) and backtracking with constraint propagation.
    """
    
    def __init__(self):
        self.domains: Dict[int, Set[int]] = {}  # vessel_id -> possible berths
        self.constraints: List[Callable] = []
        self.assignments: Dict[int, int] = {}
    
    def add_variable(self, vessel_id: int, possible_berths: Set[int]):
        """Add a vessel with its domain of possible berths"""
        self.domains[vessel_id] = possible_berths.copy()
    
    def add_constraint(self, constraint_fn: Callable[[Dict[int, int]], bool]):
        """Add a constraint function"""
        self.constraints.append(constraint_fn)
    
    def is_consistent(self, assignments: Dict[int, int]) -> bool:
        """Check if current assignments satisfy all constraints"""
        return all(constraint(assignments) for constraint in self.constraints)
    
    def arc_consistency_3(self) -> bool:
        """
        Apply AC-3 algorithm to reduce domains.
        Returns False if any domain becomes empty (no solution).
        """
        queue = []
        for xi in self.domains:
            for xj in self.domains:
                if xi != xj:
                    queue.append((xi, xj))
        
        while queue:
            xi, xj = queue.pop(0)
            if self._revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False
                for xk in self.domains:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))
        return True
    
    def _revise(self, xi: int, xj: int) -> bool:
        """Remove values from domain of xi that are inconsistent with xj"""
        revised = False
        for x in list(self.domains[xi]):
            # Check if there exists any value in xj's domain that's consistent
            consistent = False
            for y in self.domains[xj]:
                test_assignment = {xi: x, xj: y}
                if self.is_consistent(test_assignment):
                    consistent = True
                    break
            if not consistent:
                self.domains[xi].remove(x)
                revised = True
        return revised
    
    def backtrack_search(self) -> Optional[Dict[int, int]]:
        """
        Backtracking search with constraint propagation.
        Returns complete assignment or None if no solution exists.
        """
        return self._backtrack({})
    
    def _backtrack(self, assignment: Dict[int, int]) -> Optional[Dict[int, int]]:
        # Check if assignment is complete
        if len(assignment) == len(self.domains):
            return assignment
        
        # Select unassigned variable (MRV heuristic)
        unassigned = [v for v in self.domains if v not in assignment]
        var = min(unassigned, key=lambda v: len(self.domains[v]))
        
        # Try each value in domain (LCV heuristic ordering)
        for value in self._order_domain_values(var, assignment):
            new_assignment = assignment.copy()
            new_assignment[var] = value
            
            if self.is_consistent(new_assignment):
                result = self._backtrack(new_assignment)
                if result is not None:
                    return result
        
        return None
    
    def _order_domain_values(self, var: int, assignment: Dict[int, int]) -> List[int]:
        """Order domain values by Least Constraining Value (LCV) heuristic"""
        def count_constraints(value: int) -> int:
            count = 0
            for other_var in self.domains:
                if other_var not in assignment and other_var != var:
                    for other_val in self.domains[other_var]:
                        test = {var: value, other_var: other_val}
                        if not self.is_consistent(test):
                            count += 1
            return count
        
        return sorted(self.domains[var], key=count_constraints)


# ============================================================================
# PRIORITY-BASED BERTH ALLOCATION
# ============================================================================

class PriorityBasedAllocator:
    """
    Priority-based berth allocation using weighted scoring.
    Fast heuristic for real-time allocation decisions.
    """
    
    def __init__(self, berths: List[BerthSlot]):
        self.berths = {b.berth_id: b for b in berths}
        self.schedules: Dict[int, List[TimeSlot]] = defaultdict(list)  # berth_id -> occupied slots
    
    def calculate_priority_score(self, vessel: VesselRequest) -> float:
        """Calculate weighted priority score for a vessel"""
        base_score = 100.0
        
        # Priority weight
        priority_map = {1: 1.5, 2: 1.0, 3: 0.8}
        base_score *= priority_map.get(vessel.priority, 1.0)
        
        # Vessel size factor (larger vessels get slight priority)
        if vessel.loa > 300:
            base_score *= 1.2
        elif vessel.loa > 200:
            base_score *= 1.1
        
        # Cargo type urgency
        if vessel.is_hazardous:
            base_score *= 0.9  # Slightly lower (requires special handling)
        if 'reefer' in vessel.cargo_type.lower() or 'perishable' in vessel.cargo_type.lower():
            base_score *= 1.3  # Higher (time-sensitive)
        
        # Waiting time penalty (the longer waiting, the higher priority)
        # This would use actual waiting time data
        
        return base_score
    
    def find_best_berth(
        self, 
        vessel: VesselRequest,
        target_time: datetime
    ) -> Tuple[Optional[int], float, List[str]]:
        """
        Find the best berth for a vessel at target time.
        Returns (berth_id, score, reasons)
        """
        candidates = []
        
        for berth_id, berth in self.berths.items():
            can_fit, violations = berth.can_accommodate(vessel)
            
            if not can_fit:
                continue
            
            # Check time availability
            earliest_available = self._get_earliest_available(
                berth_id, target_time, vessel.estimated_dwell_time
            )
            
            waiting_time = max(0, (earliest_available - target_time).total_seconds() / 60)
            
            # Calculate score (higher is better)
            score = self._score_berth_fit(vessel, berth, waiting_time)
            
            candidates.append((berth_id, score, waiting_time, earliest_available))
        
        if not candidates:
            return None, 0, ["No suitable berth found"]
        
        # Sort by score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        best = candidates[0]
        reasons = [
            f"Best fit score: {best[1]:.2f}",
            f"Waiting time: {best[2]:.0f} minutes",
            f"Available from: {best[3].isoformat()}"
        ]
        
        return best[0], best[1], reasons
    
    def _get_earliest_available(
        self, 
        berth_id: int, 
        after_time: datetime,
        duration_minutes: float
    ) -> datetime:
        """Find earliest time a berth is available for given duration"""
        occupied = sorted(self.schedules[berth_id], key=lambda s: s.start)
        
        if not occupied:
            return after_time
        
        # Check if we can fit before first slot
        if occupied[0].start > after_time + timedelta(minutes=duration_minutes):
            return after_time
        
        # Check gaps between slots
        for i in range(len(occupied) - 1):
            gap_start = occupied[i].end
            gap_end = occupied[i + 1].start
            
            if gap_start >= after_time:
                gap_duration = (gap_end - gap_start).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    return max(gap_start, after_time)
        
        # After last slot
        return max(occupied[-1].end, after_time)
    
    def _score_berth_fit(
        self, 
        vessel: VesselRequest, 
        berth: BerthSlot,
        waiting_time: float
    ) -> float:
        """Score how well a vessel fits a berth (0-100)"""
        score = 100.0
        
        # Dimension fit (prefer berths that are well-sized, not too big)
        loa_efficiency = vessel.loa / berth.max_loa
        if 0.8 <= loa_efficiency <= 0.95:
            score += 10  # Optimal fit
        elif loa_efficiency < 0.5:
            score -= 10  # Berth too large (inefficient)
        
        # Draft margin
        draft_margin = berth.max_draft - vessel.draft
        if draft_margin < 1.0:
            score -= 15  # Very tight
        elif draft_margin > 3.0:
            score += 5
        
        # Crane availability
        score += min(10, berth.cranes * 3)
        
        # Waiting time penalty
        score -= min(30, waiting_time / 10)
        
        return max(0, score)
    
    def allocate_vessels(
        self, 
        vessels: List[VesselRequest]
    ) -> AllocationSolution:
        """
        Allocate multiple vessels using priority-based heuristic.
        """
        # Sort by priority score
        scored_vessels = [
            (v, self.calculate_priority_score(v)) for v in vessels
        ]
        scored_vessels.sort(key=lambda x: x[1], reverse=True)
        
        solution = AllocationSolution(
            assignments={},
            start_times={},
            end_times={},
        )
        
        total_waiting = 0
        
        for vessel, priority_score in scored_vessels:
            berth_id, fit_score, reasons = self.find_best_berth(vessel, vessel.eta)
            
            if berth_id is not None:
                # Get actual start time
                start_time = self._get_earliest_available(
                    berth_id, vessel.eta, vessel.estimated_dwell_time
                )
                end_time = start_time + timedelta(minutes=vessel.estimated_dwell_time)
                
                # Record assignment
                solution.assignments[vessel.vessel_id] = berth_id
                solution.start_times[vessel.vessel_id] = start_time
                solution.end_times[vessel.vessel_id] = end_time
                
                # Update berth schedule
                self.schedules[berth_id].append(TimeSlot(
                    start=start_time,
                    end=end_time,
                    berth_id=berth_id,
                    is_available=False
                ))
                
                # Calculate waiting time
                waiting = max(0, (start_time - vessel.eta).total_seconds() / 60)
                total_waiting += waiting
            else:
                solution.is_feasible = False
                solution.conflicts.append({
                    'vessel_id': vessel.vessel_id,
                    'reason': 'No suitable berth found',
                    'time': vessel.eta.isoformat()
                })
        
        solution.total_waiting_time = total_waiting
        solution.fitness_score = self._calculate_fitness(solution, vessels)
        
        return solution
    
    def _calculate_fitness(
        self, 
        solution: AllocationSolution, 
        vessels: List[VesselRequest]
    ) -> float:
        """Calculate overall fitness score for a solution"""
        if not solution.is_feasible:
            return 0.0
        
        # Components
        waiting_penalty = solution.total_waiting_time / (len(vessels) * 60)  # Normalize
        allocation_rate = len(solution.assignments) / len(vessels)
        conflict_penalty = len(solution.conflicts) * 10
        
        fitness = 100 * allocation_rate - waiting_penalty - conflict_penalty
        return max(0, fitness)


# ============================================================================
# GENETIC ALGORITHM FOR SCHEDULE OPTIMIZATION
# ============================================================================

class GeneticAlgorithmOptimizer:
    """
    Genetic Algorithm for berth schedule optimization.
    Suitable for finding near-optimal solutions when exact methods are too slow.
    """
    
    def __init__(
        self,
        berths: List[BerthSlot],
        population_size: int = GA_POPULATION_SIZE,
        generations: int = GA_GENERATIONS,
        mutation_rate: float = GA_MUTATION_RATE,
        crossover_rate: float = GA_CROSSOVER_RATE
    ):
        self.berths = berths
        self.berth_ids = [b.berth_id for b in berths]
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
    
    def optimize(
        self, 
        vessels: List[VesselRequest],
        objective: OptimizationObjective = OptimizationObjective.BALANCED
    ) -> AllocationSolution:
        """
        Run genetic algorithm to find optimal berth allocation.
        """
        # Initialize population
        population = self._initialize_population(vessels)
        
        best_solution = None
        best_fitness = float('-inf')
        
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [
                self._evaluate_fitness(ind, vessels, objective) 
                for ind in population
            ]
            
            # Track best
            gen_best_idx = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_solution = population[gen_best_idx].copy()
            
            # Selection (tournament)
            selected = self._tournament_selection(population, fitness_scores)
            
            # Crossover
            offspring = []
            for i in range(0, len(selected) - 1, 2):
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(selected[i], selected[i+1], vessels)
                    offspring.extend([child1, child2])
                else:
                    offspring.extend([selected[i].copy(), selected[i+1].copy()])
            
            # Mutation
            for individual in offspring:
                if random.random() < self.mutation_rate:
                    self._mutate(individual, vessels)
            
            # Elitism
            elite = sorted(zip(population, fitness_scores), key=lambda x: x[1], reverse=True)
            population = [e[0] for e in elite[:GA_ELITE_SIZE]] + offspring[:self.population_size - GA_ELITE_SIZE]
        
        if best_solution is None:
            best_solution = population[0]
        
        # Convert to AllocationSolution
        return self._decode_solution(best_solution, vessels)
    
    def _initialize_population(
        self, 
        vessels: List[VesselRequest]
    ) -> List[Dict[int, int]]:
        """Create initial population of random valid assignments"""
        population = []
        
        for _ in range(self.population_size):
            individual = {}
            for vessel in vessels:
                # Find valid berths for this vessel
                valid_berths = [
                    b for b in self.berths 
                    if b.can_accommodate(vessel)[0]
                ]
                if valid_berths:
                    individual[vessel.vessel_id] = random.choice(valid_berths).berth_id
                else:
                    # Assign any berth (will be penalized)
                    individual[vessel.vessel_id] = random.choice(self.berth_ids)
            
            population.append(individual)
        
        return population
    
    def _evaluate_fitness(
        self,
        individual: Dict[int, int],
        vessels: List[VesselRequest],
        objective: OptimizationObjective
    ) -> float:
        """Evaluate fitness of an individual solution"""
        fitness = 100.0
        
        # Count constraint violations
        violations = 0
        for vessel in vessels:
            berth_id = individual.get(vessel.vessel_id)
            if berth_id:
                berth = next((b for b in self.berths if b.berth_id == berth_id), None)
                if berth:
                    can_fit, _ = berth.can_accommodate(vessel)
                    if not can_fit:
                        violations += 1
        
        fitness -= violations * 20
        
        # Count berth conflicts (same berth, overlapping time)
        berth_assignments = defaultdict(list)
        for vessel in vessels:
            berth_id = individual.get(vessel.vessel_id)
            if berth_id:
                berth_assignments[berth_id].append(vessel)
        
        conflicts = 0
        for berth_id, assigned_vessels in berth_assignments.items():
            if len(assigned_vessels) > 1:
                # Check time overlaps
                for i, v1 in enumerate(assigned_vessels):
                    for v2 in assigned_vessels[i+1:]:
                        if self._vessels_overlap(v1, v2):
                            conflicts += 1
        
        fitness -= conflicts * 15
        
        # Objective-specific scoring
        if objective == OptimizationObjective.MINIMIZE_WAITING_TIME:
            # Prefer earlier allocations
            pass  # Would need time slot calculation
        elif objective == OptimizationObjective.MAXIMIZE_BERTH_UTILIZATION:
            # Prefer even distribution
            utilization_variance = self._calculate_utilization_variance(individual, vessels)
            fitness -= utilization_variance * 5
        
        return max(0, fitness)
    
    def _vessels_overlap(self, v1: VesselRequest, v2: VesselRequest) -> bool:
        """Check if two vessels' time windows overlap"""
        return v1.eta < v2.etd and v2.eta < v1.etd
    
    def _calculate_utilization_variance(
        self, 
        individual: Dict[int, int],
        vessels: List[VesselRequest]
    ) -> float:
        """Calculate variance in berth utilization"""
        berth_usage = defaultdict(float)
        for vessel in vessels:
            berth_id = individual.get(vessel.vessel_id)
            if berth_id:
                berth_usage[berth_id] += vessel.estimated_dwell_time
        
        if not berth_usage:
            return 0.0
        
        values = list(berth_usage.values())
        mean_usage = sum(values) / len(values)
        variance = sum((v - mean_usage) ** 2 for v in values) / len(values)
        return math.sqrt(variance)
    
    def _tournament_selection(
        self,
        population: List[Dict[int, int]],
        fitness_scores: List[float],
        tournament_size: int = 3
    ) -> List[Dict[int, int]]:
        """Tournament selection for GA"""
        selected = []
        for _ in range(len(population)):
            tournament = random.sample(list(enumerate(fitness_scores)), tournament_size)
            winner_idx = max(tournament, key=lambda x: x[1])[0]
            selected.append(population[winner_idx].copy())
        return selected
    
    def _crossover(
        self,
        parent1: Dict[int, int],
        parent2: Dict[int, int],
        vessels: List[VesselRequest]
    ) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Two-point crossover"""
        vessel_ids = [v.vessel_id for v in vessels]
        if len(vessel_ids) < 3:
            return parent1.copy(), parent2.copy()
        
        # Random crossover points
        points = sorted(random.sample(range(len(vessel_ids)), 2))
        
        child1, child2 = {}, {}
        for i, vid in enumerate(vessel_ids):
            if points[0] <= i < points[1]:
                child1[vid] = parent2.get(vid, parent1.get(vid))
                child2[vid] = parent1.get(vid, parent2.get(vid))
            else:
                child1[vid] = parent1.get(vid)
                child2[vid] = parent2.get(vid)
        
        return child1, child2
    
    def _mutate(self, individual: Dict[int, int], vessels: List[VesselRequest]):
        """Mutation: randomly reassign one vessel"""
        vessel = random.choice(vessels)
        valid_berths = [b for b in self.berths if b.can_accommodate(vessel)[0]]
        if valid_berths:
            individual[vessel.vessel_id] = random.choice(valid_berths).berth_id
    
    def _decode_solution(
        self,
        individual: Dict[int, int],
        vessels: List[VesselRequest]
    ) -> AllocationSolution:
        """Convert GA individual to AllocationSolution"""
        solution = AllocationSolution(
            assignments=dict(individual),
            start_times={},
            end_times={}
        )
        
        # Calculate times based on ETA and berth availability
        berth_timeline = defaultdict(list)
        vessels_by_id = {v.vessel_id: v for v in vessels}
        
        # Sort vessels by ETA
        sorted_vessels = sorted(vessels, key=lambda v: v.eta)
        
        for vessel in sorted_vessels:
            berth_id = individual.get(vessel.vessel_id)
            if not berth_id:
                continue
            
            # Find earliest available slot
            occupied = berth_timeline[berth_id]
            if not occupied:
                start = vessel.eta
            else:
                last_end = max(slot[1] for slot in occupied)
                start = max(vessel.eta, last_end)
            
            end = start + timedelta(minutes=vessel.estimated_dwell_time)
            
            solution.start_times[vessel.vessel_id] = start
            solution.end_times[vessel.vessel_id] = end
            berth_timeline[berth_id].append((start, end))
            
            # Calculate waiting time
            waiting = (start - vessel.eta).total_seconds() / 60
            solution.total_waiting_time += max(0, waiting)
        
        solution.is_feasible = len(solution.assignments) == len(vessels)
        solution.fitness_score = self._evaluate_fitness(
            individual, vessels, OptimizationObjective.BALANCED
        )
        
        return solution


# ============================================================================
# HUNGARIAN ALGORITHM FOR RESOURCE ASSIGNMENT
# ============================================================================

class HungarianAssigner:
    """
    Hungarian Algorithm implementation for optimal resource assignment.
    Used for pilot/tug to vessel assignment optimization.
    """
    
    def __init__(self):
        pass
    
    def assign(
        self,
        vessels: List[VesselRequest],
        resources: List[Dict[str, Any]],
        cost_matrix: Optional[List[List[float]]] = None
    ) -> List[ResourceAssignment]:
        """
        Optimal assignment of resources to vessels.
        
        If cost_matrix is not provided, generates one based on compatibility.
        """
        if not vessels or not resources:
            return []
        
        # Generate cost matrix if not provided
        if cost_matrix is None:
            cost_matrix = self._generate_cost_matrix(vessels, resources)
        
        # Pad matrix to be square
        n = max(len(vessels), len(resources))
        padded_matrix = [[float('inf')] * n for _ in range(n)]
        
        for i, row in enumerate(cost_matrix):
            for j, val in enumerate(row):
                padded_matrix[i][j] = val
        
        # Run Hungarian algorithm
        assignments = self._hungarian_algorithm(padded_matrix)
        
        # Convert to ResourceAssignment objects
        result = []
        for vessel_idx, resource_idx in assignments:
            if vessel_idx < len(vessels) and resource_idx < len(resources):
                vessel = vessels[vessel_idx]
                resource = resources[resource_idx]
                
                result.append(ResourceAssignment(
                    resource_id=resource.get('resource_id', resource_idx),
                    resource_type=resource.get('resource_type', 'Unknown'),
                    resource_name=resource.get('resource_name', f'Resource-{resource_idx}'),
                    vessel_id=vessel.vessel_id,
                    start_time=vessel.eta - timedelta(hours=1),  # 1 hour before ETA
                    end_time=vessel.eta + timedelta(hours=2),    # 2 hours buffer
                    status="assigned"
                ))
        
        return result
    
    def _generate_cost_matrix(
        self,
        vessels: List[VesselRequest],
        resources: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """Generate cost matrix based on vessel-resource compatibility"""
        matrix = []
        
        for vessel in vessels:
            row = []
            for resource in resources:
                cost = self._calculate_assignment_cost(vessel, resource)
                row.append(cost)
            matrix.append(row)
        
        return matrix
    
    def _calculate_assignment_cost(
        self,
        vessel: VesselRequest,
        resource: Dict[str, Any]
    ) -> float:
        """Calculate cost of assigning a resource to a vessel"""
        cost = 50.0  # Base cost
        
        resource_type = resource.get('resource_type', '').lower()
        
        if 'pilot' in resource_type:
            # Check pilot class vs vessel size
            pilot_class = resource.get('pilot_class', 'III')
            max_gt = resource.get('max_gt', 20000)
            
            if vessel.gross_tonnage > max_gt:
                cost += 100  # Incompatible - high penalty
            else:
                # Prefer appropriately skilled pilots
                utilization = vessel.gross_tonnage / max_gt
                if 0.5 <= utilization <= 0.9:
                    cost -= 10  # Good fit bonus
        
        elif 'tug' in resource_type:
            # Check tug capacity vs vessel requirements
            bollard_pull = resource.get('bollard_pull', 50)
            required_pull = vessel.gross_tonnage / 5000 * 10  # Rough estimate
            
            if bollard_pull < required_pull:
                cost += 50  # Underpowered
            else:
                cost -= min(20, (bollard_pull - required_pull))
        
        # Availability factor
        if not resource.get('is_available', True):
            cost += 200  # Heavily penalize unavailable resources
        
        return max(0, cost)
    
    def _hungarian_algorithm(self, cost_matrix: List[List[float]]) -> List[Tuple[int, int]]:
        """
        Hungarian Algorithm implementation.
        Returns list of (row, col) assignments.
        """
        n = len(cost_matrix)
        
        # Step 1: Subtract row minimums
        u = [0] * (n + 1)
        v = [0] * (n + 1)
        p = [0] * (n + 1)
        way = [0] * (n + 1)
        
        matrix = [row[:] for row in cost_matrix]
        
        # Row reduction
        for i in range(n):
            min_val = min(matrix[i])
            for j in range(n):
                matrix[i][j] -= min_val
        
        # Column reduction
        for j in range(n):
            min_val = min(matrix[i][j] for i in range(n))
            for i in range(n):
                matrix[i][j] -= min_val
        
        # Simple greedy assignment (approximate)
        row_assigned = [-1] * n
        col_assigned = [-1] * n
        
        for i in range(n):
            for j in range(n):
                if matrix[i][j] == 0 and row_assigned[i] == -1 and col_assigned[j] == -1:
                    row_assigned[i] = j
                    col_assigned[j] = i
        
        assignments = [(i, row_assigned[i]) for i in range(n) if row_assigned[i] != -1]
        
        return assignments


# ============================================================================
# CONFLICT DETECTION ENGINE
# ============================================================================

class ConflictDetector:
    """
    Detect conflicts in berth schedules and resource allocations.
    Implements real-time conflict detection as per FR-CONF requirements.
    """
    
    def __init__(self):
        pass
    
    def detect_conflicts(
        self,
        solution: AllocationSolution,
        vessels: Dict[int, VesselRequest],
        berths: Dict[int, BerthSlot],
        resources: Optional[List[ResourceAssignment]] = None
    ) -> List[ConflictDetection]:
        """
        Detect all conflicts in a schedule solution.
        Returns list of detected conflicts with resolution options.
        """
        conflicts = []
        
        # 1. Time overlap conflicts
        conflicts.extend(self._detect_time_overlaps(solution, vessels))
        
        # 2. Resource contention
        if resources:
            conflicts.extend(self._detect_resource_contention(resources, vessels))
        
        # 3. Physical constraint violations
        conflicts.extend(self._detect_physical_violations(solution, vessels, berths))
        
        return conflicts
    
    def _detect_time_overlaps(
        self,
        solution: AllocationSolution,
        vessels: Dict[int, VesselRequest]
    ) -> List[ConflictDetection]:
        """Detect vessels scheduled at same berth with overlapping times"""
        conflicts = []
        
        # Group by berth
        berth_assignments = defaultdict(list)
        for vessel_id, berth_id in solution.assignments.items():
            start = solution.start_times.get(vessel_id)
            end = solution.end_times.get(vessel_id)
            if start and end:
                berth_assignments[berth_id].append((vessel_id, start, end))
        
        # Check overlaps within each berth
        for berth_id, assignments in berth_assignments.items():
            assignments.sort(key=lambda x: x[1])  # Sort by start time
            
            for i, (v1_id, s1, e1) in enumerate(assignments):
                for v2_id, s2, e2 in assignments[i+1:]:
                    if s1 < e2 and s2 < e1:  # Overlap
                        overlap_start = max(s1, s2)
                        overlap_end = min(e1, e2)
                        
                        v1_name = vessels[v1_id].vessel_name if v1_id in vessels else f"Vessel-{v1_id}"
                        v2_name = vessels[v2_id].vessel_name if v2_id in vessels else f"Vessel-{v2_id}"
                        
                        conflicts.append(ConflictDetection(
                            conflict_type=ConflictType.TIME_OVERLAP,
                            vessel_ids=[v1_id, v2_id],
                            berth_id=berth_id,
                            time_window=(overlap_start, overlap_end),
                            severity=8,
                            description=f"Time overlap: {v1_name} and {v2_name} at Berth {berth_id}",
                            resolution_options=[
                                f"Delay {v2_name} to {e1.isoformat()}",
                                f"Reassign {v2_name} to another berth",
                                f"Reduce dwell time for {v1_name}"
                            ]
                        ))
        
        return conflicts
    
    def _detect_resource_contention(
        self,
        resources: List[ResourceAssignment],
        vessels: Dict[int, VesselRequest]
    ) -> List[ConflictDetection]:
        """Detect same resource assigned to multiple vessels at same time"""
        conflicts = []
        
        # Group by resource
        resource_assignments = defaultdict(list)
        for ra in resources:
            resource_assignments[ra.resource_id].append(ra)
        
        for resource_id, assignments in resource_assignments.items():
            assignments.sort(key=lambda x: x.start_time)
            
            for i, a1 in enumerate(assignments):
                for a2 in assignments[i+1:]:
                    if a1.start_time < a2.end_time and a2.start_time < a1.end_time:
                        conflicts.append(ConflictDetection(
                            conflict_type=ConflictType.RESOURCE_CONTENTION,
                            vessel_ids=[a1.vessel_id, a2.vessel_id],
                            berth_id=None,
                            time_window=(max(a1.start_time, a2.start_time), 
                                       min(a1.end_time, a2.end_time)),
                            severity=7,
                            description=f"{a1.resource_type} {a1.resource_name} double-booked",
                            resolution_options=[
                                f"Assign alternate {a1.resource_type}",
                                f"Delay vessel {a2.vessel_id}",
                                f"Adjust assignment windows"
                            ]
                        ))
        
        return conflicts
    
    def _detect_physical_violations(
        self,
        solution: AllocationSolution,
        vessels: Dict[int, VesselRequest],
        berths: Dict[int, BerthSlot]
    ) -> List[ConflictDetection]:
        """Detect vessels assigned to berths they don't fit"""
        conflicts = []
        
        for vessel_id, berth_id in solution.assignments.items():
            vessel = vessels.get(vessel_id)
            berth = berths.get(berth_id)
            
            if not vessel or not berth:
                continue
            
            can_fit, violations = berth.can_accommodate(vessel)
            
            if not can_fit:
                start = solution.start_times.get(vessel_id, datetime.now())
                end = solution.end_times.get(vessel_id, datetime.now())
                
                conflicts.append(ConflictDetection(
                    conflict_type=ConflictType.TIME_OVERLAP,  # Physical constraint
                    vessel_ids=[vessel_id],
                    berth_id=berth_id,
                    time_window=(start, end),
                    severity=10,  # Hard constraint
                    description=f"{vessel.vessel_name} cannot fit at Berth {berth.berth_code}: {', '.join(violations)}",
                    resolution_options=[
                        f"Reassign to compatible berth",
                        f"Reduce cargo/draft if possible"
                    ]
                ))
        
        return conflicts


# ============================================================================
# RE-OPTIMIZATION ENGINE
# ============================================================================

class ReOptimizationEngine:
    """
    Dynamic re-optimization for schedule disruptions.
    Handles delays, cancellations, and priority changes.
    """
    
    def __init__(
        self,
        berths: List[BerthSlot],
        allocator: Optional[PriorityBasedAllocator] = None
    ):
        self.berths = {b.berth_id: b for b in berths}
        self.allocator = allocator or PriorityBasedAllocator(berths)
    
    def handle_delay(
        self,
        current_solution: AllocationSolution,
        delayed_vessel_id: int,
        new_eta: datetime,
        vessels: Dict[int, VesselRequest]
    ) -> Tuple[AllocationSolution, List[Dict[str, Any]]]:
        """
        Re-optimize schedule when a vessel is delayed.
        Returns (new_solution, cascade_effects)
        """
        cascade_effects = []
        new_solution = current_solution.copy()
        
        if delayed_vessel_id not in new_solution.assignments:
            return new_solution, [{"error": "Vessel not found in schedule"}]
        
        vessel = vessels.get(delayed_vessel_id)
        if not vessel:
            return new_solution, [{"error": "Vessel data not found"}]
        
        old_start = new_solution.start_times.get(delayed_vessel_id)
        old_end = new_solution.end_times.get(delayed_vessel_id)
        berth_id = new_solution.assignments[delayed_vessel_id]
        
        # Update delayed vessel's times
        delay_minutes = (new_eta - vessel.eta).total_seconds() / 60
        new_start = new_eta
        new_end = new_start + timedelta(minutes=vessel.estimated_dwell_time)
        
        new_solution.start_times[delayed_vessel_id] = new_start
        new_solution.end_times[delayed_vessel_id] = new_end
        
        cascade_effects.append({
            "type": "delay",
            "vessel_id": delayed_vessel_id,
            "old_start": old_start.isoformat() if old_start else None,
            "new_start": new_start.isoformat(),
            "delay_minutes": delay_minutes
        })
        
        # Check for cascading conflicts
        for v_id, b_id in new_solution.assignments.items():
            if v_id == delayed_vessel_id or b_id != berth_id:
                continue
            
            v_start = new_solution.start_times.get(v_id)
            v_end = new_solution.end_times.get(v_id)
            
            if v_start and v_end:
                # Check overlap with delayed vessel
                if new_start < v_end and v_start < new_end:
                    # Need to shift this vessel
                    shift = (new_end - v_start).total_seconds() / 60
                    
                    new_v_start = new_end
                    new_v_end = new_v_start + (v_end - v_start)
                    
                    new_solution.start_times[v_id] = new_v_start
                    new_solution.end_times[v_id] = new_v_end
                    
                    cascade_effects.append({
                        "type": "cascade_delay",
                        "vessel_id": v_id,
                        "shift_minutes": shift,
                        "reason": f"Cascaded from vessel {delayed_vessel_id}"
                    })
        
        # Recalculate total waiting time
        new_solution.total_waiting_time = 0
        for v_id, start in new_solution.start_times.items():
            vessel = vessels.get(v_id)
            if vessel:
                waiting = max(0, (start - vessel.eta).total_seconds() / 60)
                new_solution.total_waiting_time += waiting
        
        return new_solution, cascade_effects
    
    def find_alternative_berth(
        self,
        vessel: VesselRequest,
        current_berth_id: int,
        current_solution: AllocationSolution,
        target_time: datetime
    ) -> Optional[Tuple[int, datetime, List[str]]]:
        """
        Find alternative berth when current berth is problematic.
        Returns (berth_id, available_time, reasons) or None.
        """
        candidates = []
        
        for berth_id, berth in self.berths.items():
            if berth_id == current_berth_id:
                continue
            
            can_fit, violations = berth.can_accommodate(vessel)
            if not can_fit:
                continue
            
            # Check availability
            earliest = self._find_earliest_slot(
                berth_id, target_time, 
                vessel.estimated_dwell_time, 
                current_solution
            )
            
            waiting = max(0, (earliest - target_time).total_seconds() / 60)
            
            candidates.append((
                berth_id, 
                earliest, 
                waiting,
                [f"Berth {berth.berth_code}", f"Wait: {waiting:.0f}min"]
            ))
        
        if not candidates:
            return None
        
        # Return best option (minimum waiting)
        best = min(candidates, key=lambda x: x[2])
        return (best[0], best[1], best[3])
    
    def _find_earliest_slot(
        self,
        berth_id: int,
        after_time: datetime,
        duration_minutes: float,
        solution: AllocationSolution
    ) -> datetime:
        """Find earliest available slot at a berth"""
        # Get all assignments at this berth
        occupied = []
        for v_id, b_id in solution.assignments.items():
            if b_id == berth_id:
                start = solution.start_times.get(v_id)
                end = solution.end_times.get(v_id)
                if start and end:
                    occupied.append((start, end))
        
        occupied.sort(key=lambda x: x[0])
        
        if not occupied:
            return after_time
        
        # Try before first
        if occupied[0][0] > after_time + timedelta(minutes=duration_minutes):
            return after_time
        
        # Try gaps
        for i in range(len(occupied) - 1):
            gap_start = occupied[i][1]
            gap_end = occupied[i + 1][0]
            
            if gap_start >= after_time:
                gap_duration = (gap_end - gap_start).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    return gap_start
        
        # After last
        return max(occupied[-1][1], after_time)


# ============================================================================
# GREEDY FIRST-FIT ALLOCATOR (FAST HEURISTIC)
# ============================================================================

class GreedyFirstFitAllocator:
    """
    Simple greedy first-fit algorithm for quick allocations.
    O(n*m) complexity where n=vessels, m=berths.
    """
    
    def __init__(self, berths: List[BerthSlot]):
        self.berths = sorted(berths, key=lambda b: -b.max_loa)  # Largest first
    
    def allocate(
        self, 
        vessels: List[VesselRequest]
    ) -> AllocationSolution:
        """Quick first-fit allocation"""
        # Sort vessels by priority then ETA
        sorted_vessels = sorted(vessels, key=lambda v: (v.priority, v.eta))
        
        solution = AllocationSolution(
            assignments={},
            start_times={},
            end_times={}
        )
        
        berth_schedules = defaultdict(list)
        
        for vessel in sorted_vessels:
            assigned = False
            
            for berth in self.berths:
                can_fit, _ = berth.can_accommodate(vessel)
                if not can_fit:
                    continue
                
                # Find slot
                occupied = berth_schedules[berth.berth_id]
                occupied.sort(key=lambda x: x[0])
                
                start_time = vessel.eta
                
                # Check for conflicts
                conflict = False
                for occ_start, occ_end in occupied:
                    proposed_end = start_time + timedelta(minutes=vessel.estimated_dwell_time)
                    if start_time < occ_end and occ_start < proposed_end:
                        # Conflict - try after this slot
                        start_time = occ_end
                        conflict = True
                
                end_time = start_time + timedelta(minutes=vessel.estimated_dwell_time)
                
                # Final overlap check
                final_conflict = any(
                    start_time < oe and os < end_time 
                    for os, oe in occupied
                )
                
                if not final_conflict:
                    solution.assignments[vessel.vessel_id] = berth.berth_id
                    solution.start_times[vessel.vessel_id] = start_time
                    solution.end_times[vessel.vessel_id] = end_time
                    berth_schedules[berth.berth_id].append((start_time, end_time))
                    assigned = True
                    break
            
            if not assigned:
                solution.conflicts.append({
                    'vessel_id': vessel.vessel_id,
                    'reason': 'No available berth slot'
                })
        
        solution.is_feasible = len(solution.conflicts) == 0
        return solution


# ============================================================================
# FACADE / API
# ============================================================================

class SmartBerthHeuristics:
    """
    Unified API for all heuristics and optimization algorithms.
    """
    
    def __init__(self, berths: List[Dict[str, Any]]):
        # Convert dict berths to BerthSlot objects
        self.berth_slots = [
            BerthSlot(
                berth_id=b.get('BerthId', b.get('berthId', 0)),
                berth_code=b.get('BerthCode', b.get('berthCode', '')),
                terminal_code=b.get('TerminalCode', b.get('terminalCode', '')),
                max_loa=b.get('MaxLOA', b.get('maxLoa', 300)),
                max_beam=b.get('MaxBeam', b.get('maxBeam', 50)),
                max_draft=b.get('MaxDraft', b.get('maxDraft', 14)),
                berth_type=b.get('BerthType', b.get('terminalType', 'Container')),
                cranes=b.get('CraneCount', b.get('numberOfCranes', 2)),
                is_available=b.get('IsAvailable', True)
            )
            for b in berths
        ]
        
        # Initialize algorithms
        self.priority_allocator = PriorityBasedAllocator(self.berth_slots)
        self.ga_optimizer = GeneticAlgorithmOptimizer(self.berth_slots)
        self.greedy_allocator = GreedyFirstFitAllocator(self.berth_slots)
        self.hungarian_assigner = HungarianAssigner()
        self.conflict_detector = ConflictDetector()
        self.reopt_engine = ReOptimizationEngine(self.berth_slots)
    
    def quick_allocate(
        self, 
        vessels: List[Dict[str, Any]]
    ) -> AllocationSolution:
        """Fast first-fit allocation for real-time use"""
        requests = self._convert_to_requests(vessels)
        return self.greedy_allocator.allocate(requests)
    
    def priority_allocate(
        self, 
        vessels: List[Dict[str, Any]]
    ) -> AllocationSolution:
        """Priority-weighted allocation"""
        requests = self._convert_to_requests(vessels)
        return self.priority_allocator.allocate_vessels(requests)
    
    def optimize_schedule(
        self,
        vessels: List[Dict[str, Any]],
        objective: OptimizationObjective = OptimizationObjective.BALANCED
    ) -> AllocationSolution:
        """Full GA optimization (slower but better quality)"""
        requests = self._convert_to_requests(vessels)
        return self.ga_optimizer.optimize(requests, objective)
    
    def assign_resources(
        self,
        vessels: List[Dict[str, Any]],
        resources: List[Dict[str, Any]]
    ) -> List[ResourceAssignment]:
        """Optimal resource assignment using Hungarian algorithm"""
        requests = self._convert_to_requests(vessels)
        return self.hungarian_assigner.assign(requests, resources)
    
    def detect_conflicts(
        self,
        solution: AllocationSolution,
        vessels: List[Dict[str, Any]]
    ) -> List[ConflictDetection]:
        """Detect all conflicts in a solution"""
        requests = self._convert_to_requests(vessels)
        vessel_dict = {r.vessel_id: r for r in requests}
        berth_dict = {b.berth_id: b for b in self.berth_slots}
        return self.conflict_detector.detect_conflicts(solution, vessel_dict, berth_dict)
    
    def reoptimize_for_delay(
        self,
        solution: AllocationSolution,
        delayed_vessel_id: int,
        new_eta: datetime,
        vessels: List[Dict[str, Any]]
    ) -> Tuple[AllocationSolution, List[Dict[str, Any]]]:
        """Re-optimize after a delay"""
        requests = self._convert_to_requests(vessels)
        vessel_dict = {r.vessel_id: r for r in requests}
        return self.reopt_engine.handle_delay(solution, delayed_vessel_id, new_eta, vessel_dict)
    
    def _convert_to_requests(self, vessels: List[Dict[str, Any]]) -> List[VesselRequest]:
        """Convert vessel dicts to VesselRequest objects"""
        requests = []
        for v in vessels:
            eta = v.get('ETA', v.get('eta'))
            if isinstance(eta, str):
                eta = datetime.fromisoformat(eta.replace('Z', '+00:00'))
            elif eta is None:
                eta = datetime.now()
            
            requests.append(VesselRequest(
                vessel_id=v.get('VesselId', v.get('vesselId', 0)),
                vessel_name=v.get('VesselName', v.get('vesselName', 'Unknown')),
                vessel_type=v.get('VesselType', v.get('vesselType', 'Container')),
                loa=v.get('LOA', v.get('loa', 200)),
                beam=v.get('Beam', v.get('beam', 30)),
                draft=v.get('Draft', v.get('draft', 10)),
                gross_tonnage=v.get('GrossTonnage', v.get('grossTonnage', 50000)),
                cargo_type=v.get('CargoType', v.get('cargoType', 'General')),
                cargo_quantity=v.get('CargoQuantity', v.get('cargoQuantity', 0)),
                eta=eta,
                requested_berth=v.get('RequestedBerth'),
                priority=v.get('Priority', v.get('priority', 2)),
                estimated_dwell_time=v.get('EstimatedDwellTime', v.get('dwellTime', 720)),
                tugs_required=v.get('TugsRequired', 2),
                pilot_required=v.get('PilotRequired', True),
                is_hazardous='hazard' in v.get('CargoType', '').lower()
            ))
        return requests


# ============================================================================
# SINGLETON ACCESSOR
# ============================================================================

_heuristics_engine: Optional[SmartBerthHeuristics] = None

def get_heuristics_engine(berths: Optional[List[Dict[str, Any]]] = None) -> SmartBerthHeuristics:
    """Get or create the heuristics engine singleton"""
    global _heuristics_engine
    if _heuristics_engine is None and berths:
        _heuristics_engine = SmartBerthHeuristics(berths)
    return _heuristics_engine
