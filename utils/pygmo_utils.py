import pygmo as pg
import math as math
import numpy as numpy
from scipy.interpolate import UnivariateSpline

def plot_spline(plt, x_plot, y_plot, max_fevals, label):
    spline = UnivariateSpline(x_plot, y_plot, s=5)

    spline_x = numpy.linspace(0, max_fevals, 20)
    spline = spline(spline_x)
    plt.plot(spline_x, spline, label=label)

# Weighted Objective Function (Augmented Chebyshev)
def calculate_weighted_objective(weights, values, rho):
    weighted_vals = [value * weight for value, weight in zip(values,weights)] 
    aug_tcheby = max(weighted_vals) + rho * sum(weighted_vals)
    return aug_tcheby

# Calculates the hypervolume with a changing ref point
def reconstruct_hv_per_feval(max_fevals, x_list, f_list, hv_pop):
    # Have the same ref point at the beginning, and compute the starting hypervolume
    hv = [0]

    x = hv_pop.get_x()

    for fevals in range(max_fevals):
        hv_pop.push_back(x_list[fevals], f_list[fevals])
        new_hv = pg.hypervolume(hv_pop)
        ref = new_hv.refpoint(offset=4.0)
        hv.append(new_hv.compute(ref))

    return hv

# Calculates the hypervolume with all the old points from the old generations
# But starts with a full population. Used for the meta-heuristic algorithms
def reconstruct_hv_per_feval_meta(max_fevals, x_list, f_list, hv_pop):
    # Have the same ref point at the beginning, and compute the starting hypervolume
    original_hv = pg.hypervolume(hv_pop)
    ref = original_hv.refpoint(offset=4.0)
    hv = []

    for fevals in range(max_fevals):
        hv_pop.push_back(x_list[fevals], f_list[fevals])
        new_hv = pg.hypervolume(hv_pop)
        hv.append(new_hv.compute(ref))

    return hv

# Stores the f and x values for each generation of the evolutionary algo,
# Then calculate the hypervolume per function evaluation
def get_hv_for_algo(algo, max_fevals, pop_size, seed, problem):

    max_gen = math.ceil(max_fevals/pop_size)

    # same (random) starting population for both algos
    pop = pg.population(problem, pop_size, seed)

    f_list, x_list = pop.get_f(), pop.get_x()

    for i in range(max_gen):
        pop = algo.evolve(pop)

        # Get all the f and x values for this generation
        f_list = numpy.concatenate((f_list, pop.get_f()))
        x_list = numpy.concatenate((x_list, pop.get_x()))

    pop_empty = pg.population(prob=problem, seed=seed)

    return reconstruct_hv_per_feval(max_fevals, x_list, f_list, pop_empty)

# Meta-heuristic algorithms are stochastic and need to be run many times.
# Calculates the hypervolume n times, and then gets the mean across columns
# to give a 1D mean array
def calculate_mean(n, algo, max_fevals, pop_size, seed, problem):

    # 2D array whose elements are the n arrays of hypervolume
    return_array = []
    for i in range(n):
        return_array.append(get_hv_for_algo(algo, max_fevals, pop_size, seed, problem))
        # Make sure we change the seed each time the algo is being run
        seed += i
    return numpy.mean(return_array, axis=0)