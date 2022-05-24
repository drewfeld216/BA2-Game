'''
This module deals with random number generation. It supports multiple
randomization path existing concurrently without interfering with each
other. It also allows a randomization path to persist even if the kernel
is interrupted and later re-loaded.

Note that there are two randomization engines - one used by numpy and
scipy, and one used by faker. This module deals with both at once and
abstracts this complexity.

The "workhorse function" of this module is generate_rv - it accepts
an object, and details of what kind of random number should be generated.
It then does the following
  - Sets the state of the random number generates to obj.random_state. This
    allows us to "pick up" from the last time a random number was generated
  - Generates whatever RV we need
  - Saves the state of the generators to obj.random_state, so we can pick up
    in the future

If the object has no random_state attribute, or if it is none, or if it is
an empty string, generate_rv will look for a seed attribute, initialize 
the numpy/faker engines using that seed, and save the state of the engine
to random_state before starting.

In practice, obj can inherit from Rand_utils_mixin to be endowed with a
generate_rv function which seamlessly handles the update of random_state.

Multiple objects can each have a random_state, and each can operate in
parallel without upsetting each other 
'''

import numpy as np
from faker import Faker
import json

fake = Faker()

def init_random_state(obj):
    '''
    This function takes an object with a seed property, sets the random seed
    of numpy and faker using this seed, and then changes the objects
    random_state property to reflect the serialized random_state that results
    '''
    
    np.random.seed(obj.seed)
    fake.random.seed(obj.seed)
    
    obj.random_state = get_random_state()

def get_random_state():
    '''
    This function retrieves the numpy random state and the current
    faker random state, and serializes them into a string, which it
    returns
    '''
    
    # numpy random state
    # ------------------
    np_state = np.random.get_state()
    
    # Tuples and ndarrays can't be serialized using json;
    # convert to lists
    np_state    = list(np_state)
    np_state[1] = np_state[1].tolist()
    
    # random random state
    # -------------------
    random_state = fake.random.getstate()
    
    # Concatenate, serialize, and return
    # ----------------------------------
    return json.dumps({'np_state':np_state, 'random_state':random_state})
    
def set_random_state(state):
    '''
    This function takes a serialized random state returned by get_random_state, and sets the random states to those numbers
    '''
    
    state        = json.loads(state)
    np_state     = state['np_state']
    random_state = state['random_state']
    
    # numpy random state
    # ------------------
    np.random.set_state(np_state)
    
    # random random state
    # -------------------
    # First, convert element 1 to a tuple to avoid an error
    random_state[1] = tuple(random_state[1])
    fake.random.setstate(random_state)

def generate_rv(obj, kind, n=1, **kwargs):
    '''
    This function generates random variables of all kinds based on the
    serialized random state in an object. It then updates the random state
    in that object. It accepts the following arguments
      - obj: an object that has a random_state attribute
      - The kind of the variable to generate
      - The number of RVs to generate
      - **kwargs arguments to pass to the RV generating functions (eg:
        the mean of a normal RV)
    See the first line of the function for distributions available and
    associated kwargs.
    
    The function then
      - Alters the random_state of obj to reflect the new random state
      - Returns the random variable requested; if n=1, this will be a scalar,
        and if n>1, this will be a list/array
    '''
    
    # Check whether the random_state has been saved
    if ( (not hasattr(obj, 'random_state'))
                or (obj.random_state is None)
                    or (obj.random_state == '')
                        or (not (type(obj.random_state) is str)) ):
        init_random_state(obj)
    
    def stand(x):
        sum_x = sum(x)
        
        if sum_x == 1:
            return x
        else:
            return [i/sum_x for i in x]
    
    # Dictionary mapping each variable type to a function
    # which generates that RV
    rv_kinds = {'uniform'     : lambda low=0, high=1  : np.random.uniform(size=n, low=low, high=high),
                'exponential' : lambda loc=0, scale=1 : np.random.exponential(size=n)*scale + loc,
                'normal'      : lambda loc=0, scale=1 : np.random.normal(loc=loc, scale=scale, size=n),
                'poisson'     : lambda lam            : np.random.poisson(lam=lam, size=n),
                'dirichlet'   : lambda alpha          : np.random.dirichlet(alpha=alpha, size=n),
                'choice'      : lambda l, p=None      : np.random.choice(l, size=n, p=stand(p)),
                'name'        : lambda                : [fake.name() for i in range(n)],
                'ipv4'        : lambda                : [fake.ipv4() for i in range(n)],
                'user_agent'  : lambda                : [fake.user_agent() for i in range(n)]}
    
    # Ensure the kind requested exists
    assert kind in rv_kinds
    
    # Set the random state
    set_random_state(obj.random_state)

    # Generate the RV
    out = rv_kinds[kind](**kwargs)
    
    # If the size is 1, extract the first element in the
    # list/array to return a scalar
    if n == 1:
        out = out[0]
    
    # Update the random state
    obj.random_state = get_random_state()
    
    # Return
    return out

class Rand_utils_mixin():
    '''
    This class can be inherited to endow any other class with a generate_rv
    function that automatically uses and updatesthe parent class' random_state
    to generate random variables
    '''
    
    def generate_rv(self, kind, n=1, **kwargs):
        return generate_rv(self, kind, n, **kwargs)