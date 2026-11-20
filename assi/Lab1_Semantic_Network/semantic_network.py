"""
AI401 - Expert Systems Lab
Experiment: Knowledge Representation — Semantic Network with Inheritance
"""

class SemanticNetwork:
    """
    Represents knowledge as a list of (subject, relation, object) triples.
    Supports property inheritance along 'is-a' links with local exception handling.
    """
    def __init__(self):
        self.triples = []

    def add_triple(self, subject: str, relation: str, obj: str):
        self.triples.append((subject, relation, obj))

    def get_parent(self, node: str) -> str:
        """Finds the parent of a node via the 'is-a' relation."""
        for s, r, o in self.triples:
            if s == node and r == "is-a":
                return o
        return None

    def get_inheritance_chain(self, node: str) -> list:
        """Algorithm Step 2: Follows 'is-a' links repeatedly until no parent exists."""
        chain = []
        current = node
        while current:
            chain.append(current)
            current = self.get_parent(current)
        return chain

    def query(self, node: str, relation: str, obj_target: str = None):
        """
        Algorithm Step 3: Walk up the chain; at each level check for an exception 
        ('cannot') matching the relation/target, and then for a local value; return first match.
        Algorithm Step 4: Report 'unknown' if the chain is exhausted.
        """
        chain = self.get_inheritance_chain(node)
        for current_node in chain:
            # 1. Check for negative exception ('cannot')
            for s, r, o in self.triples:
                if s == current_node and r == "cannot":
                    if obj_target is not None and o == obj_target:
                        return f"cannot {o}"
                    elif obj_target is None and relation in ("can", "cannot"):
                        return f"cannot {o}"
            
            # 2. Check for matching local relation
            for s, r, o in self.triples:
                if s == current_node:
                    if obj_target is not None:
                        if r == relation and o == obj_target:
                            return o
                    else:
                        if r == relation:
                            return o

        return "unknown"


def main_part1():
    print("=" * 60)
    print("PART 1: SEMANTIC NETWORK WITH INHERITANCE & EXCEPTIONS")
    print("=" * 60)
    
    net = SemanticNetwork()
    
    # Knowledge Base Triples
    facts = [
        ("animal", "has", "skin"),
        ("animal", "can", "breathe"),
        ("fish", "is-a", "animal"),
        ("fish", "can", "swim"),
        ("fish", "has", "gills"),
        ("bird", "is-a", "animal"),
        ("bird", "has", "feathers"),
        ("bird", "can", "fly"),
        ("bird", "has", "wings"),
        ("penguin", "is-a", "bird"),
        ("penguin", "cannot", "fly"),
        ("penguin", "can", "swim"),
        ("shark", "is-a", "fish"),
        ("shark", "can", "bite"),
    ]
    
    for s, r, o in facts:
        net.add_triple(s, r, o)

    print("\n1. Knowledge Base Triples:")
    for triple in net.triples:
        print(f"   {triple}")

    print("\n2. Inheritance Chains:")
    for concept in ["shark", "penguin", "bird", "animal"]:
        chain = net.get_inheritance_chain(concept)
        print(f"   Chain for '{concept}': {' -> '.join(chain)}")

    print("\n3. Queries Execution:")
    test_queries = [
        ("shark", "has", None),
        ("shark", "can", None),
        ("bird", "can", None),
        ("penguin", "can", "fly"),
        ("penguin", "can", "swim"),
        ("penguin", "has", None),
        ("animal", "can", None),
        ("penguin", "lives_in", None),
    ]

    for node, rel, tgt in test_queries:
        if tgt:
            result = net.query(node, rel, tgt)
            print(f"   query('{node}', '{rel} {tgt}') => {result}")
        else:
            result = net.query(node, rel)
            print(f"   query('{node}', '{rel}') => {result}")


def exercise_1():
    print("\n" + "=" * 60)
    print("EXERCISE 1: EXTEND NETWORK WITH OSTRICH")
    print("=" * 60)

    net = SemanticNetwork()
    
    facts = [
        ("animal", "has", "skin"),
        ("animal", "can", "breathe"),
        ("bird", "is-a", "animal"),
        ("bird", "has", "feathers"),
        ("bird", "can", "fly"),
        ("bird", "has", "wings"),
        ("penguin", "is-a", "bird"),
        ("penguin", "cannot", "fly"),
        ("penguin", "can", "swim"),
        # Extension: Ostrich
        ("ostrich", "is-a", "bird"),
        ("ostrich", "cannot", "fly"),
        ("ostrich", "can", "run_fast"),
    ]

    for s, r, o in facts:
        net.add_triple(s, r, o)

    print("\nExtended Triples for 'ostrich':")
    for s, r, o in net.triples:
        if s == "ostrich":
            print(f"   ({s}, {r}, {o})")

    chain = net.get_inheritance_chain("ostrich")
    print(f"\nInheritance Chain for 'ostrich': {' -> '.join(chain)}")

    print("\nQueries for 'ostrich':")
    print(f"   query('ostrich', 'can fly')      => {net.query('ostrich', 'can', 'fly')}")
    print(f"   query('ostrich', 'can run_fast') => {net.query('ostrich', 'can', 'run_fast')}")
    print(f"   query('ostrich', 'has')          => {net.query('ostrich', 'has')}")


