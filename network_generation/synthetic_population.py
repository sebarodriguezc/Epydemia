import sys
sys.path.append('./')
from typing import List, Union
import pandas as pd
import numpy as np
import igraph as ig
from itertools import combinations
import os

def random_combinations(iterable, r, random_state, n):
    "Random selection from itertools.combinations(iterable, r)"
    pool = tuple(iterable)
    k = len(pool)
    indices = [sorted(tup) for tup in random_state.choice(list(range(k)), (n,r))]
    return tuple([(pool[i], pool[j]) for i,j in indices])

# Step 1: population creation.
#   create population from distribution. Needs bracket distribution per age group.
# Step 2: households creation.
#   needs distribution of household size, and composition of each household.
#   Assign population to households using marginal distributions of composition.
# Step 3: schools.
#   Needs number of schools, distribution of school sizes, enrollment by age,
#   contact matrix between students, number of children per teacher (think about this).
# Step 4: workplaces.
#   Needs number of industries?, distribution of industries, avg number of connections
#    per industry
# Step 5: community.
#   Random layer. Average number of contacts per age group?


# Create population
# 2010 U.S. Census of Population and Housing3
# 2012–2016 ACS Public Use Microdata Sample3
# Public Use Microdata Sample (PUMS) data using a method inspired by
#  Beckman, R. J., Baggerly, K. A. & McKay, M. D. Creating synthetic baseline
# populations. Transportation Res. A: Policy Pract. 30, 415–429 (1996).

def create_network():
    # Workplaces, schools, and social environments are modeled as
    # Watts–Strogatz small-world networks, households are modeled as separate
    # fully connected networks, and random interactions, such as those on
    # public transportation, are modeled in a random network
    # The networks are parameterized such that the average number of 
    # interactions matches the age-stratified data in
    # Mossong, J. et al. Social contacts and mixing patterns relevant to the spread of
    # infectious diseases. PLoS Med. 5, e74 (2008).
    pass

def synthetic_population(population_distribution, size, seed,
                         household_size_distribution,
                         household_age_composition_by_size,
                         school_size_distribution, students_per_teacher,
                         workplace_distribution,
                         p, name, save_dir):
    random_state = np.random.RandomState(seed)
    population = create_population(
        population_distribution,
        size=size,
        random_state=random_state
        )
    population = add_households(
        population,
        size_distribution=household_size_distribution,
        age_composition_by_size=household_age_composition_by_size,
        random_state=random_state
        )
    population = add_schools(
        population,
        size_distribution=school_size_distribution,
        students_per_teacher=students_per_teacher,
        random_state=random_state
        )
    population = add_workplaces(
        population,
        distribution=workplace_distribution,
        random_state=random_state
        )
    households_graph = create_households_graph(population)
    schools_graph = create_schools_graph(population, random_state)
    workplaces_graph = create_workplaces_graph(population, random_state)
    community_graph = create_community_graph(population, p, seed)
    
    # Save
    path = os.path.join(save_dir, '{}_n{}_seed{}'.format(name, size, seed))
    os.mkdir(path)
    wd = os.getcwd()
    os.chdir(path)
    population.to_csv('population.csv')
    households_graph.write_graphml('households')
    schools_graph.write_graphml('schools')
    workplaces_graph.write_graphml('workplaces')
    community_graph.write_graphml('community')
    os.chdir(wd)

def create_population(distribution: str,
                      size: int,
                      random_state:
                      np.random.RandomState = np.random.RandomState(12450)):
    distribution = pd.read_csv(distribution)
    
    # Sample the synthetic population
    synthetic_population = distribution.sample(n=size, replace=True,
                                               weights='proportion',
                                               random_state=random_state).drop(
                                                   columns='proportion')
    
    # Sample an age in years from the sampled age group with equal probability
    age_bounds = synthetic_population['age_group'].str.split("-", expand=True)
    synthetic_population['age'] = random_state.randint(
        age_bounds[0].astype(int).values, age_bounds[1].astype(int).values + 1)
    synthetic_population = synthetic_population.reset_index(drop=True)
    synthetic_population['idx'] = synthetic_population.index.values
    return synthetic_population

