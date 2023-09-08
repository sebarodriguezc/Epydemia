import sys
sys.path.append('./')
import epydemia as epy
from typing import List

def population_from_census():
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

def create_schools_graph(students: List[int],
                         n_schools: int,
                         n_classes_per_school: List[int],
                         subgroups: List[List[int]] = None
                         ):
    pass

def create_workplaces_graph(workers: List[int],
                            n_workplaces: int,
                            subgroups: List[List[int]] = None
                            ):
    # U.S. Bureau of Labor Statistics in
    # their Quarterly Census of Employment and Wages for the fourth quarter of 2019
    pass

def create_community_graph(community_members: List[int],
                           n_communities: int,
                           subgroups: List[List[int]] = None
                           ):
    pass

def create_households_graph(household_members: List[int],
                            n_households: int,
                            subgroups: List[List[int]] = None
                            )
    pass