def exercise_2():
    print("\n" + "=" * 60)
    print("EXERCISE 2: FRAME-BASED KNOWLEDGE REPRESENTATION")
    print("=" * 60)

    frames = {
        "animal": {
            "ako": None,
            "has": "skin",
            "can": "breathe"
        },
        "bird": {
            "ako": "animal",
            "has": "feathers",
            "can": "fly",
            "wings": "2"
        },
        "penguin": {
            "ako": "bird",
            "cannot": "fly",
            "can": "swim"
        },
        "ostrich": {
            "ako": "bird",
            "cannot": "fly",
            "can": "run_fast"
        },
        "fish": {
            "ako": "animal",
            "has": "gills",
            "can": "swim"
        },
        "shark": {
            "ako": "fish",
            "can": "bite"
        }
    }

    def frame_get_inheritance_chain(concept):
        chain = []
        curr = concept
        while curr:
            chain.append(curr)
            curr = frames.get(curr, {}).get("ako")
        return chain

    def frame_query(concept, slot, value=None):
        chain = frame_get_inheritance_chain(concept)
        for node in chain:
            frame = frames.get(node, {})
            # Exception check
            if "cannot" in frame:
                cannot_val = frame["cannot"]
                if value is None and slot in ("can", "cannot"):
                    return f"cannot {cannot_val}"
                elif value is not None and value == cannot_val:
                    return f"cannot {cannot_val}"
            # Slot check
            if slot in frame:
                return frame[slot]
        return "unknown"

    print("\nFrames Data Structure (Python Dicts):")
    for concept, slots in frames.items():
        print(f"   '{concept}': {slots}")

    print("\nFrame Queries Results:")
    test_cases = [
        ("penguin", "can", "fly"),
        ("penguin", "can", "swim"),
        ("penguin", "has", None),
        ("ostrich", "can", "fly"),
        ("ostrich", "can", "run_fast"),
        ("ostrich", "has", None),
        ("shark", "has", None),
        ("shark", "can", None)
    ]
    for concept, slot, val in test_cases:
        ans = frame_query(concept, slot, val)
        print(f"   frame_query('{concept}', '{slot}'{f', {val}' if val else ''}) => {ans}")


def exercise_3():
    print("\n" + "=" * 60)
    print("EXERCISE 3: MULTIPLE INHERITANCE (MULTIPLE IS-A LINKS)")
    print("=" * 60)

    class MultiParentSemanticNetwork:
        def __init__(self):
            self.triples = []

        def add_triple(self, subject: str, relation: str, obj: str):
            self.triples.append((subject, relation, obj))

        def get_parents(self, node: str) -> list:
            parents = []
            for s, r, o in self.triples:
                if s == node and r == "is-a":
                    parents.append(o)
            return parents

        def get_inheritance_order(self, node: str) -> list:
            """
            Breadth-First Search (BFS) / C3-style Order:
            Ensures child nodes and immediate parents are evaluated before grand-parents,
            resolving conflicts by prioritizing specific local traits over distant general ones.
            """
            order = []
            queue = [node]
            visited = set()

            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    order.append(curr)
                    parents = self.get_parents(curr)
                    queue.extend(parents)
            return order

        def query(self, node: str, relation: str, obj_target: str = None):
            order = self.get_inheritance_order(node)
            for current_node in order:
                # 1. Exception check
                for s, r, o in self.triples:
                    if s == current_node and r == "cannot":
                        if obj_target is not None and o == obj_target:
                            return f"cannot {o}"
                        elif obj_target is None and relation in ("can", "cannot"):
                            return f"cannot {o}"
                # 2. Local value match
                for s, r, o in self.triples:
                    if s == current_node:
                        if obj_target:
                            if r == relation and o == obj_target:
                                return o
                        else:
                            if r == relation:
                                return o
            return "unknown"

    net_mp = MultiParentSemanticNetwork()

    # Bat inherits from both Mammal and FlyingCreature
    facts = [
        ("animal", "has", "skin"),
        ("mammal", "is-a", "animal"),
        ("mammal", "has", "fur"),
        ("mammal", "can", "give_birth"),
        ("flying_creature", "is-a", "animal"),
        ("flying_creature", "can", "fly"),
        ("bat", "is-a", "mammal"),
        ("bat", "is-a", "flying_creature"),
        ("bat", "cannot", "see_in_daylight"),
    ]

    for s, r, o in facts:
        net_mp.add_triple(s, r, o)

    print("\nMultiple Inheritance Triples for 'bat':")
    for s, r, o in net_mp.triples:
        if s == "bat":
            print(f"   ({s}, {r}, {o})")

    bat_order = net_mp.get_inheritance_order("bat")
    print(f"\nLinearized Inheritance Order for 'bat': {' -> '.join(bat_order)}")

    print("\nQueries for 'bat':")
    print(f"   query('bat', 'can fly')              => {net_mp.query('bat', 'can', 'fly')}")
    print(f"   query('bat', 'can give_birth')       => {net_mp.query('bat', 'can', 'give_birth')}")
    print(f"   query('bat', 'has')                    => {net_mp.query('bat', 'has')}")
    print(f"   query('bat', 'can see_in_daylight') => {net_mp.query('bat', 'can', 'see_in_daylight')}")


if __name__ == "__main__":
    main_part1()
    exercise_1()
    exercise_2()
    exercise_3()