def add_households(population: pd.DataFrame,
                      size_distribution: str,
                      age_composition_by_size: str,
                      random_state:
                      np.random.RandomState = np.random.RandomState(5624)):

    # Open files
    size_distribution = pd.read_csv(size_distribution)
    composition = pd.read_csv(age_composition_by_size)
    population['household'] = pd.NA

    # Map age in years to household age groups
    temp_pop = population.copy()
    age_groups = composition.columns.drop('size')
    bins = [int(g.split('-')[0]) for g in age_groups]
    bins.append(int(age_groups[-1].split('-')[1]) + 1)
    temp_pop['age_group'] = pd.cut(temp_pop['age'].values,
                                   bins=bins,
                                   include_lowest=True, right=False,
                                   labels=age_groups)
    
    # Map probabilities by size of household per age group
    for _,row in composition.iterrows():
        temp_pop[str(int(row['size']))] = temp_pop['age_group'].map(row.to_dict())
    
    # Sample households first with their size, and then
    # assign people in the population based on weights.
    household_id = 0
    while len(temp_pop) > 0:
        household_size = size_distribution.sample(n=1,
                                                  weights='proportion',
                                                  random_state=random_state
                                                  )['size'].values[0]
        household = temp_pop.sample(n=min(household_size,
                                          len(temp_pop)),
                                    replace=False,
                                    weights=str(household_size),
                                    random_state=random_state
                                    )['idx'].values
        population.loc[household, 'household'] = household_id
        household_id += 1
        temp_pop.drop(household, inplace=True)
    return population

def add_schools(population: pd.DataFrame,
                  size_distribution: str,
                  students_per_teacher: int,
                  enrollment: str = None,
                  schooling_age: tuple = (5, 18),
                  teaching_age: tuple = (19, 65), 
                  random_state:
                  np.random.RandomState = np.random.RandomState(32561)
                  ):

    size_distribution = pd.read_csv(size_distribution)
    students = population[population['age'].between(*schooling_age)].copy()
    candidate_teachers = population[population['age'].between(*teaching_age)].copy()

    population['school'] = pd.NA
    population['workplace'] = pd.NA

    school_id = 0
    while len(students) > 0:
        school_size_range = size_distribution.sample(n=1,
                                                     weights='proportion',
                                                     random_state=random_state,
                                                     )['size'].values[0]
        school_size_range = tuple(map(int, school_size_range.split('-')))
        school_size = min(random_state.randint(*school_size_range), len(students))
        school = students.sample(n=school_size,
                                 replace=False,
                                 random_state=random_state
                                 )['idx'].values
        try:
            teachers = candidate_teachers.sample(
                n=int(np.ceil(school_size/students_per_teacher)),
                replace=False,
                random_state=random_state
                )['idx'].values
            population.loc[teachers, 'workplace'] = 'schools'
            population.loc[teachers, 'school'] = school_id
            candidate_teachers.drop(teachers, inplace=True)
        except Exception:
            pass
        population.loc[school, 'school'] = school_id
        school_id += 1
        students.drop(school, inplace=True)
    return population

def add_workplaces(population: pd.DataFrame,
                   distribution: str,
                   working_age: tuple = (19, 65), 
                   random_state:
                   np.random.RandomState = np.random.RandomState(32561)
                   ):

    distribution = pd.read_csv(distribution)
    distribution = pd.concat([distribution,
                              pd.DataFrame.from_dict({'workplace':[pd.NA],
                               'proportion': [max(
                                   1-distribution['proportion'].sum(), 0)]})],
                                   ignore_index=True)

    if 'workplace' not in population.columns:
        population['workplace'] = pd.NA
    
    workers = population[
        population['age'].between(*working_age) &
        population['workplace'].isna()].index.values
    
    population.loc[workers, 'workplace'] = distribution.sample(n=len(workers),
                                                weights='proportion',
                                                random_state=random_state,
                                                replace=True)['workplace'].values
    return population

# Ultimately, the idea is to have one function that receives
# a column to groupby, and an algorithm to generate connections.

