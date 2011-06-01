#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import sys
import random
import operator
import logging
import csv
import itertools

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Read the spam list features and put it in a list of lists.
# The dataset is from http://archive.ics.uci.edu/ml/datasets/Spambase
# This example is a copy of the OpenBEAGLE example :
# http://beagle.gel.ulaval.ca/refmanual/beagle/html/d2/dbe/group__Spambase.html
spamReader = csv.reader(open("spambase.csv"))
spam = list(list(float(elem) for elem in row) for row in spamReader)

# defined a new primitive set for strongly typed GP
pset = gp.PrimitiveSetTyped("MAIN", itertools.repeat("float", 57), "bool", "IN")

# boolean operators
pset.addPrimitive(operator.and_, ["bool", "bool"], "bool")
pset.addPrimitive(operator.or_, ["bool", "bool"], "bool")
pset.addPrimitive(operator.not_, ["bool"], "bool")

# floating point operators
# Define a safe division function
def safeDiv(left, right):
    try: return left / right
    except ZeroDivisionError: return 0

pset.addPrimitive(operator.add, ["float","float"], "float")
pset.addPrimitive(operator.sub, ["float","float"], "float")
pset.addPrimitive(operator.mul, ["float","float"], "float")
pset.addPrimitive(safeDiv, ["float","float"], "float")

# logic operators
# Define a new if-then-else function
def if_then_else(input, output1, output2):
    if input: return output1
    else: return output2

pset.addPrimitive(operator.lt, ["float", "float"], "bool")
pset.addPrimitive(operator.eq, ["float", "float"], "bool")
pset.addPrimitive(if_then_else, ["bool", "float", "float"], "float")

# terminals
pset.addEphemeralConstant(lambda: random.random() * 100, "float")
pset.addTerminal(0, "bool")
pset.addTerminal(1, "bool")

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

toolbox = base.Toolbox()
toolbox.register("expr", gp.generateRamped, pset=pset, type_=pset.ret, min_=1, max_=2)
toolbox.register("individual", tools.fillIter, creator.Individual, toolbox.expr)
toolbox.register("population", tools.fillRepeat, list, toolbox.individual)
toolbox.register("lambdify", gp.lambdify, pset=pset)

def evalSpambase(individual):
    # Transform the tree expression in a callable function
    func = toolbox.lambdify(expr=individual)
    # Randomly sample 400 mails in the spam database
    spam_samp = random.sample(spam, 400)
    # Evaluate the sum of correctly identified mail as spam
    result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)
    return result,
    
toolbox.register("evaluate", evalSpambase)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxTypedOnePoint)
toolbox.register("expr_mut", gp.generateFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutTypedUniform, expr=toolbox.expr_mut)

def main():
    pop = toolbox.population(n=100)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)
    
    algorithms.eaSimple(toolbox, pop, 0.5, 0.2, 40, stats, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)

    return pop, stats, hof

if __name__ == "__main__":
    main()