def create_households_graph(population):
    assert 'household' in population.columns
    edges = pd.DataFrame(
        [(i,j) for _,df in population.groupby('household') for i,j in combinations(df['idx'].values, 2)], columns=['source', 'target'])
    G = ig.Graph.DataFrame(edges=edges, vertices=pd.DataFrame(population['idx']),
                           directed=False)
    return G

def create_schools_graph(population,
                         random_state,
                         contact_matrix=None,
                         avg_contacts_students=4,
                         avg_contacts_teachers_with_students=10,
                         age_groups=[(5,8), (9,12), (13,18)]):
    # TO DO: classes logic implementation
    assert 'school' in population.columns
    edges = []

    for _,dfs in population.groupby('school'):
        students = dfs[(dfs['age'] < 19) & (~dfs['school'].isna())]['idx'].values
        teachers = dfs[(dfs['age'] >= 19) & (~dfs['school'].isna())]['idx'].values
        edges.append(random_combinations(students, r=2, random_state=random_state,
                            n=int(np.ceil(len(students/avg_contacts_students)))))
        for t in teachers:
            edges.append(
                [sorted((t, s)) for s in random_state.choice(
                    students, size=min(len(students), avg_contacts_teachers_with_students),
                                       replace=False)]
                    )

    edges = pd.DataFrame(
        [(i, j) for l in edges for i,j in l], columns=['source', 'target'])
    G = ig.Graph.DataFrame(edges=edges, vertices=pd.DataFrame(population['idx']),
                           directed=False)
    return G

def create_workplaces_graph(population,
                         random_state,
                         contact_matrix=None,
                         avg_contacts=6):
    # TO DO: classes logic implementation
    assert 'workplace' in population.columns
    edges = []

    for _,df in population.groupby('workplace'):
        if _ != 'schools':
            workers = df['idx'].values
            edges.append(random_combinations(workers, r=2,
                                             random_state=random_state,
                                             n=int(np.ceil(len(workers/avg_contacts)))))
    edges = pd.DataFrame(
        [(i, j) for l in edges for i,j in l], columns=['source', 'target'])
    G = ig.Graph.DataFrame(edges=edges, vertices=pd.DataFrame(population['idx']),
                           directed=False)
    return G
    # U.S. Bureau of Labor Statistics in
    # their Quarterly Census of Employment and Wages for the fourth quarter of 2019

def create_community_graph(population, p,
                           random_seed=2334):
    import random
    random.seed(random_seed)
    return ig.Graph.Erdos_Renyi(n=len(population), p=p)


# %%
if __name__ == '__main__':
    pop = create_population('./data/pop.csv', 500)
    pop = add_households(pop, './data/household_size.csv', './data/household.csv')
    pop = add_schools(pop, size_distribution='./data/schools_size.csv',
                    students_per_teacher=20,
                    teaching_age=(19, 45),
                    random_state=np.random.RandomState(2514))
    pop = add_workplaces(pop, distribution='./data/workplaces.csv',
                        working_age=(19, 65),
                        random_state=np.random.RandomState(24314))

    g = create_households_graph(pop)
    ig.plot(g, vertex_size=5, edge_width=1)

    g = create_schools_graph(pop, random_state=np.random.RandomState(2374))
    colors = ['green' if (row['age']<19) & (~pd.isna(row['school']))
            else 'purple' if not pd.isna(row['school']) else 'white' for i,row in pop.iterrows()]
    ig.plot(g, vertex_size=5, edge_width=1, vertex_color=colors)

    g = create_community_graph(pop, p=0.002)
    ig.plot(g, vertex_size=10, edge_width=0.5, vertex_color='white')

    g = create_workplaces_graph(pop, random_state=np.random.RandomState(2374))
    colors_dict = {w: c for c, w in zip(['white', 'blue', 'orange', 'black', 'purple'], pop.workplace.unique())}
    colors = [colors_dict[row['workplace']] for i,row in pop.iterrows()]
    ig.plot(g, vertex_size=10, edge_width=0.5, vertex_color=colors)